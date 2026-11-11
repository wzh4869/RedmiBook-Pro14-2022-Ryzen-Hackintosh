# 组件与配置来源

[English](components.en.md) | [返回构建步骤](build.zh-CN.md)

基础 RDNA 2 加速来自 [RembrandtGfx](https://github.com/caoshiyuan0211-blip/winmax2-2022-6800u-hackintosh/tree/a114bdef1d48ecf7a4672d29097af3d91eb3ff80)。本机补充 GPU 属性路径、revision `02 → c7`、Tahoe 入口、命令暂存和分配回退。完整显卡源码只在 [GPU 仓库](https://github.com/wzh4869/Radeon-680M-Hackintosh) 维护，本仓库引用固定提交。

| 用途 | 版本与来源 |
|---|---|
| 引导 / 插件基础 | [OpenCore 1.0.5 DEBUG; Lilu 1.7.2](https://github.com/acidanthera/OpenCorePkg) / [upstream](https://github.com/acidanthera/Lilu) |
| AMD 内核 | [AMD Vanilla + local 25G332 match](https://github.com/AMD-OSX/AMD_Vanilla) |
| SMC / 电池 | [VirtualSMC 1.3.8 / SMCBatteryManager](https://github.com/acidanthera/VirtualSMC) |
| 音频 | [AppleALC 1.9.8 + SimpleHDA 1.0.1; CX11880 layout 15](https://github.com/acidanthera/AppleALC) / [upstream](https://github.com/laobamac/SimpleHDA) |
| I2C 输入 | [VoodooI2C 2.9.1 / VoodooI2CHID](https://github.com/VoodooI2C/VoodooI2C) |
| PS/2 输入 | [VoodooPS2Controller 2.3.7; keyboard plugin](https://github.com/acidanthera/VoodooPS2) |
| 蓝牙 | [BlueToolFixup 2.7.2 / RealtekBluetoothFirmware 1.0.2 / local Ready fix](https://github.com/acidanthera/BrcmPatchRAM) / [upstream](https://github.com/thegwchr/RealtekBluetoothFirmware) |
| 原生 Wi-Fi | [AirPort_RTW89 PR #11 54ecd01 + local build patch](https://github.com/FranciumOS-org/AirPort_RTW89/pull/11) |
| Wi-Fi 兼容依赖 | [OCLP d9604c36: IOSkywalkFamily / IO80211FamilyLegacy / AMFIPass 1.4.1](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/d9604c36a432eaf243ea18659ff4d208187452d7) |
| 存储 / USB 共享 | [NVMeFix 1.1.3 / HoRNDIS rel9.3 (bundle 9.2)](https://github.com/acidanthera/NVMeFix) / [upstream](https://github.com/TomHeaven/HoRNDIS) |
| AMD MCE 匹配 | [AppleMCEReporterDisabler 1.2, codeless XLNC personalities](https://github.com/mikigal/ryzen-hackintosh/tree/5a1fe91a142497b994b0b9af074135207dc4043b) |

版本锁定与下载哈希见 [sources.lock.json](../sources.lock.json)。Wi-Fi 的扫描修复属于上游 PR；这里保留本机使用的交叉构建、来源标识、签名和 KDK 核验补丁。声卡、触控板、电池主要是已有驱动的机型集成，不是重新实现的驱动。

## 配置与正在运行的 EFI 有哪些差异

公开模板来自 25G332 候选 23 的实际配置。只作以下整理：

- 清空序列号、MLB、UUID、ROM，移除机器 VBIOS；装配时填入个人文件。
- 删除 Tahoe 不会选择的 Darwin 24 GPU 加载项和内核补丁。当前公开包只装配 Tahoe。
- 默认不带可选 `RmbMemoryProbe.efi` 日志驱动；原实现和构建入口保留在 [tools/memory-probe](../tools/memory-probe/README.md)。
- 与原机一样，只保留 PS/2 键盘插件，移除 IO80211FamilyLegacy 的 Broadcom 插件，并重新签名这两个 bundle。

四张 SSDT、触控板的小型 DSDT Find／Replace、Tahoe 的有效内核补丁、Booter／UEFI 设置和启动参数保留原值。GPU 注入路径是 root 1；声卡 layout 15 位于 root 0 的音频设备。

启动参数 `slide=146` 来自这台机器的启动记录；它不是所有同型号电脑通用的自动计算结果。`-rmbcmdstaging -rmballocinspect -rmballoclow -rmballocboth` 对应当前候选。`-rmbvcnprep` 仍保留，`-rmbvcn` 关闭。

模板整理由代码比较和本地装配验证，不是一次新的实机启动验收。实机结果见 [验证记录](validation.zh-CN.md)。

## ACPI、VBIOS 与许可

`SSDT-CPUR` 对应本机 16 个处理器 ID；`SSDT-EC-USBX` 与 `SSDT-PNLF` 基于固定 RembrandtGfx 的 ACPI，按本机 EC 路径和 Darwin 条件适配；`SSDT-TPD0` 与配置中的精确 DSDT 补丁用于 ELAN2310。

[vbios](../vbios) 保留固定上游的 `vfct-rom.py` 和 `augment-rom.py`，按 GPL-2.0 发布。它们只生成驱动使用的注入副本；本机的 VFCT 与 ROM 不发布。[蓝牙](../bluetooth/THIRD_PARTY_NOTICES.md) 与 [Wi-Fi](../wifi/README.md#许可与归属) 各自保留派生代码和依赖归属。

其他组件保持各自许可证。本仓库 GPL-2.0 不改变 Apple、AMD／Realtek 固件或第三方驱动的许可。[早期同型号 EFI](https://github.com/copws/RedmiBookPro2022-Ryzen-Hackintosh-EFI) 是机型研究参考，硬件组合与本机不同。
