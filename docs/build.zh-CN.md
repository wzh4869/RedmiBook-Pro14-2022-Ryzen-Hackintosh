# 构建与试用

[English](build.en.md) | [返回首页](../README.md)

这套流程重建本机的 Tahoe 25G332 配置，输出本地 `build/EFI/`。它不制作 macOS 安装器，也不写入磁盘 EFI 分区。需要自己的 25G332 系统文件、同机 VFCT 和兼容组件；第一次装系统时，先准备能启动的基础 EFI，不能用别人的序列号或 VBIOS 代替这些输入。

## 1. 准备工具和仓库

构建机可以是 Intel 或 Apple Silicon Mac。需要 Python 3.10 或更新版本、Git、Xcode Command Line Tools 和 `iasl`。Apple Silicon 上的 Wi-Fi 构建还会运行 x86_64 测试，需要 Rosetta 可用。`iasl` 可从 [ACPICA](https://github.com/acpica/acpica/releases) 取得，或使用 Homebrew 的 `acpica` 包。

```sh
git clone https://github.com/wzh4869/RedmiBook-Pro14-2022-Ryzen-Hackintosh.git
git clone https://github.com/wzh4869/Radeon-680M-Hackintosh.git
cd RedmiBook-Pro14-2022-Ryzen-Hackintosh
git -C ../Radeon-680M-Hackintosh checkout --detach a34b37d2839dff3223315188dad7851ca58060d7
python3 --version
xcrun --find clang
iasl -v
```

两个仓库放在同一父目录。GPU 使用的固定提交见 [sources.lock.json](../sources.lock.json) 的 `gpu.commit`；在 GPU 仓库切到该提交后再构建。

## 2. 下载通用依赖

```sh
python3 scripts/fetch_inputs.py
```

脚本下载 OpenCore 1.0.5 DEBUG、Lilu、VirtualSMC、输入、音频、蓝牙固件加载器等固定包，校验 SHA-256，整理到 `build/inputs/`。完整版本与链接在 [组件来源](components.zh-CN.md) 和 [锁定文件](../sources.lock.json)。

Wi-Fi 另外需要下面三个兼容包。打开链接，将 ZIP 保存在 `build/downloads/`，保留文件名：

| 包 | 下载 |
|---|---|
| IOSkywalkFamily | [IOSkywalkFamily-v1.2.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IOSkywalkFamily-v1.2.0.zip) |
| IO80211FamilyLegacy | [IO80211FamilyLegacy-v1.0.0.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Wifi/IO80211FamilyLegacy-v1.0.0.zip) |
| AMFIPass | [AMFIPass-v1.4.1-RELEASE.zip](https://raw.githubusercontent.com/dortania/OpenCore-Legacy-Patcher/d9604c36a432eaf243ea18659ff4d208187452d7/payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-RELEASE.zip) |

这些文件由你自行取得并留在本机。下载后执行：

```sh
python3 scripts/prepare_compat.py
```

脚本核对固定归档哈希并复制需要的 kext，不修改系统。不要用新版同名包替换。

## 3. 准备个人身份和 VBIOS

生成一次身份，以后重建复用同一文件：

```sh
python3 scripts/prepare_identity.py \
  --macserial build/inputs/OpenCorePkg/Utilities/macserial/macserial
```

输出 `private/smbios.plist`，权限为 0600。它填写 MacPro7,1 的序列号、MLB、UUID 和 ROM。已有个人身份时，可把相同字段的 plist 放在这个路径；不要上传它。

VBIOS 必须来自自己的这台红米本。在 Linux Live 系统中复制 ACPI 表：

```sh
sudo cp /sys/firmware/acpi/tables/VFCT ./VFCT
sudo chown "$(id -u):$(id -g)" ./VFCT
```

把这个文件传到构建仓库的 `private/VFCT`，然后执行：

```sh
python3 scripts/prepare_vbios.py --vfct private/VFCT
```

输出 `private/680m.rom`。脚本保留原提取方法，生成给驱动注入的 PCI 73ff 副本及 512 MiB／128 bit 表，检查校验和。它不刷写 BIOS，也不会增大固件实际预留显存。本流程只覆盖硬件表中的固定 512 MiB 配置。

## 4. 构建显卡

按 [GPU 构建说明](https://github.com/wzh4869/Radeon-680M-Hackintosh/blob/a34b37d2839dff3223315188dad7851ca58060d7/docs/build.zh-CN.md) 从自己的 25G332 系统提取 Metal 输入，准备匹配的 yellow_carp 固件并构建。完成后应有：

```text
../Radeon-680M-Hackintosh/build/RembrandtGfx/RembrandtGfx.kext
```

构建可以在另一台 Mac 上完成；系统输入必须来自目标版本。驱动只针对记录的 25G332 字节匹配，不承诺更新 macOS 后仍可使用。

## 5. 构建蓝牙和 Wi-Fi

按 [蓝牙说明](../bluetooth/README.md) 取得固定 SDK／Lilu 和自己 25G332 的 `bluetoothd`，运行构建。输出：

```text
bluetooth/build/RealtekBluetoothCompat.kext
```

按 [Wi-Fi 说明](../wifi/README.md) 准备本地 KDK，再运行：

```sh
python3 wifi/build.py \
  --kdk "/path/to/KDK_15.8.1_24H32.kdk/System/Library" \
  --compat-kexts build/inputs \
  --jobs 4
ditto wifi/build/AirPort_RTW89.kext build/inputs/AirPort_RTW89.kext
```

将 KDK 路径换成你本机的实际目录。这里保留已有构建使用的 24H32 离线符号检查；它不证明 Tahoe 全部 ABI。25G332 的联网结论来自之前的实机记录。Front 是 Core 内的插件，装配配置会单独列出它。

## 6. 装配和校验 EFI

以下命令在红米仓库根目录运行：

```sh
python3 scripts/assemble_efi.py \
  --inputs build/inputs \
  --gpu-kext ../Radeon-680M-Hackintosh/build/RembrandtGfx/RembrandtGfx.kext \
  --bluetooth-kext bluetooth/build/RealtekBluetoothCompat.kext \
  --identity private/smbios.plist \
  --vbios private/680m.rom \
  --iasl "$(command -v iasl)"
```

成功后得到 `build/EFI/` 和 `build/EFI-manifest.json`。脚本编译四张 SSDT，补入个人配置与 VBIOS，检查启用的文件、x86_64 架构、依赖顺序，并运行相同版本的 `ocvalidate`。不会挂载或写入 ESP。

输出目录已经存在时会停止；再次构建可加 `--output build/EFI-next`，保留前一份结果。若缺少输入，按报错文件名补齐后重试。

配置源是 [config.template.plist](../efi/config.template.plist)。它保留当前有效补丁和启动参数，移除了不参与 Tahoe 启动的 Darwin 24 项和可选 UMA 日志驱动。显卡实际注入路径是 `PciRoot(0x1)/Pci(0x8,0x1)/Pci(0x0,0x0)`；不要沿用 GPD 的 root 0。具体差异见 [组件与配置说明](components.zh-CN.md)。

## 7. 从备用 U 盘试用

先保留完整的可启动 EFI 和对应的 U 盘引导入口。将生成的 `EFI` 文件夹放到另一只备用 U 盘的 FAT32 EFI 分区，不覆盖唯一的工作 EFI。这里只提供构建结果，磁盘选择由你核对型号和容量后手动完成。

从固件启动菜单选择备用 U 盘。进入桌面后，先检查内屏、键盘、触控板和 Wi-Fi，再运行 [GPU 测试工具](https://github.com/wzh4869/Radeon-680M-Hackintosh/blob/a34b37d2839dff3223315188dad7851ca58060d7/tools/README.md)。GPU 通过应输出 `passed: true`，蓝牙再用自己的外设进行配对和输入测试。

无法进入桌面或出现新问题时，从固件菜单选择原来可工作的 U 盘。需要恢复时，将完整的原 EFI 放回测试盘；不要只替换一个 kext，留下与它不匹配的配置。新装配包还没有重新在红米实机启动，构建通过与历史实机通过是两项不同结果。

睡眠、外屏和硬件视频没有通过验收。保持 `-rmbvcn` 关闭；`-rmbvcnprep` 只是当前保留的实验准备参数，不代表硬件视频可用。
