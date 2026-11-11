# RedmiBook Pro 14 2022 Ryzen Hackintosh

[中文](README.md) | English

macOS configuration, machine patches and build tools for the Ryzen RedmiBook Pro 14 2022. This machine runs **Tahoe 26.7.2 / 25G332**. Basic 680M acceleration, the 120 Hz internal display, Wi-Fi, speakers, trackpad and an S1 Bluetooth mouse have hardware test records. Safari window switching still stutters.

The repository contains a sanitized configuration and actual source build steps. Generate your own SMBIOS, extract a VBIOS from this machine's VFCT, and build the graphics, Wi-Fi and Bluetooth plugins. There is no prebuilt EFI ready to copy. Start with the [build and trial guide](docs/build.en.md).

## Tested hardware

| Component | Configuration |
|---|---|
| CPU / memory | Ryzen 7 6800H, 8 cores and 16 threads; 16 GB LPDDR5 |
| GPU | Radeon 680M, `1002:1681` revision `02`; fixed 512 MiB VRAM |
| Internal display | BOE NE140QDM-NX2, 2560 × 1600, 120 Hz |
| Wi-Fi / Bluetooth | RTL8852BE `10ec:b852` / USB `0cb8:c559` |
| Audio | Conexant CX11880 `14f1:1f86`, layout 15 |
| Trackpad | ELAN2310 I2C HID `04f3:3238` |
| SSD / BIOS | KIOXIA BG5 512 GB / RMARB4B0P1010 |

The same model name may ship with a different wireless card, codec or panel. Check your hardware first; other combinations have not been tested.

## Current status

As of 2026-11-11, the current system uses `MacPro7,1` and GPU candidate 23. macOS 15 results are historical; that system volume has been deleted.

| Feature | Hardware checks completed |
|---|---|
| Boot / storage | Tahoe desktop; APFS write and readback passed. This machine still boots from a USB EFI |
| GPU / display | 1,024 Metal compute values, 1,024 rendered pixels and 480 texture samples passed; 2560 × 1600, 1280 × 800 HiDPI, 120 Hz |
| Wi-Fi / battery | Connection through the system UI and HTTPS access; battery level and AC state |
| Audio / input | November 9: speakers, at least 30 seconds of Safari Bilibili playback, trackpad movement, clicks and two-/three-finger gestures; keyboard works |
| Bluetooth | November 9: S1 mouse pairing, encryption, movement, buttons, wheel and short-term reconnection after turning the mouse off and on |

**Hardware video encoding and decoding are disabled.** Video playback does not establish hardware decoding. Safari stutter remains; sleep, external displays, microphone recording, camera, fingerprint and long-term stability have not been accepted. Dates and test limits are in the [validation record](docs/validation.en.md).

## Where to start

- [Build and trial guide](docs/build.en.md): dependencies, personal inputs, EFI assembly, trial from a spare USB and rollback.
- [efi/config.template.plist](efi/config.template.plist) and [acpi](acpi): machine configuration and four SSDT sources.
- [Bluetooth patch](bluetooth/README.en.md): RTL8852B ready-stage fix for 25G332.
- [Wi-Fi build](wifi/README.en.md): pinned AirPort_RTW89 scan fix and local build patch.
- [Radeon 680M repository](https://github.com/wzh4869/Radeon-680M-Hackintosh): graphics source, experiments and Metal tools, maintained separately.
- [Component sources](docs/components.en.md): versions, attribution and configuration differences.

## License

Original code and documentation use [GPL-2.0](LICENSE). Derived source retains original attribution; third-party components retain their own licenses. Build output, Apple system files, firmware, personal identities and raw machine logs are not published with this repository.
