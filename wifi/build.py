#!/usr/bin/env python3
"""Rebuild the pinned AirPort_RTW89 native Core/Front bundle on macOS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / 'build'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def run(arguments, cwd=ROOT, env=None, log=None):
    if log is None:
        subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=env, check=True)
        return
    with log.open('w') as stream:
        result = subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=env,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        tail = '\n'.join(log.read_text(errors='replace').splitlines()[-35:])
        raise RuntimeError(f'Build failed; see {log}\n{tail}')


def source(lock):
    archive = BUILD / 'downloads/AirPort_RTW89.tar.gz'
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.is_file():
        temporary = archive.with_suffix('.download')
        run(['curl', '-fL', '--retry', '2', '--connect-timeout', '30', '--max-time',
             '300', '-o', temporary, lock['archive_url']])
        if sha256(temporary) != lock['archive_sha256']:
            raise ValueError('Downloaded source archive SHA-256 does not match source-lock.json')
        temporary.replace(archive)
    if sha256(archive) != lock['archive_sha256']:
        raise ValueError(f'Source archive SHA-256 does not match: {archive}')
    patch = ROOT / lock['patch']
    if sha256(patch) != lock['patch_sha256']:
        raise ValueError('Local patch SHA-256 does not match source-lock.json')
    destination = BUILD / 'source'
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir()
    run(['tar', '-xzf', archive, '-C', destination, '--strip-components=1'])
    run(['patch', '-p1', '-i', patch], cwd=destination)
    return destination


def compatibility_inputs(kdk, compatibility):
    paths = {
        'kernel': kdk / 'Kernels/kernel',
        'IOPCIFamily.kext': kdk / 'Extensions/IOPCIFamily.kext',
        'IONetworkingFamily.kext': kdk / 'Extensions/IONetworkingFamily.kext',
        'IO80211FamilyLegacy.kext': compatibility / 'IO80211FamilyLegacy.kext',
        'IOSkywalkFamily.kext': compatibility / 'IOSkywalkFamily.kext',
    }
    for name, path in paths.items():
        if not path.exists():
            raise ValueError(f'Missing local input: {path}')
        if name.endswith('.kext'):
            info = plistlib.loads((path / 'Contents/Info.plist').read_bytes())
            expected = 'com.apple.iokit.' + name.removesuffix('.kext')
            if info['CFBundleIdentifier'] != expected:
                raise ValueError(f'Unexpected bundle identifier in {path}')
    library = BUILD / 'kpi/System/Library'
    if library.parent.parent.exists():
        shutil.rmtree(library.parent.parent)
    (library / 'Kernels').mkdir(parents=True)
    (library / 'Extensions').mkdir()
    for name, path in paths.items():
        target = library / ('Kernels/kernel' if name == 'kernel' else 'Extensions/' + name)
        target.symlink_to(path, target_is_directory=path.is_dir())
    return library, paths


def input_manifest(paths):
    result = {}
    for name, path in paths.items():
        if name == 'kernel':
            result[name] = {'sha256': sha256(path)}
        else:
            info = plistlib.loads((path / 'Contents/Info.plist').read_bytes())
            result[name] = {
                'identifier': info['CFBundleIdentifier'],
                'version': info['CFBundleVersion'],
                'executable_sha256': sha256(path / 'Contents/MacOS' / info['CFBundleExecutable']),
            }
    return result


def package(source_root, lock, paths):
    bundle = BUILD / 'AirPort_RTW89.kext'
    if bundle.exists():
        shutil.rmtree(bundle)
    shutil.copytree(source_root / 'build/out/bundle/AirPort_RTW89.kext', bundle)
    front = bundle / 'Contents/PlugIns/AirPortRTW89Front.kext'
    if not front.is_dir():
        raise ValueError('Built bundle is missing the nested AirPortRTW89Front.kext')
    run(['codesign', '--verify', '--deep', '--strict', bundle])
    tool = BUILD / 'rtw89ctl'
    shutil.copy2(source_root / 'build/out/rtw89ctl', tool)
    run(['codesign', '--force', '--sign', '-', tool])
    run(['codesign', '--verify', '--strict', tool])
    files = {path.relative_to(bundle).as_posix(): sha256(path)
             for path in sorted(bundle.rglob('*')) if path.is_file()}
    manifest = {
        'source_commit': lock['commit'], 'source_archive_sha256': lock['archive_sha256'],
        'patch_sha256': lock['patch_sha256'], 'local_inputs': input_manifest(paths),
        'make_target': 'bundle', 'hosttests_passed': True,
        'kdk_direct_import_checks_passed': True, 'signature_check': 'deep strict',
        'hardware_validation': 'Not performed by this build script',
        'bundle_files': files, 'rtw89ctl_sha256': sha256(tool),
    }
    (BUILD / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kdk', type=Path, required=True,
                        help='Target KDK System/Library directory containing Kernels and Extensions')
    parser.add_argument('--compat-kexts', type=Path, required=True,
                        help='Local directory containing IO80211FamilyLegacy.kext and IOSkywalkFamily.kext')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('This build requires macOS and Xcode command line tools')
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    BUILD.mkdir(exist_ok=True)
    lock = json.loads((ROOT / 'source-lock.json').read_text())
    library, paths = compatibility_inputs(args.kdk.resolve(), args.compat_kexts.resolve())
    source_root = source(lock)
    environment = dict(os.environ, RTW89_KDK=str(library))
    print('Fetching pinned firmware; downloaded files stay in wifi/build/.', flush=True)
    run(['make', 'fetch-firmware'], cwd=source_root, log=BUILD / 'firmware.log')
    print('Building Core/Front and running the upstream host tests; see wifi/build/build.log.', flush=True)
    run(['make', f'HOST_CPUS={args.jobs}', f'SOURCE_COMMIT={lock["commit"]}', 'bundle'],
        cwd=source_root, env=environment, log=BUILD / 'build.log')
    run([sys.executable, 'tools/check_kpi.py',
         'build/out/bundle/AirPort_RTW89.kext/Contents/PlugIns/AirPortRTW89Front.kext'],
        cwd=source_root, env=environment, log=BUILD / 'front-imports.log')
    bundle = package(source_root, lock, paths)
    print(f'Built {bundle}\nManifest: {BUILD / "build-manifest.json"}')


if __name__ == '__main__':
    main()
