#!/usr/bin/env python3
"""Download pinned public EFI dependencies to the local build directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def download(record, cache):
    path = cache / record['asset']
    if not path.exists():
        print('Downloading', record['name'], flush=True)
        request = urllib.request.Request(record['url'], headers={'User-Agent': 'RedmiBook-EFI-build'})
        with urllib.request.urlopen(request, timeout=120) as response, path.open('wb') as output:
            shutil.copyfileobj(response, output)
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError(f'Archive checksum differs: {path}; remove it and retry')
    return path


def extract(archive, destination):
    with zipfile.ZipFile(archive) as package:
        for member in package.infolist():
            path = Path(member.filename)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Invalid archive member: ' + member.filename)
        package.extractall(destination)


def unique_bundle(folder, name):
    matches = [p for p in folder.rglob(name) if p.is_dir() and '__MACOSX' not in p.parts]
    if len(matches) != 1:
        raise ValueError(f'Expected one {name} in {folder}, found {len(matches)}')
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/inputs')
    parser.add_argument('--cache', type=Path, default=ROOT / 'build/downloads')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    records = json.loads((ROOT / 'sources.lock.json').read_text())['artifacts']
    for record in records:
        archive = download(record, args.cache)
        if record['name'] == 'AppleMCEReporterDisabler':
            target = args.output / 'AppleMCEReporterDisabler.kext/Contents'
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archive, target / 'Info.plist')
            continue
        expanded = args.cache / (record['name'] + '-extracted')
        if expanded.exists():
            shutil.rmtree(expanded)
        extract(archive, expanded)
        if record['name'] == 'OpenCorePkg':
            target = args.output / 'OpenCorePkg'
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(expanded, target)
        for name in record['bundles']:
            target = args.output / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(unique_bundle(expanded, name), target)
    print('Inputs:', args.output)
    print('Still required: locally built GPU, Bluetooth and Wi-Fi; IOSkywalkFamily, IO80211FamilyLegacy, AMFIPass.')


if __name__ == '__main__':
    main()
