# 可选 UMA 日志工具

[English](README.en.md)

这是当前实验 EFI 使用过的 UEFI 工具源码，在 macOS 启动前读取 680M 的预留显存和固件内存映射。正常使用驱动不需要它，所以公开装配流程默认不加载。

在仓库根目录，用自己下载的 [Zig 0.15.2](https://ziglang.org/download/) 构建：

```sh
python3 tools/memory-probe/build.py --zig /path/to/zig
```

脚本先运行已有 ASan／UBSan 入口测试，再生成 `build/memory-probe/RmbMemoryProbe.efi`。如需诊断，手动把它放到测试 EFI 的 `OC/Drivers/`，并在 OpenCore 的 `UEFI/Drivers` 中新增同名启用项。

只有卷根目录的 `RmbMemoryProbe.tag` 内容以 `RMB-U352-AUDIT` 开头时才写入 `RmbMemoryProbe.txt`；这是保留的旧实验标记。没有标记的卷不会写入。工具不写 PCI、MMIO 或 NVRAM。日志可能包含机器内存布局，不要直接上传原文件。测试结束可删除驱动、加载项和标记。

源码保留原实验实现，使用 [GPL-2.0](LICENSE)，UEFI ABI 声明来源于固定 RembrandtGfx 的 HdaSnoop。
