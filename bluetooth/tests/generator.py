#!/usr/bin/env python3
"""Exercise the actual generator using a user-provided local Apple binary."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    args = parser.parse_args()
    binary = bytearray(args.binary.read_bytes())
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        fixture = temporary / 'bluetoothd'
        output = temporary / 'generated'

        def run(data, success):
            fixture.write_bytes(data)
            result = subprocess.run([sys.executable, str(ROOT / 'generate.py'), '--binary',
                                     str(fixture), '--output', str(output)],
                                    capture_output=True, text=True)
            assert (result.returncode == 0) == success, result.stdout + result.stderr

        run(binary, True)
        expected = (output / 'Patches.hpp').read_bytes()
        baseline_hash = json.loads((ROOT / 'sources.lock.json').read_text())['validated_generated_header_sha256']
        assert hashlib.sha256(expected).hexdigest() == baseline_hash, 'Header differs from tested Ready baseline'
        manifest = json.loads((output / 'manifest.json').read_text())
        assert manifest['patches'] == [{'name': 'baseline-ready', 'offset': 0x216694,
                                      'original': '74', 'replacement': 'eb'}]
        offset = manifest['slice_offset']
        clean = bytearray(binary)
        clean[offset + 0x216694] = 0x74
        run(clean, True)
        assert (output / 'Patches.hpp').read_bytes() == expected
        cached = bytearray(clean)
        cached[offset + 0x216694] = 0xEB
        run(cached, True)
        assert (output / 'Patches.hpp').read_bytes() == expected
        assert json.loads((output / 'manifest.json').read_text())['normalized_ready_byte']
        changed = bytearray(clean)
        changed[offset + 0x216694] = 0x75
        run(changed, False)
        changed = bytearray(clean)
        changed[offset + 0x216551] ^= 1  # The removed PHY experiment must remain original.
        run(changed, False)
        changed = bytearray(clean)
        changed[offset + 0x216000] ^= 1
        run(changed, False)
        changed = bytearray(clean)
        changed[offset + 0x2000] ^= 1
        run(changed, False)
        position = offset + 32
        for _ in range(struct.unpack_from('<I', clean, offset + 16)[0]):
            command, length = struct.unpack_from('<II', clean, position)
            if command == 0x1D:
                signature_offset = struct.unpack_from('<I', clean, position + 8)[0]
                break
            position += length
        changed = bytearray(clean)
        primary_directory = struct.unpack_from('>I', clean, offset + signature_offset + 16)[0]
        changed[offset + signature_offset + primary_directory + 40] ^= 1
        run(changed, False)
        run(clean[:100], False)
        assert (output / 'Patches.hpp').read_bytes() == expected, 'Failure overwrote valid output'
    print('PASS: tested baseline header; clean/cached input equivalence; unknown byte, PHY, page, signature and truncated input rejection.')


if __name__ == '__main__':
    main()
