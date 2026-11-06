# SuperLoader

在 NeoForge 上跑 Fabric 模组的一键启动器 + 排错工具。

一句话：**你的整合包放进 `mods/`，`python superloader.py launch`，崩了就看 `summary.txt` 告诉你是哪个 mod、哪一层出的问题。**

跑在 Minecraft **1.21.1** + NeoForge **21.1.265** + [Connector](https://github.com/Sinytra/Connector) + Forgified Fabric API 上，Windows x64，离线单人。

---

## 先看结论：它现在能用到什么程度

- 一个 66 个 jar 的整包（性能 mod、QoL、内容 mod 混着放）能正常启动、进存档、存盘、退出码 0。
- 缺 refmap 的 Fabric mod（YACL 这类）靠内置的 companion 自动补 refmap，不用改 jar。
- BetterEnd / BetterNether 的斧头去皮（bclib 那套）能用。
- 有 6 个 mod 在 1.21.1 上就是装不上，原因都查清了：见 [docs/limits.md](docs/limits.md)。

## 三步开始

需要：Windows x64、Python 3.10+、Java 21（`java` 在 PATH 里）。

```bash
# 1. 告诉它数据放哪（只做一次，改成你自己的目录）
copy settings.example.json settings.json
#   然后编辑 settings.json：{"root": "D:\\你的目录"}

# 2. 装游戏（下载 NeoForge、libraries、natives、assets，以及 Connector + FFAPI）
python superloader.py install

# 3. 把你的模组丢进实例的 mods/ 目录，然后启动
python superloader.py launch
```

游戏会一直跑到你退出；退出后自动生成报告。

**模组放哪？** `你的目录\instances\1.21.1\mods\`。把 jar 直接丢进去就行，不用管加载器——Fabric 的、NeoForge 的、两个都支持的，都能放。

## 崩了怎么办

先看这里：`你的目录\instances\1.21.1\logs\superloader-report\summary.txt`

```
启动
  开始: 2026-11-05T13:25:11  ...
  退出码: 1（异常退出）
  致命行:
    Mixin apply for mod minihud failed ...
```

再往下看「可疑模组」段，它会写：

```
可疑模组（1）
  minihud  [L2] 崩溃栈里出现
    证据: net.minecraft.locale.Language ← ...MixinLanguage (mixins.minihud.json)
```

`L0`–`L4` 的意思：

| 层 | 含义 | 你能做什么 |
| --- | --- | --- |
| L0 | 元数据 / 依赖 | 缺前置或版本不对，按提示补 |
| L1 | API 表面 | Fabric API 模块缺口，属于工具该补的 |
| L2 | mixin 重映射 / 目标迁移 | 上游或 Connector 的问题，通常只能移出这个 mod |
| L3 | 渲染 / 内核重写 | Sodium、Iris 这类，建议用它们的 NeoForge 原生版 |
| L4 | 类加载 / 同名类 | jar-in-jar 冲突，通常要换 mod 版本 |

多数情况下处理方式就是：**把可疑的那个 jar 从 `mods/` 移走，再启动一次**。移走的 jar 建议放到 `logs/removed-mods/`，别直接删，方便以后回滚。

## 常用命令

| 命令 | 作用 |
| --- | --- |
| `python superloader.py install` | 首次安装（可重复跑，只补缺的） |
| `python superloader.py launch` | 启动（默认 4 GB 内存） |
| `python superloader.py launch --mem 8192` | 给 8 GB |
| `python superloader.py launch --dry-run` | 只打印启动命令，不启动，用来检查参数 |
| `python superloader.py report` | 不启动游戏，只按上次的数据重新渲染报告 |

环境变量（一般用不到）：

- `SL_NO_REFMAP_REPAIR=1`：关掉 refmap 自动修复
- `SL_NO_AXE_BRIDGE=1`：关掉斧头去皮桥
- `SL_QUICKPLAY="存档名"`：启动后直接进这个存档

## 报告里都有什么

都在 `logs/superloader-report/`，一般人只需要看两个：

- **`summary.txt`** — 人读的总结：启动结果、退出码、致命行、模组分组、可疑模组、mixin 失败、事件覆盖率、APIs、类加载器。
- **`launch.json`** — 这次启动的原始记录：开始/结束时间、退出码、抓到的致命行。

出问题需要细查时再看：

| 文件 | 什么时候看 |
| --- | --- |
| `mods.json` | 某个 mod 没加载？这里能看到它有没有进 ModList、来源、目标平台 |
| `mixins.json` | mixin 报错，想看是哪个 mixin、哪个目标方法 |
| `suspects.json` | 「可疑模组」的完整版（summary 只显示前 8 条） |
| `refmap_repair.json` | 想知道哪些 jar 被补了 refmap、每条映射有没有校验通过 |
| `apis.json` | Fabric API 模块缺不缺、mod 的 `depends` 满不满足 |
| `classloading.json` | 怀疑两个 mod 撞类 |
| `events.json` / `events_report.json` | Fabric 事件到底有没有在 NeoForge 上被触发 |

注意：**退出码不可信**。停在 crash screen 后关窗，退出码也可能是 0；判断有没有真的进游戏，看 summary 里的「✓ 本次启动 / ⚠ 上次运行」和进存档证据（`Time elapsed` / `Saving chunks`）。

## 它到底做了什么

三层，各管一件事：

1. **启动器（`superloader.py` + `core/`）** — Python。下载 NeoForge installer 并替换成国内可达的镜像、补齐 libraries/natives/assets、从 Modrinth 拉 Connector 和 FFAPI、拼 classpath、起游戏。
2. **companion mod（独立 Gradle 项目）** — Java，跑在游戏里。做两件事：
   - **采集**：把 ModList、事件触发、类加载器结构写成 `runtime.json` / `events.json`；
   - **修复**：启动前补缺失的 refmap（用 Yarn 映射，逐条校验）；运行期把 bclib 的「可去皮方块」接到 NeoForge 的去皮事件上。
3. **报告渲染（`core/report.py` 等）** — Python。把上面两层的数据渲染成人看的 `summary.txt` 和机器看的各个 json。

## 已知限制

- **只支持 1.21.1 + NeoForge 21.1.265**，版本写死在 `core/paths.py`。
- **只支持 Windows x64**。
- **离线单人**：账号字段是假的，只能单机。
- **Connector 上游不再给 1.21.1 发兼容修复**（官方原话：1.21.1 不再接收新的兼容性修复）。所以遇到 L2 问题，基本只能移出 mod 或等 mod 作者自己适配 NeoForge。
- 有 6 个具体 mod 装不上，原因与证据都写在 [docs/limits.md](docs/limits.md)。

## 目录结构

```
superloader.py          命令行入口
core/                   启动、下载、报告渲染
tools/                  评测台、归档脚本（一次性脚本在 tools/archive/）
compat/                 样本集、依赖闭包、调查记录、issue 草稿（已归档）
docs/                   给人和给维护者的说明
settings.json           你的本地配置（已 gitignore）
```

## 给维护者

- **换 MC / NeoForge 版本**：改 `core/paths.py` 的 `MC_VERSION` / `NF_VERSION`，`superloader.py` 的 `MOD_SLUGS` 走 Modrinth 最新匹配所以不用改；companion 的 `neo_version` 在它自己的 `gradle.properties` 里。
- **companion 怎么构建**：独立 Gradle 项目（NeoForge MDK + JDK 21），`gradlew.bat build --offline`，产物手动复制进实例 `mods/`。它不在本仓库里。
- **历史**：项目决策与踩坑记录在 [docs/handoff-archive.md](docs/handoff-archive.md)（2026-11 归档，含 39 条决策、每个 L2 案例的字节码证据）。
- **评测台**：`tools/compat_sweep.py` 可以单 mod 隔离跑并出 `compat.json`；日常用不到，只在归因时需要。
