# SuperLoader

一个极简的 Minecraft NeoForge 启动器：下载 NeoForge、补齐 libraries / natives / assets、拉取 Modrinth 模组，然后离线启动游戏。

当前目标组合：**Minecraft 1.21.1 + NeoForge 21.1.265 + Connector + Forgified Fabric API**（用于在 NeoForge 上跑 Fabric 模组）。

## 环境要求

- Python 3（开发环境为 3.13，3.10+ 应该都能跑）
- Java 21（NeoForge 1.21.1 要求；`java` 需在 PATH 中）
- Windows x64（当前只支持这一种平台）

## 用法

### 1. 配置根目录

编辑项目根目录的 `settings.json`，指定数据存放的根目录：

```json
{
  "root": "D:\\SLData"
}
```

> 目前没有 `set-root` 命令，需要手动编辑这个文件（见「已知限制」）。

### 2. 安装

```bash
python superloader.py install
```

依次执行：

1. 下载并运行 NeoForge installer（自动把官方 maven 源替换为 forgecdn 镜像）
2. 补齐 libraries
3. 抽取 Windows x64 natives（DLL）
4. 下载 assets（index + objects，线程池）
5. 从 Modrinth 拉取 Connector + Forgified Fabric API

### 3. 启动

```bash
python superloader.py launch            # 默认 4096 MB
python superloader.py launch --mem 8192 # 指定内存
python superloader.py launch --dry-run  # 只打印完整启动命令，不真正启动
```

`launch` 启动前会自动检查 `mods/` 里的 Connector 和 Forgified Fabric API：存在就跳过（不联网），缺失就自动补下，同前缀有多个 jar 时列出冲突并中止（不会自动删你的文件）。`--dry-run` 只打印检查结果和完整启动命令，不下载、不启动。

### 4. 透明化报告

`launch` 结束后会自动生成报告，也可以不启动游戏、直接重新渲染：

```bash
python superloader.py report
```

输出在 `instances/<MC版本>/logs/superloader-report/`：

| 文件 | 内容 |
| --- | --- |
| `environment.json` | MC / NeoForge / Connector / FFAPI 版本、Java、系统、类加载器结构、模组与 mixin 统计 |
| `mods.json` | 每个 mod 的 id / 名称 / 版本 / 加载结果 / 来源（mods 目录、Connector 缓存、jar-in-jar）/ 目标平台（fabric / neoforge / both / connector） |
| `summary.txt` | 人读摘要：启动结果（时间 / 退出码 / 致命行 / 数据是否新鲜）、环境、模组分组、mixin 失败、事件覆盖率与缺口、APIs 检查、类加载器 |
| `launch.json` | 本次启动记录：开始 / 结束时间、退出码、从控制台日志抓到的致命行；`report` 单独跑时复用上一次 |
| `mixins.json` | 路 B1（jar 扫描）+ 路 C（日志解析）合并的 mixin 报告 |
| `events.json` | companion 写的事件审计原始快照：GAME bus 全量事件类的注册监听器数、会话内触发次数、耗时样本（三阶段覆盖写，无历史） |
| `events_report.json` | Python 侧渲染的事件报告：覆盖率、程序化 `addListener` 缺口、非 GAME bus 边界、按 mod 的声明归属、触发次数/耗时排行 |
| `apis.json` | Python 侧渲染的 API 报告：FFAPI 模块是否全部加载、Fabric mod 的 `depends` 是否满足（含加载失败的 mod）、Connector adapter 补丁审计 |
| `classloading.json` | Python 侧渲染的类加载报告：运行期 ClassLoader 分层、顶层 jar 撞类（真冲突）、jar-in-jar 共存的归类统计、mods 与 classpath 撞名 |
| `refmap_repair.json` | refmap 合成/校验：哪个 jar 缺 refmap、合成了几条、每条映射 `verified` 三态、来源是玩家基线还是评测台样本 |
| `suspects.json` | 可疑模组清单：把本次启动里"看起来有问题"的模组挑出来（mixin 失败、没进 ModList、依赖不满足、refmap 校验失败、类冲突、日志异常按包名归因），并给人工抽查项 |
| `runtime.json` | companion mod 采集的原始运行时事实（ModList / LoadingModList 公开 API） |

`runtime.json` / `events.json` 由 companion 在游戏内写出；`environment.json` / `mods.json` / `events_report.json` / `apis.json` / `classloading.json` / `refmap_repair.json` / `suspects.json` / `summary.txt` / `launch.json` 由 Python 侧渲染，所以 companion 没跑过时报告仍可生成（只是缺少运行时字段）。

启动失败（崩溃 / 被关窗）时 `runtime.json` 不会更新：此时 `summary.txt` 的「启动」段会写明退出码与致命行，并提示「下面的 模组/事件/APIs/类加载器 是上一次运行的快照」，四个 json 顶层带 `stale: true`。注意退出码不可靠——停在 crash screen 后关窗也是 0。

`logs/` 只放运行时证据，别往里堆一次性脚本：

| 目录 | 内容 | 清理方式 |
| --- | --- | --- |
| `logs/compat/<时间戳>/` | 评测台每次运行的日志与 `compat.json` | `python tools/clean_logs.py --keep 3`（旧的打包进 `logs/archive/`） |
| `logs/baseline-*` | 基线报告快照，回归对照用 | 手删，建议每次基线变更时留一份 |
| `logs/tmp-mods-backup/` / `logs/removed-mods/` | 回滚备份 / 永久移出的 jar | 手删 |
| `logs/archive/` | 被清理的旧运行（zip） | 手删 |
| `tools/archive/` | 一次性探测/修复脚本 | 手删 |


## 版本锁定

版本是硬编码在代码里的，改版本要动这几个地方：

| 项 | 位置 |
| --- | --- |
| MC 版本 `1.21.1` | `core/paths.py` → `MC_VERSION` |
| NeoForge 版本 `21.1.265` | `core/paths.py` → `NF_VERSION` |
| Connector / FFAPI 版本 | `superloader.py` → `MOD_SLUGS`（走 Modrinth 最新匹配，不写死具体版本号） |
| 模组列表 | `superloader.py` → `MOD_SLUGS` |
| Companion mod 的 NeoForge 版本 | `D:\IDEA_mods\nfprobe\gradle.properties` → `neo_version` |

## 设计说明

- **installer 镜像替换**：NeoForge installer 内部硬编码 `maven.neoforged.net`，国内不可达。`core/installer.py` 下载后自动把 `version.json` / `install_profile.json` 里的域名替换为 `neoforged.forgecdn.net`，再运行 patched installer。
- **classpath 去重**：`mc.libraries` 和 `nf.libraries` 有重叠（如 gson），BootstrapLauncher 遇到重复条目会崩（`Duplicate key`），`core/libraries.py` 按 path 去重。
- **natives 平铺**：natives jar 里的 dll 在 `windows/x64/org/lwjgl/...` 子目录下，`java.library.path` 不递归子目录，`core/natives.py` 只提取 `.dll` 平铺到 `natives/windows/x64/`。
- **离线参数**：`--username Steve --uuid 全0 --accessToken 0 --userType legacy`，只够单人离线，不连正版服务器。
- **防误删**：`superloader.py` → `ensure_runtime_mods` 在 `install` 第 5 步和 `launch` 启动前都会检查 `mods/` 里的 Connector / FFAPI。按文件名前缀匹配，存在即跳过（零网络，离线可 launch）；缺失才从 Modrinth 补下，只补缺的那个；同一前缀下出现多个 jar 时报错并列出文件名、中止启动，不自动删用户文件。`--dry-run` 时只打印检查结果，不下载。
- **Companion mod**：独立 Gradle 项目（`D:\IDEA_mods\nfprobe`），mod id `superloader_companion`，MIT，依赖 `connector` 和 `fabric_api`（`ordering = "AFTER"`）。构建产物 `superloader_companion-0.4.1.jar` 手动复制进 `mods/`。当前职责只有审计采集，失败只记日志、不影响启动：
  - `runtime.json`：`FMLCommonSetupEvent` / `FMLLoadCompleteEvent` 两个时机，通过 `ModList` / `LoadingModList` / `IModFile` 的 discovery attributes 采集 mod 清单、加载状态、加载问题、类加载器结构。
  - `events.json`：扫 `@SubscribeEvent` 声明 + 扫 GAME bus 注册表（`load_complete` 和每次 periodic）给所有事件类挂 spy；每个事件类在 HIGHEST / LOWEST 各挂一个探针采耗时；`load_complete` / 每 30 秒 / JVM shutdown 三个时机落盘（schema 2）。
  - **不使用 mixin**：实测 Mixin 服务只处理 `TransformingClassLoader` 的类，`net.neoforged.bus.*` 在 `ModuleClassLoader` 模块层，注入不生效。
- **报告分工**：companion 只落原始事实，Python（`core/report.py` / `core/events_report.py` / `core/apis.py`）是最终报告的唯一写入者。目标平台（fabric / neoforge）由 Python 扫 jar 元数据判定：`fabric.mod.json` → fabric，`META-INF/neoforge.mods.toml` → neoforge，两者都有 → both。只扫 `mods/` 和 `runtime.json` 里实际加载的 jar，避免 Connector 缓存里已删除 mod 的残留文件污染统计。事件板块同理：`events.json` 是原始快照，`events_report.json` 由 Python 渲染，v2 新字段（`timing`、程序化注册全覆盖）读不到时自动降级。
- **apis 板块**：v1 只做可验证事实，不做「调用是否成功」。FFAPI 模块数从 jar 的 `META-INF/jars/*.jar` 元数据读；Fabric `depends` 逐条解析到运行时 mod / `provides` 别名 / 内置版本（minecraft、java、fabricloader），版本范围做尽力而为的语义比较；adapter 补丁数直接读 Connector 自己写的 `.cache/connector/patch_audit.txt`，文件早于本次启动时标 `stale`。
- **classloading 板块**：运行期归属来自 companion 的 7 个探针（按 identity 归组成 ClassLoader 实例）；静态重复类扫 `mods/*.jar` 与嵌套 jar 的 `.class`，**判据只看结构**——同一类在顶层 jar 撞才算冲突，顶层与嵌套、嵌套之间共存都算 jar-in-jar（Fabric 生态常态）；`reloc/`、fabric loader 前缀只用于给 jar-in-jar 再分一次子类。另外对重复类做 classpath 交叉：类名与 `libraries/` 撞且至少一个顶层出现才报。

## 已知限制

- **离线登录写死**：`core/launcher.py` 里账号字段是假的（`Steve` / uuid 全 0 / `legacy`），没有正版或离线账号体系，只能离线进游戏。
- **仅 Windows x64**：`core/libraries.py` 的 `os_matches` 和 `core/natives.py` 的路径/DLL 过滤都硬编码了平台。
- **版本写死**：只支持上面那套 MC + NeoForge 组合，没有版本选择。companion mod 的 `neo_version` 也要手动同步。
- **没有 `set-root` 命令**：配置只能手改 `settings.json`。
- **assets 无镜像 fallback**：installer 打了 forgecdn 镜像补丁，但 assets 仍直连 `resources.download.minecraft.net`，国内可能慢。
- **模组列表写死且很小**：只自动装 Connector + FFAPI，其它模组需手动放进 `mods/` 目录。防误删只覆盖 Connector / FFAPI，不覆盖用户手动放的模组。
- **companion mod 需手动部署**：构建后要手动把 jar 复制进 `mods/`，启动器不自动构建、不自动复制。
- **透明化报告完成 7 个板块**：mixins、environment、mods、summary、events（v2）、apis（v1）、classloading（v1）。
- **classloading v1 的口径**：运行期只探了 7 个代表类（不枚举全部类），静态扫描只看 `mods/` 与 `libraries/`（不扫 Connector 缓存）。`reported` **只含顶层 jar 撞类**；jar-in-jar 共存（顶层 vs 嵌套、嵌套 vs 嵌套）归 `jar_in_jar` 不报，这是 Fabric 生态常态，不是异常。前缀规则只做 `relocated` / `fabric_loader` 的子分类，不参与"是否冲突"的判断。`classpath_conflicts` 候选集是重复类，条件是撞 `libraries/` 且至少一个顶层出现（混合情况会报）；`library_classes` 不含 `libraries/` 里嵌套 jar 的类（131 个 jar 中 2 个有嵌套，共 513 个类）。
- **apis v1 的口径**：只覆盖 FFAPI 模块加载 / Fabric `depends` / Connector adapter 审计三个事实，不判断 API 调用是否成功，也没有 API 版本语义。`depends` 的版本比较支持 `>= <= > < = ~ ^`、空格 AND、`x` 通配，复杂范围无法判定时记 `null`（不猜）。
- **adapter 审计可能过期**：Connector 复用 `.cache/connector/` 时不会重写 `patch_audit.txt`，`apis.json` 会标 `stale` 并在 summary 提示，数字只代表上一次 remap 时的补丁情况（可能是已删掉的 mod）。
- **events 的口径**：只覆盖 GAME bus。所有在 GAME bus 注册过的事件类都会挂 spy（73/73），另有 17 个只注册在 MOD bus / 被 classChecker 拒绝的类保持未覆盖（设计边界）。`observed_since`（companion 加载时刻）之前触发的事件不计，主菜单挂机时只有渲染类事件有数，进存档才能看到 gameplay 事件；报告里的覆盖率分母是「总数 - 非 GAME bus」。
- **事件耗时是近似值**：`timing` 是同一事件 HIGHEST 探针到 LOWEST 探针之间的间隔，等于「其他监听器的处理耗时」，不含与探针同优先级的监听器，也不是 `EventBus.post` 的总墙钟时间；同一线程嵌套 post 只采最外层，探针本身每次有几十 ns 开销（可与 `posts` 对照看样本数）。
- **报告在游戏退出后才生成**：`launch` 会阻塞到游戏进程结束，然后才渲染 `environment.json` / `mods.json` / `events_report.json` / `apis.json` / `classloading.json` / `summary.txt`；游戏运行期间只有 companion 写的 `runtime.json` / `events.json`。不想重开游戏可以用 `python superloader.py report` 重新渲染。