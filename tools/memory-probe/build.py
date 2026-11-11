#!/usr/bin/env python3
"""Build the optional USB-only UMA logger with Zig 0.15.2."""
import argparse
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zig', type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / 'build/memory-probe'
    output.mkdir(parents=True, exist_ok=True)
    test = output / 'test'
    subprocess.run(['xcrun', 'clang', '-fno-builtin', '-fshort-wchar', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-parameter', '-fsanitize=address,undefined', str(HERE / 'test.c'),
                    '-o', str(test)], check=True)
    subprocess.run([str(test)], check=True)
    if subprocess.check_output([str(args.zig.resolve()), 'version'], text=True).strip() != '0.15.2':
        raise ValueError('Use Zig 0.15.2 for the recorded build')
    target = output / 'RmbMemoryProbe.efi'
    subprocess.run([str(args.zig.resolve()), 'build-exe', '-target', 'x86_64-uefi', '-O', 'ReleaseSmall',
                    '--subsystem', 'efi_boot_service_driver', '-fno-stack-check', '-fno-stack-protector',
                    '-fno-compiler-rt', '-femit-bin=' + str(target), '-cflags', '-ffreestanding',
                    '-fshort-wchar', '-mno-red-zone', '-fno-builtin', '-Wall', '-Wextra', '-Werror',
                    '--', str(HERE / 'RmbMemoryProbe.c')], check=True)
    data = target.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    if data[:2] != b'MZ' or data[pe:pe + 4] != b'PE\0\0' or struct.unpack_from('<H', data, pe + 4)[0] != 0x8664:
        raise ValueError('Expected x86_64 PE image')
    optional = pe + 24
    if struct.unpack_from('<H', data, optional + 68)[0] != 11 or struct.unpack_from('<II', data, optional + 120)[0]:
        raise ValueError('Expected UEFI boot-service driver without imports')
    print('Optional logger:', target)


if __name__ == '__main__':
    main()
