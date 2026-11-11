# RTL8852B Bluetooth ready patch

[简体中文](README.md)

For this repository's RedmiBook Pro 14 2022 Ryzen with RTL8852B Bluetooth **`0cb8:c559`** on macOS Tahoe **25G332**. It addresses the observed BLE connection stall before readiness that prevented the S1 mouse from pairing. Other OS builds cannot use this patch directly.

On November 9, 2026, the target machine passed S1 pairing, encryption, at least one minute of pointer/left button/right button/wheel use, and automatic reconnection after switching the mouse off and on. Headphones, other peripherals, sleep/wake and long-term use have not been tested.

## Build

Build on an Intel or Apple Silicon Mac with Python 3, Git and Xcode Command Line Tools. Start the following commands at the repository root.

### 1. Get the pinned dependencies

```sh
cd bluetooth
mkdir -p Dependencies
git clone --filter=blob:none --no-checkout https://github.com/acidanthera/MacKernelSDK.git Dependencies/MacKernelSDK
git -C Dependencies/MacKernelSDK checkout --detach 3f750085caa17ec3a7880f11c11bf4f48cd6a164
git clone --filter=blob:none --no-checkout https://github.com/acidanthera/Lilu.git Dependencies/Lilu
git -C Dependencies/Lilu checkout --detach e4748cc081bf060302c7d3c44a643ce1d11b7e1d
```

Clone only for the first build. Existing clean Git checkouts at these commits can also be passed directly to the build command. `--lilu-root` means the Lilu repository root, containing `Lilu/Library/plugin_start.cpp`.

### 2. Get bluetoothd from your own 25G332 system

On the target Mac running **25G332**, confirm the OS build and copy the executable:

```sh
sw_vers -buildVersion
cp /usr/sbin/bluetoothd "$HOME/Desktop/bluetoothd-25G332"
```

The first command must print `25G332`. When building on a different Mac, transfer the copied file to the build machine, for example to its desktop as `bluetoothd-25G332`. The build machine's own `/usr/sbin/bluetoothd` may belong to another OS build and cannot substitute for this file. Use your legally obtained system file; this repository supplies neither Apple executables nor full code pages derived from them.

### 3. Build and test

Continue in the repository's `bluetooth/` directory. Adjust `--binary` to the actual input location:

```sh
python3 build.py \
  --binary "$HOME/Desktop/bluetoothd-25G332" \
  --sdk-root Dependencies/MacKernelSDK \
  --lilu-root Dependencies/Lilu
```

A successful build produces:

- `build/RealtekBluetoothCompat.kext`: the x86_64 plugin, still version `0.2.0`.
- `build/validation.json`: build/test results, dependency commits, imports and executable hash.
- `generated/manifest.json`: input hash, original-page hash and the actual patch location.

The script checks dependency commits, generates the patch, runs native/ASan/UBSan and generator tests, then builds the plugin and audits its kmod start/stop pointers. It stops on an unsupported input or page mismatch. It only builds; it does not install or load the plugin.

Continue with the repository's [EFI build instructions](../docs/build.en.md), passing this kext to `--bluetooth-kext`.

## Generate and verify separately

To validate the input and generate the local patch without building a kext:

```sh
python3 generate.py --binary "$HOME/Desktop/bluetoothd-25G332"
python3 tests/generator.py --binary "$HOME/Desktop/bluetoothd-25G332"
shasum -a 256 -c SOURCE_SHA256SUMS
```

`tests/phy.cpp` retains its name from the earlier experiment, but tests the current Ready patch. It calls the same `applyPage` implementation used by the plugin and checks exact-page matching, the one-byte replacement, repeated application, unknown-page rejection and bounds handling.

## What the patch changes

Using Lilu, the plugin patches the in-memory code page during validation of `/usr/sbin/bluetoothd`. It changes only `74` to `EB` at x86_64 slice offset `0x216694`, entering the native connection-ready handler and continuing through the system's SMP pairing and encryption flow. It does not fabricate pairing or encryption success. The earlier PHY experiment at `0x216551` stays at its original `74`.

At runtime, the CodeDirectory CDHash must be `ac367bd0eb64f10ec8673143e52372cf21051491`, and the complete original 4096-byte page must match. The USB observer identifies `0cb8:c559`, but page patching does not depend on whether that observer has started. This plugin targets the hardware and OS combination documented here.

The generator accepts the original byte or the one known cached replacement. It restores the latter in a temporary memory buffer before checking signed original pages, without modifying the input executable. The old dispatcher, random-address and multiple-profile generation paths have been removed.

The published generator produces a header byte-identical to the version tested on November 9. On November 11, 2026, an Apple Silicon host passed the x86_64 build, the targeted tests above and verification of all 307 imports. Machine instructions match the tested binary; only Lilu's build date and the link UUID differ. No new hardware acceptance or all-peripheral test was performed for this publication.

## Source and license

Based on [tanner02/RealtekBluetoothCompat](https://github.com/tanner02/RealtekBluetoothCompat), pinned at `ef5294418e3c4c228b72c7309ba13448e382fcec`. This is an independent adaptation for this machine, not a claim of upstream RTL8852B support. Source is licensed under [GPL-2.0-only](LICENSE). See [sources.lock.json](sources.lock.json) for dependency pins and tested-source hashes, and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.

`generated/`, `build/` and `Dependencies/` are ignored. Generated headers and kexts containing full Apple pages are excluded from the source publication.
