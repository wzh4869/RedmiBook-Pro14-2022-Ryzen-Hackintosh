# RTL8852B 蓝牙就绪补丁

[English](README.en.md)

适用于本仓库的 RedmiBook Pro 14 2022 Ryzen、RTL8852B 蓝牙 `0cb8:c559` 和 macOS Tahoe **25G332**。它解决已观察到的 BLE 连接停在就绪阶段、S1 鼠标配对失败的问题。其他系统 build 不能直接使用。

2026 年 11 月 9 日实机已通过 S1 配对、加密、至少一分钟的移动/左右键/滚轮操作，以及鼠标关闭再开启后的自动重连。耳机、其他外设、睡眠唤醒和长期使用尚未验证。

## 构建

在 Intel 或 Apple Silicon Mac 上构建，需要 Python 3、Git 和 Xcode Command Line Tools。以下命令从仓库根目录开始执行。

### 1. 取得固定版本的依赖

```sh
cd bluetooth
mkdir -p Dependencies
git clone --filter=blob:none --no-checkout https://github.com/acidanthera/MacKernelSDK.git Dependencies/MacKernelSDK
git -C Dependencies/MacKernelSDK checkout --detach 3f750085caa17ec3a7880f11c11bf4f48cd6a164
git clone --filter=blob:none --no-checkout https://github.com/acidanthera/Lilu.git Dependencies/Lilu
git -C Dependencies/Lilu checkout --detach e4748cc081bf060302c7d3c44a643ce1d11b7e1d
```

只在第一次构建时克隆。已有这两个固定提交的干净 Git 工作树时，也可以直接向构建命令传入它们的路径。`--lilu-root` 指向 Lilu 仓库根目录，里面应有 `Lilu/Library/plugin_start.cpp`。

### 2. 从自己的 25G332 系统取得 bluetoothd

在运行 **25G332** 的目标 Mac 上确认系统 build，然后复制文件：

```sh
sw_vers -buildVersion
cp /usr/sbin/bluetoothd "$HOME/Desktop/bluetoothd-25G332"
```

第一条应输出 `25G332`。如果用另一台 Mac 构建，把复制的文件传到构建机，例如桌面的 `bluetoothd-25G332`。构建机自身的 `/usr/sbin/bluetoothd` 可能属于其他系统版本，不能替代目标文件。请使用自己合法取得的系统文件；仓库不提供 Apple 可执行文件或从它生成的完整代码页。

### 3. 构建和测试

继续在仓库的 `bluetooth/` 目录执行，按实际文件位置调整 `--binary`：

```sh
python3 build.py \
  --binary "$HOME/Desktop/bluetoothd-25G332" \
  --sdk-root Dependencies/MacKernelSDK \
  --lilu-root Dependencies/Lilu
```

成功后得到：

- `build/RealtekBluetoothCompat.kext`：x86_64 插件，版本保持 `0.2.0`。
- `build/validation.json`：构建、测试、依赖提交、导入符号和二进制哈希。
- `generated/manifest.json`：输入哈希、原页哈希和实际补丁位置。

脚本检查依赖提交，生成补丁，运行原生、ASan、UBSan 和生成器测试，再构建插件并检查 kmod 启停指针。输入版本或原页不匹配时会停止。它只构建，不安装或加载插件。

接下来按仓库的 [EFI 构建说明](../docs/build.zh-CN.md) 装配 EFI，将这个 kext 传给 `--bluetooth-kext`。

## 单独生成和核验

不构建 kext，只检查输入并生成本地补丁：

```sh
python3 generate.py --binary "$HOME/Desktop/bluetoothd-25G332"
python3 tests/generator.py --binary "$HOME/Desktop/bluetoothd-25G332"
shasum -a 256 -c SOURCE_SHA256SUMS
```

`tests/phy.cpp` 保留实验时期的文件名，但实际测试的是当前 Ready 补丁。它直接调用插件使用的 `applyPage`，检查原页匹配、单字节替换、重复应用、拒绝未知页和边界检查。

## 补丁做了什么

插件通过 Lilu 在 `/usr/sbin/bluetoothd` 的代码页验证路径上应用内存补丁。它只把 x86_64 slice 内 `0x216694` 的 `74` 改为 `EB`，进入原生连接就绪处理，再继续系统的 SMP 配对和加密流程；不会伪造配对或加密成功。旧 PHY 实验位置 `0x216551` 保持原始 `74`。

运行时必须匹配 CodeDirectory CDHash `ac367bd0eb64f10ec8673143e52372cf21051491` 和完整的 4096 字节原页。USB 观察器识别 `0cb8:c559`，但代码页补丁不以观察器是否已经启动为条件。本插件面向这里记录的硬件和系统组合。

生成器只接受原始字节或该补丁留下的已知缓存字节；后者在临时内存中还原后验证签名原页，不修改输入文件。旧 dispatcher、随机地址和多系统 profile 生成入口已移除。

本次公开源码的生成头文件与 11 月 9 日实测版本逐字节一致；2026 年 11 月 11 日在 Apple Silicon 上完成 x86_64 构建、上述专项测试和 307 个导入符号核对。机器指令与实测二进制一致，只有 Lilu 构建日期和链接 UUID 不同。本次没有重新进行实机验收，也没有全外设测试。

## 来源和许可证

基于 [tanner02/RealtekBluetoothCompat](https://github.com/tanner02/RealtekBluetoothCompat) 的固定提交 `ef5294418e3c4c228b72c7309ba13448e382fcec`，这是针对本机的独立适配，不代表上游支持 RTL8852B。源码采用 [GPL-2.0-only](LICENSE)。固定依赖和实测源码哈希见 [sources.lock.json](sources.lock.json)，第三方说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

`generated/`、`build/` 和 `Dependencies/` 均被忽略；包含 Apple 原页的生成头文件和 kext 不在源码发布范围内。
