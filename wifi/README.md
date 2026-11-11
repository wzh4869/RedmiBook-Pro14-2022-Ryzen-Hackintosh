# RTL8852BE 原生 Wi-Fi

[English](README.en.md)

本目录提供 AirPort_RTW89 原生 Wi-Fi 的固定源码、局部补丁和构建入口，用于本项目的 RTL8852BE 网卡（PCI `10ec:b852`）。连接网络使用 macOS 系统 Wi-Fi 菜单和设置，`rtw89ctl` 用于诊断。

已经在红米实机的 macOS Tahoe、系统构建 `25G332` 上确认系统菜单连接和 HTTPS 访问。保存网络、自动重连和睡眠唤醒没有专项验证；其他 Realtek 型号没有实机验证。这里的构建检查不等于重新完成这些实机测试。

## 源码和补丁

源码来自 [FranciumOS-org/AirPort_RTW89 PR #11](https://github.com/FranciumOS-org/AirPort_RTW89/pull/11) 的提交 `54ecd01ee1e3e5c0b378611a989b8d8c11e58579`，实际归档仓库为 [hrx114514x/AirPort_RTW89](https://github.com/hrx114514x/AirPort_RTW89)。PR 的扫描请求修正已经在这个提交中，本目录不重新实现它。

[`patches/0001-native-build.patch`](patches/0001-native-build.patch) 保留已使用的两文件构建修正：

- `Makefile`：用户态测试和诊断工具统一构建为 x86_64；源码归档没有 `.git` 时由参数写入来源提交；Core 与嵌套 Front 组装后重新签名并严格验证。
- `tools/check_kpi.py`：通过本地 KDK 离线核对 x86_64 直接导入符号，方便在 Apple Silicon 主机上构建 Intel 驱动。

没有修改 Linux 网卡源码，没有更改上游 bundle 版本。源码归档包含固定的 Linux、MacKernelSDK、hostap 和 Mbed TLS 内容；构建不会拉取这些项目的最新分支。全部来源、归档校验值和固件提交见 [`source-lock.json`](source-lock.json)。

## 准备依赖

在 macOS 上构建，需要 Xcode 命令行工具、macOS SDK、Python 3.9 或更新版本。Apple Silicon 主机还需要能够运行 x86_64 用户态程序，因为上游 `make bundle` 会执行这些测试。

Apple 组件由构建者自行取得并保存在本机。本仓库不包含 Apple kext、KDK 或固件二进制。

1. 从 [Apple Developer 下载页面](https://developer.apple.com/download/all/?q=Kernel%20Debug%20Kit) 取得 KDK。已有构建的离线检查使用 KDK `15.8.1 / 24H32`。`--kdk` 指向其 `System/Library`，其中需要 `Kernels/kernel`、`Extensions/IOPCIFamily.kext` 和 `Extensions/IONetworkingFamily.kext`。换用其他目标系统的 KDK 时，检查结果对应所提供的 KDK；旧 KDK 的符号检查不证明 Tahoe 的 ABI 兼容。
2. 从下面固定的 OCLP 提交下载兼容包。将解压后的 kext 放到仓库根目录的 `build/inputs/`。核对 ZIP 的 SHA-256 与 `source-lock.json` 一致。

| 包 | 固定下载链接 | 用途 |
| --- | --- | --- |
| IOSkywalkFamily 1.2.0 | [IOSkywalkFamily-v1.2.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IOSkywalkFamily-v1.2.0.zip) | 原生 Wi-Fi 运行依赖 |
| IO80211FamilyLegacy 1.0.0 | [IO80211FamilyLegacy-v1.0.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IO80211FamilyLegacy-v1.0.0.zip) | Front 的运行及符号检查依赖 |
| AMFIPass 1.4.1 | [AMFIPass-v1.4.1-RELEASE.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-RELEASE.zip) | EFI 中的运行依赖；不参与本目录编译 |

把下载的 ZIP 放到 `build/downloads/` 后，可在仓库根目录执行：

```sh
shasum -a 256 build/downloads/IOSkywalkFamily-v1.2.0.zip build/downloads/IO80211FamilyLegacy-v1.0.0.zip build/downloads/AMFIPass-v1.4.1-RELEASE.zip
mkdir -p build/inputs
unzip -q build/downloads/IOSkywalkFamily-v1.2.0.zip -d build/inputs
unzip -q build/downloads/IO80211FamilyLegacy-v1.0.0.zip -d build/inputs
unzip -q build/downloads/AMFIPass-v1.4.1-RELEASE.zip -d build/inputs
```

## 构建

在仓库根目录执行，替换 KDK 路径为自己的路径：

```sh
python3 wifi/build.py \
  --kdk "/path/to/KDK_15.8.1_24H32.kdk/System/Library" \
  --compat-kexts build/inputs \
  --jobs 4
```

脚本下载并核对固定源码归档，重新解压源码，应用局部补丁，然后调用上游 `make fetch-firmware` 和 `make bundle`。固件使用源码中固定的 linux-firmware 提交及 `firmware/SHA256SUMS` 校验；下载内容仅保存在忽略提交的 `wifi/build/` 中。

成功后得到：

- `wifi/build/AirPort_RTW89.kext`，其中包含 `Contents/PlugIns/AirPortRTW89Front.kext`。
- `wifi/build/rtw89ctl`，x86_64 诊断工具。
- `wifi/build/build-manifest.json`，记录源码、补丁、本地输入和输出文件的校验值。
- `wifi/build/build.log`、`firmware.log`、`front-imports.log`，构建和检查日志。

`make bundle` 包含上游用户态测试。脚本另外核对 Front 的 KDK 直接导入符号和最终 bundle 的严格签名。KDK 检查允许上游旧网络虚表预留槽，不验证实际内核链接、完整 ABI、网络连接或睡眠唤醒。

2026-11-11 从公开归档执行本目录的独立构建入口通过：28 个上游用户态场景、原生扫描请求样例、Core/Front 的 x86_64 架构与 KDK 直接导入检查、最终严格签名均通过。Core 与 Front 可执行文件的 SHA-256 和已有实测构建一致。本次没有新增全系统测试或红米实机验收。

## 用于本项目 EFI

把完整 bundle 交给根目录装配流程：

```sh
ditto wifi/build/AirPort_RTW89.kext build/inputs/AirPort_RTW89.kext
```

后续加载顺序、系统 IOSkywalkFamily 的排除规则、兼容组件处理及 U 盘准备见 [完整构建说明](../docs/build.zh-CN.md)。Front 位于 Core 内部，OpenCore 仍需要单独的嵌套加载项。只复制 Core 可执行文件无法替代完整 bundle。

## 许可与归属

AirPort_RTW89 的代码和本地派生补丁遵循上游 GPL-2.0。Linux 驱动及头文件按各文件的 SPDX 声明许可；hostap 使用 BSD-3-Clause，Mbed TLS 使用 Apache-2.0 或 GPL-2.0-or-later，MacKernelSDK 保留其原始许可。许可副本在 [`licenses/`](licenses/)，完整第三方源码和各文件声明保留在固定源码归档中。

上游作者及 Linux、Realtek、AirPort_RTW88、Realtek-AirPort-Family、OpenIntelWireless、OCLP、Acidanthera、hostap 和 Mbed TLS 的贡献归属见解压源码的 `CREDITS.md`。本目录只整理本项目使用的构建修正。
