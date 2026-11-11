# Build and trial guide

[中文](build.zh-CN.md) | [Back to README](../README.en.md)

This workflow rebuilds the machine's Tahoe 25G332 configuration into local `build/EFI/`. It does not create a macOS installer or write an EFI partition. You need your own 25G332 system files, this machine's VFCT and compatibility components. For an initial installation, prepare a bootable basic EFI first; another machine's serial numbers or VBIOS cannot replace these inputs.

## 1. Tools and repositories

Use an Intel or Apple Silicon Mac with Python 3.10 or newer, Git, Xcode Command Line Tools and `iasl`. Wi-Fi builds execute x86_64 tests, so Apple Silicon also needs working Rosetta. Obtain `iasl` from [ACPICA](https://github.com/acpica/acpica/releases) or the Homebrew `acpica` package.

```sh
git clone https://github.com/wzh4869/RedmiBook-Pro14-2022-Ryzen-Hackintosh.git
git clone https://github.com/wzh4869/Radeon-680M-Hackintosh.git
cd RedmiBook-Pro14-2022-Ryzen-Hackintosh
git -C ../Radeon-680M-Hackintosh checkout --detach a34b37d2839dff3223315188dad7851ca58060d7
python3 --version
xcrun --find clang
iasl -v
```

Keep the repositories under the same parent directory. The pinned graphics commit is `gpu.commit` in [sources.lock.json](../sources.lock.json); check out that commit in the GPU repository before building.

## 2. Download common dependencies

```sh
python3 scripts/fetch_inputs.py
```

The script downloads pinned OpenCore 1.0.5 DEBUG, Lilu, VirtualSMC, input, audio and Bluetooth firmware-loader packages, verifies SHA-256 and arranges them under `build/inputs/`. Versions and links are listed in [component sources](components.en.md) and the [lock file](../sources.lock.json).

Wi-Fi also needs these three compatibility archives. Open the links and save the ZIPs in `build/downloads/`, retaining their filenames:

| Package | Download |
|---|---|
| IOSkywalkFamily | [IOSkywalkFamily-v1.2.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IOSkywalkFamily-v1.2.0.zip) |
| IO80211FamilyLegacy | [IO80211FamilyLegacy-v1.0.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IO80211FamilyLegacy-v1.0.0.zip) |
| AMFIPass | [AMFIPass-v1.4.1-RELEASE.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-RELEASE.zip) |

Obtain these files yourself and keep them locally. Then run:

```sh
python3 scripts/prepare_compat.py
```

The script checks the pinned archive hashes and copies the required kexts without changing the system. Do not substitute newer packages with the same names.

## 3. Personal identity and VBIOS

Generate an identity once, then reuse the file for later builds:

```sh
python3 scripts/prepare_identity.py \
  --macserial build/inputs/OpenCorePkg/Utilities/macserial/macserial
```

The output is `private/smbios.plist` with permissions 0600. It supplies MacPro7,1 serial, MLB, UUID and ROM fields. If you already have a personal identity, put a plist with those fields at this path. Do not upload it.

The VBIOS must come from your own RedmiBook. Copy the ACPI table in a Linux Live system:

```sh
sudo cp /sys/firmware/acpi/tables/VFCT ./VFCT
sudo chown "$(id -u):$(id -g)" ./VFCT
```

Transfer that file to `private/VFCT` in the build repository, then run:

```sh
python3 scripts/prepare_vbios.py --vfct private/VFCT
```

The output is `private/680m.rom`. The script retains the upstream extraction method, creates the injected PCI 73ff copy and 512 MiB / 128-bit tables, and checks the checksum. It does not flash the BIOS or increase the actual firmware reservation. This workflow covers the fixed 512 MiB configuration in the hardware table.

## 4. Build graphics

Follow the [GPU build guide](https://github.com/wzh4869/Radeon-680M-Hackintosh/blob/a34b37d2839dff3223315188dad7851ca58060d7/docs/build.en.md): extract Metal input from your own 25G332 system, supply matching yellow_carp firmware and build. The result should be:

```text
../Radeon-680M-Hackintosh/build/RembrandtGfx/RembrandtGfx.kext
```

You may build on another Mac, but the system inputs must come from the target version. The driver matches the recorded 25G332 bytes; compatibility after a macOS update is not established.

## 5. Build Bluetooth and Wi-Fi

Use the [Bluetooth guide](../bluetooth/README.en.md) to obtain pinned SDK / Lilu dependencies and your own 25G332 `bluetoothd`, then build. Its output is:

```text
bluetooth/build/RealtekBluetoothCompat.kext
```

Prepare a local KDK as described in the [Wi-Fi guide](../wifi/README.en.md), then run:

```sh
python3 wifi/build.py \
  --kdk "/path/to/KDK_15.8.1_24H32.kdk/System/Library" \
  --compat-kexts build/inputs \
  --jobs 4
ditto wifi/build/AirPort_RTW89.kext build/inputs/AirPort_RTW89.kext
```

Replace the KDK path with its location on your Mac. This retains the 24H32 offline symbol check used by the previous build; it does not establish the full Tahoe ABI. Connectivity on 25G332 comes from earlier hardware testing. Front is a plugin inside Core and receives an explicit OpenCore entry.

## 6. Assemble and validate EFI

Run from the RedmiBook repository root:

```sh
python3 scripts/assemble_efi.py \
  --inputs build/inputs \
  --gpu-kext ../Radeon-680M-Hackintosh/build/RembrandtGfx/RembrandtGfx.kext \
  --bluetooth-kext bluetooth/build/RealtekBluetoothCompat.kext \
  --identity private/smbios.plist \
  --vbios private/680m.rom \
  --iasl "$(command -v iasl)"
```

Successful output is `build/EFI/` and `build/EFI-manifest.json`. The script compiles four SSDTs, adds your identity and VBIOS, checks enabled files, x86_64 architecture and dependency order, and runs the matching `ocvalidate`. It does not mount or write an ESP.

An existing output directory is refused. Add `--output build/EFI-next` for another build while retaining the previous result. Missing inputs are reported by filename.

The configuration source is [config.template.plist](../efi/config.template.plist). It keeps the current active patches and boot arguments, removing inactive Darwin 24 entries and the optional UMA logging driver. The actual graphics injection path is `PciRoot(0x1)/Pci(0x8,0x1)/Pci(0x0,0x0)`; do not copy GPD's root 0 path. Details are in [component and configuration notes](components.en.md).

## 7. Trial from a spare USB

Keep a complete working EFI and its bootable USB entry. Copy the generated `EFI` folder to the FAT32 EFI partition of another spare USB, preserving your only working EFI. Disk selection remains a manual step: check the device model and capacity before copying.

Choose the spare USB in the firmware boot menu. After reaching the desktop, check the display, keyboard, trackpad and Wi-Fi, then run the [GPU tools](https://github.com/wzh4869/Radeon-680M-Hackintosh/blob/a34b37d2839dff3223315188dad7851ca58060d7/tools/README.en.md). GPU success should print `passed: true`. Test Bluetooth pairing and input with your own peripheral.

If boot fails or new problems appear, choose the original working USB in the firmware menu. Restore the complete original EFI to the test device when needed; replacing only one kext can leave mismatched configuration. The newly assembled package has not been booted again on the RedmiBook. Build validation and historical hardware validation are separate results.

Sleep, external displays and hardware video have not been accepted. Keep `-rmbvcn` disabled. The retained `-rmbvcnprep` argument only prepares the experiment; it does not enable hardware video.
