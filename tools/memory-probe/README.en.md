# Optional UMA logger

[中文](README.md)

This is the source of the UEFI tool used by the experimental EFI. It reads 680M reserved memory and the firmware memory map before macOS starts. Normal driver use does not need it, so the public assembler omits it by default.

From the repository root, build with your own [Zig 0.15.2](https://ziglang.org/download/):

```sh
python3 tools/memory-probe/build.py --zig /path/to/zig
```

The script runs the existing ASan / UBSan entry tests, then writes `build/memory-probe/RmbMemoryProbe.efi`. For diagnostics, manually copy it to the test EFI's `OC/Drivers/` and add an enabled entry with the same name under OpenCore `UEFI/Drivers`.

It writes `RmbMemoryProbe.txt` only to a volume whose root `RmbMemoryProbe.tag` starts with `RMB-U352-AUDIT`, the retained experiment marker. Unmarked volumes are not written. It makes no PCI, MMIO or NVRAM writes. Logs can contain the machine's memory layout; do not upload raw files. Remove the driver, entry and marker after testing.

Source retains the experimental implementation under [GPL-2.0](LICENSE). UEFI ABI declarations derive from HdaSnoop in the pinned RembrandtGfx source.
