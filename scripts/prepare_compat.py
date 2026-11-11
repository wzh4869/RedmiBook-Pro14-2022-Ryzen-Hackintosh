#!/usr/bin/env python3
"""Verify and copy user-supplied compatibility archives into local EFI inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from fetch_inputs import extract, unique_bundle

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives-dir', type=Path, default=ROOT / 'build/downloads')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/inputs')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for record in json.loads((ROOT / 'sources.lock.json').read_text())['apple_compat_inputs']:
        archive = args.archives_dir / record['name']
        if hashlib.sha256(archive.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Compatibility archive checksum differs: ' + archive.name)
        work = ROOT / 'build/compat' / archive.stem
        if work.exists():
            shutil.rmtree(work)
        extract(archive, work)
        name = archive.name.split('-')[0] + '.kext'
        target = args.output / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(unique_bundle(work, name), target)
        print('Prepared', name)


if __name__ == '__main__':
    main()
