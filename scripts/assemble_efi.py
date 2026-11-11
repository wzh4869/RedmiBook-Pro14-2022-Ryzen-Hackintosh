#!/usr/bin/env python3
"""Assemble and validate a local Tahoe EFI without writing an ESP."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import uuid

from prepare_vbios import validate_rom

ROOT = Path(__file__).resolve().parents[1]
GPU_PATH = 'PciRoot(0x1)/Pci(0x8,0x1)/Pci(0x0,0x0)'


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def read_plist(path):
    return plistlib.loads(path.read_bytes())


def identity(path):
    data = read_plist(path)
    if data['SystemProductName'] != 'MacPro7,1':
        raise ValueError('This profile requires MacPro7,1')
    for key in ['MLB', 'SystemSerialNumber', 'SystemUUID']:
        if not data.get(key) or 'CHANGE' in data[key]:
            raise ValueError('Missing identity field: ' + key)
    uuid.UUID(data['SystemUUID'])
    if not isinstance(data['ROM'], bytes) or len(data['ROM']) != 6 or data['ROM'] == bytes(6):
        raise ValueError('ROM must be six nonzero identity bytes')
    return {key: data[key] for key in ['SystemProductName', 'MLB', 'SystemSerialNumber', 'SystemUUID', 'ROM']}


def compile_acpi(tool, destination):
    for source in sorted((ROOT / 'acpi').glob('*.dsl')):
        prefix = destination / source.stem
        run([tool, '-p', prefix, source])
        data = prefix.with_suffix('.aml').read_bytes()
        if data[:4] != b'SSDT' or sum(data) % 256:
            raise ValueError('Invalid ACPI: ' + source.name)


def validate(efi, config, ocvalidate):
    loaded = set()
    for entry in config['Kernel']['Add']:
        if not entry['Enabled']:
            continue
        bundle = efi / 'OC/Kexts' / entry['BundlePath']
        info = read_plist(bundle / entry['PlistPath'])
        for dependency in info.get('OSBundleLibraries', {}):
            if not dependency.startswith('com.apple.') and dependency not in loaded:
                raise ValueError(f'{entry["BundlePath"]}: dependency must load first: {dependency}')
        loaded.add(info['CFBundleIdentifier'])
        if entry['ExecutablePath']:
            arches = run(['xcrun', 'lipo', '-archs', bundle / entry['ExecutablePath']]).split()
            if 'x86_64' not in arches:
                raise ValueError('Missing x86_64: ' + entry['BundlePath'])
    for section, folder in [('ACPI', 'ACPI'), ('UEFI', 'Drivers')]:
        for entry in config[section]['Add' if section == 'ACPI' else 'Drivers']:
            if entry['Enabled'] and not (efi / 'OC' / folder / entry['Path']).is_file():
                raise ValueError('Missing ' + entry['Path'])
    ocvalidate.chmod(ocvalidate.stat().st_mode | 0o100)
    return run([ocvalidate, efi / 'OC/config.plist'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=ROOT / 'build/inputs')
    parser.add_argument('--gpu-kext', type=Path, required=True)
    parser.add_argument('--bluetooth-kext', type=Path, required=True)
    parser.add_argument('--identity', type=Path, default=ROOT / 'private/smbios.plist')
    parser.add_argument('--vbios', type=Path, default=ROOT / 'private/680m.rom')
    parser.add_argument('--iasl', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/EFI')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f'Output already exists: {args.output}; choose a fresh --output directory')
    config = read_plist(ROOT / 'efi/config.template.plist')
    config['PlatformInfo']['Generic'].update(identity(args.identity))
    vbios = args.vbios.read_bytes()
    validate_rom(vbios)
    config['DeviceProperties']['Add'][GPU_PATH]['ATY,bin_image'] = vbios
    oc = args.inputs.resolve() / 'OpenCorePkg'
    extras = {'RembrandtGfx-Tahoe.kext': args.gpu_kext, 'RealtekBluetoothCompat.kext': args.bluetooth_kext}
    bundles = dict.fromkeys(entry['BundlePath'].split('/')[0] for entry in config['Kernel']['Add'])
    sources = {name: extras.get(name, args.inputs / name) for name in bundles}
    for name, source in sources.items():
        if not (source / 'Contents/Info.plist').is_file():
            raise ValueError(f'Missing input: {name} ({source})')
    for folder in ['BOOT', 'OC/ACPI', 'OC/Drivers', 'OC/Kexts']:
        (args.output / folder).mkdir(parents=True, exist_ok=True)
    for name in ['BOOT/BOOTx64.efi', 'OC/OpenCore.efi']:
        shutil.copy2(oc / 'X64/EFI' / name, args.output / name)
    for entry in config['UEFI']['Drivers']:
        name = entry['Path']
        shutil.copy2(oc / 'X64/EFI/OC/Drivers' / name, args.output / 'OC/Drivers' / name)
    compile_acpi(args.iasl.resolve(), args.output / 'OC/ACPI')
    for name, source in sources.items():
        shutil.copytree(source, args.output / 'OC/Kexts' / name)
    # This profile explicitly loads the PS/2 keyboard and the RTW89 front end only.
    for parent, keep in [('VoodooPS2Controller.kext', 'VoodooPS2Keyboard.kext'),
                         ('IO80211FamilyLegacy.kext', None)]:
        plugins = args.output / 'OC/Kexts' / parent / 'Contents/PlugIns'
        if not plugins.exists():
            continue
        for plugin in plugins.iterdir():
            if plugin.name != keep:
                shutil.rmtree(plugin)
            else:
                run(['codesign', '--force', '--sign', '-', plugin])
        run(['codesign', '--force', '--sign', '-', args.output / 'OC/Kexts' / parent])
        run(['codesign', '--verify', '--deep', '--strict', args.output / 'OC/Kexts' / parent])
    path = args.output / 'OC/config.plist'
    path.write_bytes(plistlib.dumps(config, sort_keys=False))
    validation = validate(args.output, config, oc / 'Utilities/ocvalidate/ocvalidate')
    files = {p.relative_to(args.output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(args.output.rglob('*')) if p.is_file()}
    manifest = dict(files=files,ocvalidate=validation.strip(),x86_64_and_dependency_order='passed',
                    runtime='not tested by this assembler',config_changes=json.loads((ROOT / 'sources.lock.json').read_text())['config_changes'])
    (args.output.parent / (args.output.name + '-manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    print('EFI built and validated:', args.output)
    print('Keep your working EFI before testing this folder on a separate USB device.')


if __name__ == '__main__':
    main()
