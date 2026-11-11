# Component and configuration sources

[中文](components.zh-CN.md) | [Back to build guide](build.en.md)

Basic RDNA 2 acceleration comes from [RembrandtGfx](https://github.com/caoshiyuan0211-blip/winmax2-2022-6800u-hackintosh/tree/a114bdef1d48ecf7a4672d29097af3d91eb3ff80). Local additions cover the GPU property path, revision `02 → c7`, Tahoe entry points, command staging and allocation retries. Graphics source is maintained in the [GPU repository](https://github.com/wzh4869/Radeon-680M-Hackintosh); this repository pins a commit.

| Purpose | Version and source |
|---|---|
| Boot / plugin base | [OpenCore 1.0.5 DEBUG; Lilu 1.7.2](https://github.com/acidanthera/OpenCorePkg) / [upstream](https://github.com/acidanthera/Lilu) |
| AMD kernel | [AMD Vanilla + local 25G332 match](https://github.com/AMD-OSX/AMD_Vanilla) |
| SMC / battery | [VirtualSMC 1.3.8 / SMCBatteryManager](https://github.com/acidanthera/VirtualSMC) |
| Audio | [AppleALC 1.9.8 + SimpleHDA 1.0.1; CX11880 layout 15](https://github.com/acidanthera/AppleALC) / [upstream](https://github.com/laobamac/SimpleHDA) |
| I2C input | [VoodooI2C 2.9.1 / VoodooI2CHID](https://github.com/VoodooI2C/VoodooI2C) |
| PS/2 input | [VoodooPS2Controller 2.3.7; keyboard plugin](https://github.com/acidanthera/VoodooPS2) |
| Bluetooth | [BlueToolFixup 2.7.2 / RealtekBluetoothFirmware 1.0.2 / local Ready fix](https://github.com/acidanthera/BrcmPatchRAM) / [upstream](https://github.com/thegwchr/RealtekBluetoothFirmware) |
| Native Wi-Fi | [AirPort_RTW89 PR #11 54ecd01 + local build patch](https://github.com/FranciumOS-org/AirPort_RTW89/pull/11) |
| Wi-Fi compatibility | [OCLP d9604c36: IOSkywalkFamily / IO80211FamilyLegacy / AMFIPass 1.4.1](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/d9604c36a432eaf243ea18659ff4d208187452d7) |
| Storage / USB tethering | [NVMeFix 1.1.3 / HoRNDIS rel9.3 (bundle 9.2)](https://github.com/acidanthera/NVMeFix) / [upstream](https://github.com/TomHeaven/HoRNDIS) |
| AMD MCE matching | [AppleMCEReporterDisabler 1.2, codeless XLNC personalities](https://github.com/mikigal/ryzen-hackintosh/tree/5a1fe91a142497b994b0b9af074135207dc4043b) |

Pinned versions and download hashes are in [sources.lock.json](../sources.lock.json). The scan fix belongs to the upstream Wi-Fi PR. This repository retains the cross-build, source identification, signing and KDK checks used on this machine. Audio, trackpad and battery support primarily integrate existing drivers.

## Differences from the running EFI

The public template derives from the actual candidate 23 configuration for 25G332, with these changes:

- Serial, MLB, UUID and ROM are blank; machine VBIOS is removed. The assembler fills them from personal files.
- Inactive Darwin 24 graphics entries and kernel patches are removed. The public assembler targets Tahoe.
- The optional `RmbMemoryProbe.efi` logging driver is omitted by default. Its source and build entry remain in [tools/memory-probe](../tools/memory-probe/README.en.md).
- As on the original machine, only the PS/2 keyboard plugin is retained, the Broadcom plugin is removed from IO80211FamilyLegacy, and both bundles are signed again.

The four SSDTs, small trackpad DSDT Find / Replace patch, active Tahoe kernel patches, Booter / UEFI settings and boot arguments are retained. GPU properties use root 1; layout 15 is on the root 0 audio device.

The `slide=146` argument comes from this machine's boot record. It is not an automatically calculated value for every unit of the same model. `-rmbcmdstaging -rmballocinspect -rmballoclow -rmballocboth` select the current candidate. `-rmbvcnprep` remains present, while `-rmbvcn` is disabled.

The template has been compared and assembled locally; it has not received a new hardware boot acceptance. Hardware results are in the [validation record](validation.en.md).

## ACPI, VBIOS and licenses

`SSDT-CPUR` describes the machine's 16 processor IDs. `SSDT-EC-USBX` and `SSDT-PNLF` derive from the pinned RembrandtGfx ACPI, adapted for the machine's EC path and Darwin conditions. `SSDT-TPD0` and the exact DSDT patch handle ELAN2310.

[vbios](../vbios) retains the upstream `vfct-rom.py` and `augment-rom.py` under GPL-2.0. They generate an injected copy for the driver; the machine's VFCT and ROM are not published. [Bluetooth](../bluetooth/THIRD_PARTY_NOTICES.md) and [Wi-Fi](../wifi/README.en.md#licenses-and-attribution) retain their derived-source and dependency attribution.

Other components keep their own licenses. This repository's GPL-2.0 does not change Apple, AMD / Realtek firmware or third-party driver licenses. The [earlier EFI for this model](https://github.com/copws/RedmiBookPro2022-Ryzen-Hackintosh-EFI) was a machine reference with a different hardware combination.
