#!/usr/bin/env python3
"""Prepare an injected VBIOS from this machine's VFCT copy. Never flash firmware."""
import argparse
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate_rom(data):
    if data[:2] != b'\x55\xaa' or len(data) != data[2] * 512 or sum(data) % 256:
        raise ValueError('Invalid option ROM length or checksum')
    pcir = struct.unpack_from('<H', data, 0x18)[0]
    atom = struct.unpack_from('<H', data, 0x48)[0]
    if data[pcir:pcir + 4] != b'PCIR' or struct.unpack_from('<HH', data, pcir + 4) != (0x1002, 0x73FF):
        raise ValueError('Expected injected 1002:73ff PCIR')
    if data[atom + 4:atom + 8] != b'ATOM':
        raise ValueError('Missing ATOM header')
    table = struct.unpack_from('<H', data, atom + 0x20)[0]
    vram = struct.unpack_from('<H', data, table + 0x3C)[0]
    if not vram or struct.unpack_from('<I', data, vram + 24)[0] != 512:
        raise ValueError('Expected 512 MiB VRAM table')
    if data[vram + 24 + 24] != 8 or data[vram + 24 + 25] != 4:
        raise ValueError('Expected 128-bit VRAM bus')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vfct', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'private/680m.rom')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f'VBIOS already exists: {args.output}; reuse it for rebuilds')
    vfct = args.vfct.resolve()
    data = vfct.read_bytes()
    if data[:4] != b'VFCT' or len(data) != struct.unpack_from('<I', data, 4)[0] or sum(data) % 256:
        raise ValueError('Invalid VFCT length or checksum')
    work = ROOT / 'build/vbios'
    if work.exists():
        shutil.rmtree(work)
    (work / 'roms').mkdir(parents=True)
    subprocess.run([sys.executable, str(ROOT / 'vbios/vfct-rom.py'), str(vfct)], cwd=work, check=True)
    generated = work / 'roms/680m-512MiB.rom'
    subprocess.run([sys.executable, str(ROOT / 'vbios/augment-rom.py'),
                    str(work / 'roms/680m-73ff.rom'), str(generated),
                    '--vram-mb', '512', '--bus-width', '128'], check=True)
    validate_rom(generated.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(generated, args.output)
    args.output.chmod(0o600)
    print('Injected VBIOS saved locally:', args.output)


if __name__ == '__main__':
    main()
