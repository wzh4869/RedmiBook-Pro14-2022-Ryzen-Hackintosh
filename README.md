# RedmiBook Pro 14 2022 Ryzen Hackintosh

中文 | [English](README.en.md)

RedmiBook Pro 14 2022 锐龙版的 macOS 配置、机型补丁和构建工具。本机已运行 **Tahoe 26.7.2 / 25G332**；680M 基础加速、120 Hz 内屏、Wi-Fi、扬声器、触控板和 S1 蓝牙鼠标有实机记录，Safari 窗口切换仍会卡顿。

仓库提供脱敏配置和实际源码构建流程。需要生成自己的 SMBIOS、从本机 VFCT 提取 VBIOS，并构建显卡、Wi-Fi 和蓝牙插件；没有可直接复制安装的预编译 EFI。第一次使用请按 [构建与试用步骤](docs/build.zh-CN.md) 操作。

## 本机硬件

| 项目 | 配置 |
|---|---|
| CPU / 内存 | Ryzen 7 6800H，8 核 16 线程；16 GB LPDDR5 |
| GPU | Radeon 680M，`1002:1681` revision `02`；固定 512 MiB 显存 |
| 内屏 | BOE NE140QDM-NX2，2560 × 1600、120 Hz |
| Wi-Fi / 蓝牙 | RTL8852BE `10ec:b852` / USB `0cb8:c559` |
| 声卡 | Conexant CX11880 `14f1:1f86`，layout 15 |
| 触控板 | ELAN2310 I2C HID `04f3:3238` |
| SSD / BIOS | KIOXIA BG5 512 GB / RMARB4B0P1010 |

同名机型可能更换网卡、声卡或面板。先核对硬件；其他组合没有测试。

## 当前能用到什么程度

截至 2026-11-11，当前系统使用 `MacPro7,1` 和 GPU 候选 23。macOS 15 的结果属于历史记录，原系统卷已删除。

| 功能 | 实测范围 |
|---|---|
| 启动 / 存储 | Tahoe 进入桌面，APFS 写入与读回通过；本机仍用外置 U 盘 EFI 引导 |
| GPU / 内屏 | Metal 1,024 项计算、1,024 个绘图像素、480 个纹理样本通过；2560 × 1600、1280 × 800 HiDPI、120 Hz |
| Wi-Fi / 电池 | 系统界面连接、HTTPS 联网；电量和交流电状态正常 |
| 音频 / 输入 | 11 月 9 日实测扬声器、Safari B 站至少 30 秒、触控板移动点击和双／三指手势；键盘可用 |
| 蓝牙 | 11 月 9 日实测 S1 鼠标配对、加密、移动、按键、滚轮及关闭再开启后的短期重连 |

**硬件视频编解码关闭。** 视频可播放不等于硬解可用。Safari 卡顿尚未解决；睡眠、外接显示、麦克风录音、摄像头、指纹和长期稳定性没有验收。详细日期与测试边界见 [验证记录](docs/validation.zh-CN.md)。

## 从哪里开始

- [构建与试用步骤](docs/build.zh-CN.md)：准备依赖、个人配置、生成 EFI、从备用 U 盘试用和回退。
- [efi/config.template.plist](efi/config.template.plist)、[acpi](acpi)：本机配置和四张 SSDT 的源码。
- [蓝牙补丁](bluetooth/README.md)：RTL8852B 的 25G332 就绪阶段修复。
- [Wi-Fi 构建](wifi/README.md)：固定 AirPort_RTW89 扫描修正与本地构建补丁。
- [Radeon 680M 仓库](https://github.com/wzh4869/Radeon-680M-Hackintosh)：显卡源码、实验与 Metal 工具，集中维护在单独仓库。
- [组件来源](docs/components.zh-CN.md)：版本、上游归属和配置差异。

## 许可证

本仓库原创代码与文档采用 [GPL-2.0](LICENSE)。派生代码保留原作者声明，第三方组件按各自许可证使用。构建产物、Apple 系统文件、固件、个人身份和原始机器日志不随仓库发布。
