# RTL8852BE native Wi-Fi

[简体中文](README.md)

This directory provides the pinned AirPort_RTW89 source, a local patch, and a build entry point for this project's RTL8852BE card (PCI `10ec:b852`). Network connections use the macOS Wi-Fi menu and Settings. `rtw89ctl` is a diagnostic tool.

Connecting from the system menu and accessing HTTPS have been checked on the RedmiBook running macOS Tahoe, build `25G332`. Saved networks, automatic reconnection, and sleep/wake have not had dedicated checks. Other Realtek models have not been tested on hardware. The build checks here do not repeat those hardware tests.

## Source and patch

The source is commit `54ecd01ee1e3e5c0b378611a989b8d8c11e58579` from [FranciumOS-org/AirPort_RTW89 PR #11](https://github.com/FranciumOS-org/AirPort_RTW89/pull/11), downloaded from [hrx114514x/AirPort_RTW89](https://github.com/hrx114514x/AirPort_RTW89). The PR's scan-request changes are already part of that commit.

[`patches/0001-native-build.patch`](patches/0001-native-build.patch) preserves the two-file build patch used by this project:

- `Makefile`: build user-space tests and the diagnostic tool for x86_64; accept the source commit as an argument when an archive has no `.git`; sign and strictly verify the assembled Core bundle with its nested Front.
- `tools/check_kpi.py`: check direct x86_64 imports against a local KDK, allowing an Intel driver build on an Apple Silicon host.

The Linux hardware driver source and upstream bundle version are unchanged. The source archive includes fixed Linux, MacKernelSDK, hostap, and Mbed TLS snapshots. The build does not follow their latest branches. Sources, archive hashes, and the firmware commit are recorded in [`source-lock.json`](source-lock.json).

## Dependencies

Build on macOS with Xcode command line tools, a macOS SDK, and Python 3.9 or later. Apple Silicon hosts must also be able to run x86_64 user-space programs because the upstream `make bundle` target executes them.

Obtain Apple components yourself and keep them locally. This repository contains no Apple kexts, KDK, or firmware binaries.

1. Obtain a KDK from [Apple Developer Downloads](https://developer.apple.com/download/all/?q=Kernel%20Debug%20Kit). The existing build used KDK `15.8.1 / 24H32` for offline checks. Point `--kdk` at its `System/Library`, containing `Kernels/kernel`, `Extensions/IOPCIFamily.kext`, and `Extensions/IONetworkingFamily.kext`. Checks using a different target KDK apply to that supplied KDK; checks against the older KDK do not establish Tahoe ABI compatibility.
2. Download the compatibility archives from the fixed OCLP commit below. Put the extracted kexts in `build/inputs/` at the repository root. Compare the ZIP SHA-256 values with `source-lock.json`.

| Package | Pinned download | Use |
| --- | --- | --- |
| IOSkywalkFamily 1.2.0 | [IOSkywalkFamily-v1.2.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IOSkywalkFamily-v1.2.0.zip) | Native Wi-Fi runtime dependency |
| IO80211FamilyLegacy 1.0.0 | [IO80211FamilyLegacy-v1.0.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IO80211FamilyLegacy-v1.0.0.zip) | Front runtime and import-check dependency |
| AMFIPass 1.4.1 | [AMFIPass-v1.4.1-RELEASE.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-RELEASE.zip) | EFI runtime dependency; not used to compile this directory |

After saving the ZIP files in `build/downloads/`, run at the repository root:

```sh
shasum -a 256 build/downloads/IOSkywalkFamily-v1.2.0.zip build/downloads/IO80211FamilyLegacy-v1.0.0.zip build/downloads/AMFIPass-v1.4.1-RELEASE.zip
mkdir -p build/inputs
unzip -q build/downloads/IOSkywalkFamily-v1.2.0.zip -d build/inputs
unzip -q build/downloads/IO80211FamilyLegacy-v1.0.0.zip -d build/inputs
unzip -q build/downloads/AMFIPass-v1.4.1-RELEASE.zip -d build/inputs
```

## Build

Run at the repository root, replacing the example KDK path:

```sh
python3 wifi/build.py \
  --kdk "/path/to/KDK_15.8.1_24H32.kdk/System/Library" \
  --compat-kexts build/inputs \
  --jobs 4
```

The script downloads and verifies the pinned source archive, extracts a fresh source tree, applies the local patch, and runs upstream `make fetch-firmware` and `make bundle`. Firmware uses the source's pinned linux-firmware commit and `firmware/SHA256SUMS`. Downloads remain under the ignored `wifi/build/` directory.

A successful build produces:

- `wifi/build/AirPort_RTW89.kext`, including `Contents/PlugIns/AirPortRTW89Front.kext`.
- `wifi/build/rtw89ctl`, the x86_64 diagnostic tool.
- `wifi/build/build-manifest.json`, recording source, patch, local input, and output hashes.
- `wifi/build/build.log`, `firmware.log`, and `front-imports.log` for build and check output.

`make bundle` includes the upstream user-space tests. The script also checks the Front's direct imports against the KDK and strictly verifies the final bundle signature. The KDK check allows the upstream old-network vtable reserved slots; it does not test live kernel linking, the complete ABI, connectivity, or sleep/wake.

On 2026-11-11, this directory's standalone entry point was run from the public archive successfully: all 28 upstream user-space scenarios, native scan-request fixtures, Core/Front x86_64 architecture and KDK direct-import checks, and final strict signatures passed. The Core and Front executable SHA-256 values match the existing hardware-tested build. No new full-system tests or RedmiBook hardware acceptance were performed.

## Use in this project's EFI

Pass the complete bundle to the root assembly workflow:

```sh
ditto wifi/build/AirPort_RTW89.kext build/inputs/AirPort_RTW89.kext
```

See the [complete build instructions](../docs/build.en.md) for loading order, exclusion of the system IOSkywalkFamily, compatibility component handling, and USB preparation. Front is nested inside Core and still needs its own OpenCore loading entry. Copying only the Core executable does not provide the complete bundle.

## Licenses and attribution

AirPort_RTW89 and this derived local patch use the upstream GPL-2.0 license. Linux driver and header licenses follow their per-file SPDX notices. hostap uses BSD-3-Clause; Mbed TLS uses Apache-2.0 or GPL-2.0-or-later; MacKernelSDK retains its original license. Copies are in [`licenses/`](licenses/). The pinned source archive retains the third-party source and per-file notices.

The extracted source's `CREDITS.md` credits the upstream authors and Linux, Realtek, AirPort_RTW88, Realtek-AirPort-Family, OpenIntelWireless, OCLP, Acidanthera, hostap, and Mbed TLS contributors. This directory packages the build patch used by this project.
