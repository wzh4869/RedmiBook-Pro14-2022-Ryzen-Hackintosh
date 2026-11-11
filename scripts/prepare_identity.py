#!/usr/bin/env python3
"""Generate a new local MacPro7,1 identity with OpenCore macserial."""
import argparse
from pathlib import Path
import plistlib
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--macserial', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'private/smbios.plist')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f'Identity already exists: {args.output}; reuse it for rebuilds')
    args.macserial.chmod(args.macserial.stat().st_mode | 0o100)
    result = subprocess.run([str(args.macserial.resolve()), '-m', 'MacPro7,1', '-n', '1'],
                            check=True, capture_output=True, text=True)
    pair = next(re.fullmatch(r'\s*([A-Z0-9]+)\s*\|\s*([A-Z0-9]+)\s*', line)
                for line in result.stdout.splitlines() if re.fullmatch(r'\s*[A-Z0-9]+\s*\|\s*[A-Z0-9]+\s*', line))
    rom = bytearray(uuid.uuid4().bytes[:6])
    rom[0] = (rom[0] | 2) & 0xFE
    identity = dict(SystemProductName='MacPro7,1', SystemSerialNumber=pair[1], MLB=pair[2],
                    SystemUUID=str(uuid.uuid4()).upper(), ROM=bytes(rom))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as output:
        args.output.chmod(0o600)
        output.write(plistlib.dumps(identity, sort_keys=False))
    print('Identity saved locally:', args.output)


if __name__ == '__main__':
    main()
