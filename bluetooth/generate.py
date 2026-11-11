#!/usr/bin/env python3
"""Generate the single RTL8852B ready patch from a local Tahoe 25G332 binary."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent
CDHASH = 'ac367bd0eb64f10ec8673143e52372cf21051491'
PATCH_OFFSET = 0x216694
PAGE = PATCH_OFFSET & ~4095
TEXT_SIZE = 0xAA3000
TEXT_SECTION_END = 0xAA2B98
CAVE = 0xAA2C00
ENTRY = 0x173218


def require(condition, message):
    if not condition:
        raise ValueError(message)


def x86_slice(binary):
    require(binary[:4] == bytes.fromhex('cafebabe'), 'Expected a universal Mach-O binary')
    count = struct.unpack_from('>I', binary, 4)[0]
    for index in range(count):
        cpu, _, offset, size, _ = struct.unpack_from('>IIIII', binary, 8 + 20 * index)
        if cpu == 0x1000007:
            require(offset + size <= len(binary), 'Truncated x86_64 slice')
            return offset, size
    raise ValueError('No x86_64 slice')


def code_directory(image, header_end):
    signature = None
    position = 32
    for _ in range(struct.unpack_from('<I', image, 16)[0]):
        command, length = struct.unpack_from('<II', image, position)
        require(length >= 8 and position + length <= header_end, 'Invalid load command')
        if command == 0x1D:
            offset, size = struct.unpack_from('<II', image, position + 8)
            signature = image[offset:offset + size]
        position += length
    require(signature is not None and len(signature) >= 12, 'No native code signature')
    magic, total, count = struct.unpack_from('>III', signature)
    require(magic == 0xFADE0CC0 and total <= len(signature), 'Invalid code signature')
    for index in range(count):
        _, location = struct.unpack_from('>II', signature, 12 + index * 8)
        magic, length = struct.unpack_from('>II', signature, location)
        if magic != 0xFADE0C02:
            continue
        candidate = signature[location:location + length]
        if hashlib.sha256(candidate).hexdigest()[:40] == CDHASH:
            return candidate
    raise ValueError('Unsupported native CodeDirectory hash; use Tahoe 25G332 bluetoothd')


def verify_pages(image, directory):
    hash_offset = struct.unpack_from('>I', directory, 16)[0]
    slots = struct.unpack_from('>I', directory, 28)[0]
    require(directory[36] == 32 and directory[37] == 2 and directory[39] == 12,
            'Unsupported CodeDirectory page hash format')
    # Preserve the verified generator's header-page and target-page guards.
    for page in sorted({0, 0x1000, 0x2000, PAGE}):
        slot = page // 4096
        require(slot < slots, 'Missing signed page')
        signed = directory[hash_offset + slot * 32:hash_offset + (slot + 1) * 32]
        require(len(signed) == 32 and hashlib.sha256(image[page:page + 4096]).digest() == signed,
                'Unexpected signed page 0x%x' % page)


def verify_text(image):
    position = 32
    found = False
    for _ in range(struct.unpack_from('<I', image, 16)[0]):
        command, length = struct.unpack_from('<II', image, position)
        if command == 0x19 and image[position + 8:position + 24].rstrip(b'\0') == b'__TEXT':
            vm, _, file_offset, file_size = struct.unpack_from('<QQQQ', image, position + 24)
            _, initial_protection, section_count = struct.unpack_from('<III', image, position + 56)
            require(vm == 0x100000000 and file_offset == 0 and file_size == TEXT_SIZE
                    and initial_protection == 5, 'Unsupported __TEXT mapping')
            ends = []
            for index in range(section_count):
                section = position + 72 + 80 * index
                address, size, offset = struct.unpack_from('<QQI', image, section + 32)
                require(address - vm == offset, 'Unsupported section mapping')
                ends.append(offset + size)
            require(max(ends) == TEXT_SECTION_END, 'Unsupported __TEXT sections')
            found = True
        position += length
    require(found and image[CAVE:CAVE + 246] == bytes(246), 'Unexpected __TEXT tail bytes')
    require(image[ENTRY:ENTRY + 18] == bytes.fromhex('554889e5415741564154534881ec20010000'),
            'Unexpected original dispatcher bytes')


def header(image, slice_offset):
    # Keep the generated header byte-identical to the tested Ready source.
    # The legacy layout constants are unused by its single PatchSpec.
    lines = ['// Generated only from the exact supported local binary. Do not edit.', '#pragma once',
             'static const int supportedKernel = 25;',
             'static const char supportedCDHashString[] = "%s";' % CDHASH,
             'static const size_t supportedTextSize = 0xaa3000;',
             'static const size_t supportedCave = 0xaa2c00;',
             'static const size_t supportedEntry = 0x173218;']

    def array(name, value, mutable=False):
        lines.append(('static unsigned char ' if mutable else 'static const unsigned char ')
                     + name + '[] = {')
        lines.extend('    ' + ','.join('0x%02x' % byte for byte in value[index:index + 24]) + ','
                     for index in range(0, len(value), 24))
        lines.append('};')

    array('supportedCDHash', bytes.fromhex(CDHASH))
    array('originalPage0', image[PAGE:PAGE + 4096])
    array('replacement0', b'\xeb', True)
    lines.extend(['static PatchSpec patchSpecs[] = {',
                  '    {0x%x, 0x694, 1, originalPage0, replacement0, "baseline-ready"},'
                  % (slice_offset + PAGE), '};'])
    return '\n'.join(lines) + '\n'


def generate(binary_path, output):
    binary = bytearray(binary_path.read_bytes())
    observed_hash = hashlib.sha256(binary).hexdigest()
    offset, size = x86_slice(binary)
    image = binary[offset:offset + size]
    header_end = 32 + struct.unpack_from('<I', image, 20)[0]
    require(header_end == 0x26C8, 'Unsupported bluetoothd layout; use Tahoe 25G332')
    directory = code_directory(image, header_end)
    current = image[PATCH_OFFSET]
    require(current in (0x74, 0xEB), 'Unexpected ready-branch byte')
    # A running plugin may leave this one known byte in the UBC cache. Restore
    # only this temporary copy, then check the original signed page. Never write
    # the supplied Apple executable or normalize any other patch location.
    image[PATCH_OFFSET] = 0x74
    verify_pages(image, directory)
    verify_text(image)
    generated = header(image, offset)
    manifest = {
        'profile': 'tahoe', 'build': '25G332', 'kernel': 25, 'text_size': TEXT_SIZE,
        'observed_file_sha256': observed_hash, 'cdhash': CDHASH, 'slice_offset': offset,
        'load_commands_end': header_end, 'text_start': 0x27F0,
        'normalized_ready_byte': current == 0xEB,
        'original_page_sha256': hashlib.sha256(image[PAGE:PAGE + 4096]).hexdigest(),
        'generated_header_sha256': hashlib.sha256(generated.encode()).hexdigest(),
        'patches': [{'name': 'baseline-ready', 'offset': PATCH_OFFSET,
                     'original': '74', 'replacement': 'eb'}],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'Patches.hpp').write_text(generated)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Generated one baseline-ready patch: 25G332 0x216694: 74 -> eb.')
    if current == 0xEB:
        print('Normalized the known cached byte in memory; signed original pages verified.')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path,
                        help='Your legally obtained local Tahoe 25G332 /usr/sbin/bluetoothd')
    parser.add_argument('--output', type=Path, default=ROOT / 'generated',
                        help='Local generated output directory (default: generated/)')
    args = parser.parse_args()
    try:
        generate(args.binary.resolve(), args.output.resolve())
    except (ValueError, OSError, struct.error, IndexError) as error:
        parser.exit(1, 'Generation failed: %s\n' % error)


if __name__ == '__main__':
    main()
