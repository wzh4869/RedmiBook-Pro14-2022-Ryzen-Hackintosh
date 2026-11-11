#!/usr/bin/env python3
"""Build and test the x86_64 RTL8852B Ready kext on Intel or Apple Silicon macOS."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / 'build'
EXECUTABLE = BUILD / 'RealtekBluetoothCompat.kext/Contents/MacOS/RealtekBluetoothCompat'


def run(arguments, log=None):
    result = subprocess.run([str(argument) for argument in arguments], cwd=ROOT,
                            text=True, capture_output=True)
    if log:
        (BUILD / log).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('%s\n%s' % (' '.join(map(str, arguments)), result.stdout + result.stderr))
    return result.stdout


def dependency(path, lock, expected_file):
    if run(['git', '-C', path, 'rev-parse', '--show-toplevel']).strip() != str(path):
        raise ValueError('Dependency root must be its own Git checkout: %s' % path)
    if run(['git', '-C', path, 'rev-parse', 'HEAD']).strip() != lock['commit']:
        raise ValueError('%s must use commit %s' % (path, lock['commit']))
    if run(['git', '-C', path, 'status', '--porcelain']).strip():
        raise ValueError('Dependency checkout contains local changes: %s' % path)
    if not (path / expected_file).is_file():
        raise ValueError('Missing dependency file: %s' % (path / expected_file))


def tests(binary):
    run([sys.executable, 'tests/generator.py', '--binary', binary], 'test-generator.log')
    for name, flags in [('native', []), ('ubsan', ['-fsanitize=undefined']),
                        ('asan', ['-fsanitize=address'])]:
        executable = BUILD / ('test-' + name)
        run(['xcrun', 'clang++', '-std=c++14', '-Wall', '-Wextra', '-Werror',
             *flags, 'tests/phy.cpp', '-o', executable], 'test-' + name + '-build.log')
        print(run([executable], 'test-' + name + '.log').strip())


def compile_kext(sdk, lilu):
    # These are the flags used by the tested Ready profile, including its Intel
    # kernel target when the build host itself is Apple Silicon.
    kernel = ['-target', 'x86_64-apple-macos10.15', '-mkernel', '-nostdinc', '-fno-builtin',
              '-fno-common', '-mno-red-zone', '-Os', '-DKERNEL', '-DKERNEL_PRIVATE',
              '-DDRIVER_PRIVATE', '-DAPPLE', '-DNeXT', '-I' + str(sdk / 'Headers'),
              '-I' + str(lilu / 'Lilu')]
    cpp = kernel + ['-std=gnu++14', '-fapple-kext', '-nostdlib', '-fno-rtti', '-fno-exceptions',
                    '-fno-use-cxa-atexit', '-mllvm', '-disable-atexit-based-global-dtor-lowering',
                    '-DPRODUCT_NAME=RealtekBluetoothCompat', '-DMODULE_VERSION=0.2.0',
                    '-DLILU_CUSTOM_IOKIT_INIT', '-Wno-deprecated-declarations',
                    '-Wno-inconsistent-missing-override']
    objects = []
    for source in [ROOT / 'RealtekBluetoothCompat.cpp', lilu / 'Lilu/Library/plugin_start.cpp']:
        obj = BUILD / (source.stem + '.o')
        run(['xcrun', 'clang++', *cpp, '-c', source, '-o', obj], source.stem + '-build.log')
        objects.append(obj)
    obj = BUILD / 'kmod_info.o'
    run(['xcrun', 'clang', *kernel, '-c', 'kmod_info.c', '-o', obj], 'kmod-info-build.log')
    objects.append(obj)
    EXECUTABLE.parent.mkdir(parents=True, exist_ok=True)
    run(['xcrun', 'ld', '-arch', 'x86_64', '-kext', '-platform_version', 'macos', '10.15', '10.15',
         '-no_data_const', '-o', EXECUTABLE, *objects, sdk / 'Library/x86_64/libkmod.a'], 'link.log')
    info = EXECUTABLE.parent.parent / 'Info.plist'
    shutil.copy2(ROOT / 'Info.plist', info)
    run(['plutil', '-lint', info], 'plist-validation.log')


def verify_kmod():
    image = EXECUTABLE.read_bytes()
    if struct.unpack_from('<II', image) != (0xFEEDFACF, 0x1000007):
        raise ValueError('Expected an x86_64 Mach-O kext')
    position = 32
    sections = []
    for _ in range(struct.unpack_from('<I', image, 16)[0]):
        command, size = struct.unpack_from('<II', image, position)
        if command == 0x19:
            sections.append(struct.unpack_from('<QQQQ', image, position + 24))
        position += size
    symbols = {}
    for line in run(['xcrun', 'nm', EXECUTABLE]).splitlines():
        words = line.split()
        if len(words) == 3:
            symbols[words[2]] = int(words[0], 16)

    def pointer(address):
        for vm, _, file_offset, file_size in sections:
            if vm <= address and address + 8 <= vm + file_size:
                return struct.unpack_from('<Q', image, file_offset + address - vm)[0]
        raise ValueError('Unmapped kmod pointer 0x%x' % address)

    checks = [(symbols['_kmod_info'] + 180, '__start'),
              (symbols['_kmod_info'] + 188, '__stop'),
              (symbols['__realmain'], '_RealtekBluetoothCompat_kern_start'),
              (symbols['__antimain'], '_RealtekBluetoothCompat_kern_stop')]
    if any(pointer(address) != symbols[symbol] for address, symbol in checks):
        raise ValueError('Invalid kmod start/stop pointer')
    print('PASS: x86_64 kext and kmod wrapper/real start-stop pointers.')
    imports = sorted(set(run(['xcrun', 'nm', '-u', EXECUTABLE], 'imports.txt').split()))
    return imports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path,
                        help='Your local Tahoe 25G332 /usr/sbin/bluetoothd')
    parser.add_argument('--sdk-root', required=True, type=Path, help='Pinned MacKernelSDK Git checkout')
    parser.add_argument('--lilu-root', required=True, type=Path, help='Pinned Lilu Git checkout (parent of Lilu/)')
    args = parser.parse_args()
    try:
        lock = json.loads((ROOT / 'sources.lock.json').read_text())
        sdk, lilu, binary = args.sdk_root.resolve(), args.lilu_root.resolve(), args.binary.resolve()
        dependency(sdk, lock['MacKernelSDK'], 'Library/x86_64/libkmod.a')
        dependency(lilu, lock['Lilu'], 'Lilu/Library/plugin_start.cpp')
        BUILD.mkdir(exist_ok=True)
        print(run([sys.executable, 'generate.py', '--binary', binary], 'generate.log').strip())
        tests(binary)
        compile_kext(sdk, lilu)
        imports = verify_kmod()
        manifest = json.loads((ROOT / 'generated/manifest.json').read_text())
        report = {'target': 'x86_64', 'version': '0.2.0', 'patches': manifest['patches'],
                  'cdhash': manifest['cdhash'], 'generated_header_sha256': manifest['generated_header_sha256'],
                  'dependencies': {name: lock[name]['commit'] for name in ['MacKernelSDK', 'Lilu']},
                  'tests': {'generator': 'passed', 'native': 'passed', 'ubsan': 'passed', 'asan': 'passed',
                            'plist': 'passed', 'kmod_start_stop': 'passed'},
                  'imports': imports, 'import_count': len(imports),
                  'executable_sha256': hashlib.sha256(EXECUTABLE.read_bytes()).hexdigest(),
                  'runtime': 'not tested by this build command'}
        (BUILD / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Built %s\nValidation: %s' % (EXECUTABLE.parent.parent.parent, BUILD / 'validation.json'))
    except (ValueError, OSError, RuntimeError, KeyError, struct.error) as error:
        parser.exit(1, 'Build failed: %s\n' % error)


if __name__ == '__main__':
    main()
