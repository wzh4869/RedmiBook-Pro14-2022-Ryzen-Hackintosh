# Hardware validation summary

[中文](validation.zh-CN.md) | English | [Project README](../README.en.md)

As of **2026-11-11 (Asia/Shanghai)**, this record covers the machine listed in the [README](../README.en.md#tested-hardware). Source, configuration and build steps are now included. Historical hardware results and the new public builds are recorded separately; private raw logs are not published.

## Public build checks: 2026-11-11

The GPU executable, Wi-Fi Core / Front and generated Bluetooth patch were rebuilt from pinned public dependencies and local inputs, then compared with the tested versions. The new EFI assembler ran successfully: 73 content files, 24 load entries and 16 Tahoe kernel patches. Four rebuilt SSDTs are byte-identical to the machine's originals; x86_64, dependency order and OpenCore 1.0.5 `ocvalidate` passed. The generated personal VBIOS also matches the original injected copy.

Bluetooth native / ASan / UBSan checks and 28 upstream Wi-Fi userspace scenarios passed. They do not replace physical peripheral or radio tests. The optional UMA tool passed its existing entry tests and x86_64 UEFI build. The compact record is [publication-checks.json](publication-checks.json).

Identity sanitization, inactive Darwin 24 removal and omission of the optional logger were compared in code. The new assembled package has not been installed or booted again. The following sections report historical machine tests; no complete machine test suite was run.

## System and historical scope

| Date | System / stage | Result |
|---|---|---|
| 2026-11-09 | Sequoia 15.8.1 / 24H32 | Correcting the GPU path and PCI revision mapping (`02 → c7`) allowed initialization; 1024 Metal compute results and 1024 rendered pixels passed readback checks, together with native Wi-Fi connectivity and battery status |
| 2026-11-09 | Tahoe 26.7.2 / 25G332 | Installed and reached the desktop; Metal, the 120 Hz display, Wi-Fi, speakers / Safari video and trackpad passed their respective checks; an S1 BLE mouse passed short pairing and input checks |
| 2026-11-10 | Retained systems | The original Sequoia system volume was deleted; only Tahoe is currently retained. Historical Sequoia success does not mean that system can still boot |
| 2026-11-11 | Tahoe, local GPU candidate 23 | The combined-region allocation fallback was deployed and booted; basic rendering, large-texture samples and verified window transitions passed. Stutter showed only an uncertain partial subjective improvement |

Local candidate numbers distinguish experiments. They are neither driver version numbers nor repository release versions.

## Candidate 23: targeted and hardware results

This iteration changes the GPU binary and boot configuration to add a controllable combined-region mode, retaining the previous render-command staging implementation. Successful native allocations keep their original result. If native allocation fails and the fallback switches are enabled, Apple's native type 2 allocator assembles fragments across the full range. Removing the new switch restores candidate 22's lower-region fallback. No kernel imports were added; VCN remains disabled.

| Check type | Result | What it establishes |
|---|---|---|
| Build / static checks | Build, native symbols, compiled ABI, `ocvalidate` and verification of 74 EFI boot files passed | The candidate build and deployed content match expectations; this is not complete compatibility validation |
| Offline native allocator replay | Synthetic fragmentation produced lower-region failure / full-range success; parsing of 6512 pages, size trimming, release and rollback after an oversized failure passed | Production fallback and matching native machine code behave as expected in synthetic layouts; this does not replace hardware GPU mapping checks |
| Basic Metal hardware checks | 1024 compute results and all 1024 pixels of a 32 × 32 image were correct; the 1294-byte render writer matched the expected staging implementation | Basic compute and rendering correctness, and activation of the existing command-write change |
| Large-texture hardware checks | Held 1 / 3 / 6 Private RGBA16Float textures at 2182 × 1394, with three rounds per stage; all 480 pixel samples were correct | Sample correctness for the tested texture path, not exhaustive coverage of textures or WindowServer resources |
| Window transitions | 15 transitions among five applications and 6 Finder / Safari transitions; foreground application and main-window visibility verified on the same desktop | All 21 operations occurred; this does not directly measure visual smoothness or FPS |
| Combined-region runtime record | One WindowServer request rounded to 851968 bytes; the lower region had 720896 and the upper region 131072 bytes available. Neither was sufficient alone, their sum was exact, and the allocation returned success | At least one matching hardware fallback succeeded; subsequent pixels were not linked to that resource, and no final fallback record for a request of at least 16 MiB was captured |

Accumulated GPU memory reclamation wait was 131.693 ms for the five-application round and 68.067 ms for the Finder / Safari round. GPU recovery count was 0 in both. These are cumulative counters for each stage, not per-frame stutter durations. Pages, warm-up and time since boot differed from the previous candidate, so these measurements do not yield a controlled improvement percentage or FPS.

The user reported, “It seems a little smoother? At least the stuttering isn't as bad.” This supports an uncertain partial subjective improvement, not a claim that Safari stutter is fixed. Complete candidate 22 recovery materials were verified and retained, but a 23 → 22 rollback was not executed in this iteration.

## Other feature scopes

Manual audio, trackpad and Bluetooth checks were performed on 2026-11-09. The candidate 23 run rechecked the GPU, internal display, Wi-Fi, battery status and fastfetch; it did not repeat all manual checks for those three features.

| Feature | Tested scope | Still unverified |
|---|---|---|
| Display / battery | 2560 × 1600, 1280 × 800 HiDPI, 120 Hz; current 512 MiB VRAM, charge level and AC status read correctly | Brightness control, battery life and complete power management |
| Wi-Fi | System UI connection, loaded drivers and successful HTTPS requests; candidate 23's final HTTPS request returned 200 | Dedicated checks for saved networks, automatic reconnection and sleep/wake |
| Audio / video playback | Built-in speakers and audio output engine worked; the user confirmed at least 30 seconds of continuous Bilibili playback with sound in Safari | Microphone recording and headphone switching; VCN hardware codecs remain disabled |
| Trackpad | Movement, mechanical clicks, tap-to-click, two-finger right-click and two-/three-finger gestures | Every gesture in every application and long-term stability |
| Bluetooth | The 25G332 readiness patch was active; S1 pairing succeeded, encryption was enabled and a BLE HID device was created. Movement, buttons, scrolling and reconnection after the mouse was powered off passed short checks of at least 1 minute | Bluetooth headphones, other peripherals, high-throughput BLE, sleep and long-term stability |
| Camera / fingerprint | Hardware IDs identified | Functional validation; Touch ID is not listed as supported |

The full upstream test suite, complete machine validation, long-duration workloads, sleep/wake and external displays have not been validated. Results apply to this machine, these system builds and the listed execution paths; they do not establish automatic compatibility with future macOS updates.

See [local progress and upstream sources](components.en.md) for attribution and the pinned GPU reference revision. Foundational driver capabilities come from upstream; machine validation and local experimental changes are recorded separately.
