# 交接文档（2026-11 归档）

> **这份文件是历史记录，不是入门文档。** 想看怎么用，去 [README](../README.md)；想看哪些 mod 装不上，
> 去 [limits.md](limits.md)。
>
> 里面保留了项目跑通/踩坑的完整决策（39 条）、补丁台账、以及每个 L2 案例的字节码证据。当前状态、下一步、
> 交接清单这类内容已经过时，只作为「当时为什么这么做」的凭证。

# SuperLoader 交接文档

更新时间：2026-11-04 下午

## North Star

[NEEDS.md](NEEDS.md)：玩家把喜欢的 mod 全塞进 `mods/` 就能连续玩、不崩、崩了知道为什么。**这是兼容层项目，不是测试项目**；报告是缺口定位器，产出物是补丁。

## 项目目标

Minecraft 多加载器兼容启动器。第一阶段（已完成）：NeoForge 1.21.1 上通过 Sinytra Connector + Forgified Fabric API 跑 Fabric 模组。

只支持 Minecraft 1.21.1 + NeoForge 21.1.265 + Windows x64，版本硬编码，改动neoforge小版本号可能引入不可知问题谨慎更新。

## 当前状态

- **2026-11-06：基线重建 + Connector issue 合集**：
  - `compat/baseline-66jar.json`（66 jar，launch 2026-11-06 12:03:20 → 12:04:59，`exit 0`、`fatal 0`、`stale false`、`suspects 0`、
    `apis_issues 0`、`covers_current_mods true`）；manual 32 条沿用 `compat/manual-checks-66jar.json`
  - `compat/connector-issues.md`：6 个 L2 案例（replaymod / minihud / bumblezone / farmers-delight-refabricated /
    friends-and-foes / language-reload）的统一环境、根因、字节码证据、建议修法与提交清单
  - 报告去噪：`fatal_lines()` 与 `suspects.scan_console/scan_crash_frames` 现在按日志级别过滤——
    WARN 里附带的异常栈（如 bclib 备份存档时 `java.io.IOException: 另一个程序已锁定文件的一部分`）不再被当成致命行/可疑模组；
    WARN 栈也不再被 `crash_frame` 误判为崩溃栈。三种情况复测：干净启动 `fatal=[] suspects=0`，
    合成 FATAL 栈仍能归因到 bclib，WARN 栈被忽略
- **2026-11-05 晚：内容组试装收工**（实例 65→66 jar，companion **0.6.3**）：
  - **bclib 斧头去皮桥实测生效**：betterend `lacugrove_log` → `lacugrove_stripped_log`、betternether `nether_sakura_log` → `nether_sakura_stripped_log`；
    `latest.log` 里 `[sl-bridge] axe strip:` 共 5 条，Render thread 与 Server thread 各命中。补丁台账第 2 条
  - 内容组现状：农夫乐事换官方 NeoForge `FarmersDelight-1.21.1-1.3.4.jar`；friends-and-foes 换 NeoForge 构建
    `friendsandfoes-neoforge-5.0.4+mc1.21.1.jar`；the_bumblezone（决策 35）与 language-reload（决策 39，用户已禁用）移出；
    replaymod（决策 33）、minihud（决策 34）此前已移出，jar 都在 `D:\SuperLoader\logs\removed-mods\`
  - manual 验收 **30/32**（待核 `modmenu`、`zoomify`），auto 回归 9/9；基线仍是 `compat/baseline-57jar.json`，实例已涨到 65 jar（下次启动后重建基线）
- **2026-11-05 第二批人工验收完成**：实例 **57 jar**（18:57:18 启动 → 18:58:36，`exit 0`、`fatal 0`、`suspects 0`、`mods=164`），
  manual **31/33 pass**；`replaymod`、`minihud` 因 L2 上游缺口移出，`itemscroller` 入样本；基线 `compat/baseline-57jar.json`。
- **2026-11-05 malilib 家族体检**：malilib 0.21.10 / litematica 0.19.61 / tweakeroo 0.21.61 / minihud 0.32.60 四件套里，
  minihud 的 `MixinLanguage` 因 NeoForge 改写 `Language.loadFromJson`（2 参 → 转发 3 参）而注入失败、启动即崩；
  其余三个没有碰 `Language`。详见决策 34 与 `compat/minihud-investigation.md`。
- **2026-11-05 replaymod 调查结案**：不是 mod 自身 bug、不是 refmap 缺口，是 Connector 把
  `@At(INVOKE, target=Screen;renderWithTooltip, shift=AFTER)` 重写成 `DeltaTracker;getGameTimeDeltaTicks()`
  且丢掉 `shift`（NeoForge 21.1 已用 `ClientHooks.drawScreen` 替换该调用点）→ 每帧在 GUI 之前触发、`GuiGraphics` 仍为 null。
  簇只有它一个，不写特判；按 Connector 上游 issue/PR 处理（决策 33、`compat/replaymod-investigation.md`）。
- **2026-11-05 suspects 补齐**：新增 `crash_frame` 来源（靠 `at TRANSFORMER/<modid>@` 栈帧归属，L2）与
  Fabric Loader 依赖失败来源（`HARD_DEP_NO_CANDIDATE`/`Resolution failed` → L0）；`launch.json` 的 `fatal[]` 现在会带上
  真实异常行（`_FATAL_EXCEPTION`），summary「致命行」不再只有 crash report 头；三负例回放全 PASS。
- `install` / `launch` 验证通过；NeoForge mod（JEI）+ Fabric mod（Comforts）同实例加载成功
- Connector + FFAPI 自动从 Modrinth 下载；`ensure_runtime_mods` 防误删（存在即跳过、缺失只补缺、同前缀多文件冲突报错不删、`--dry-run` 只打印），用户手动放入的模组启动器不干涉也不应该干涉
B 组（Jade + AppleSkin，Fabric + NeoForge 混合）：
  - mods: count=66, by_mod_id=66, by_target={both:5, connector:1, fabric:12, game:1, loader:1, neoforge:46}, issues=0
  - apis: FFAPI 44/44, fabric_depends 全 satisfied, adapter 审计 stale（已知）
  - events: coverage=1.0（93 类 / spied 76 / unspied 0 / programmatic 0）
  - classloading: reported=0, jar_in_jar=245, classpath_conflicts=0
  - multi_version_mods=7（5 FFAPI + 2 CCA）

C 组（错误路径）与 Sodium 实测，2026-11-03 晚：
  - 启动结果与新鲜度已接入报告：`launch.json`（started_at / finished_at / exit_code / fatal），`summary` 新增「启动」段，旧快照打 `⚠ 上次运行（早于本次启动）`
  - dep-test（depends `fabric-screen-api-v1 >=99.0.0`）：FML pre-loading FATAL + crash screen，`apis` 报 `fabric_dep_missing`；但整轮 Fabric mod 被 Connector 跳过（见决策 28）
  - Sodium 0.8.13 **Fabric 版**（测法错误）：`VertexConsumer` 的 `@WrapMethod` 签名不匹配 → mixin apply FATAL，exit=1，summary 列出 4 条致命行与 `failed=1`
  - Sodium 0.8.13 **官方 NeoForge 版**（`sodium-neoforge-0.8.13+mc1.21.1.jar`）实测通过：进「新的世界」、无 FATAL、events 93/76、classloading 冲突 0；结论与路线见决策 29 + `ROADMAP.md`

兼容评测台首轮（2026-11-04 12:45–12:52，`logs/compat/20261104-124552/`）：
  - `tools/compat_sweep.py` 单样本隔离跑：**auto 9/9 pass**，每个 40 s 左右，全部 `sample_loaded=true` + 强进存档证据 + 无 FATAL
  - 隔离方式 = 实例 `mods/` 与 `mods.compat/<slug>/` 交换（`SL_MODS_DIR` 只影响 Python 侧报告，游戏只认 `gameDir/mods`）；异常中断用 `--restore-mods`
  - 负例：`carpet` fail(L2)（crash report 点名 `PistonStructureResolver_customStickyMixin` 两个方法 + `Level_fillUpdatesMixin#updateNeighborsMaybe`）；`mixintrace` pass（L4 假设推翻）
  - jar 级负例控制：dep-test → fail(fatal_in_log) L0；Fabric Sodium → fail(fatal_in_log) L2
  - manual 20 条已人工核（2026-11-05，全 pass；manual 分母 34，覆盖 20/34）：12 条来自 36-jar 基线 + 8 条新增样本（better-ping-display-fabric / held-item-info / fpsdisplay / reacharound / cave-dust / wakes / better-selection / chatpatches）

整包基线（2026-11-05 13:25 启动，`compat/baseline-44jar.json`）：
  - mods 44 jar（在 36 基础上加上述 8 个，无移除），companion 0.5.2 / connector 2.0.0-beta.17 / FFAPI 0.116.15
  - `exit_code=0`、`fatal=0`、`stale=false`、`suspects=0`、`classpath_conflicts=0`、`apis_issues=0`（本次启动刷新了 adapter 审计，`adapter_audit_stale` 消失）
  - 剩余未装主样本 13 个：9 个非 malilib（presence-footsteps/optigui/replaymod/stendhal/custom-splash-screen/hold-my-items/universal-graves/lenient-death/totemcounter）+ malilib 家族 4 个（malilib/litematica/tweakeroo/minihud），清单与前置见「交接要点」

## 修复补丁台账

1. **refmap 缺失修复**（companion 0.5.0，2026-11-04）
   - 缺口：Connector 只重映射 jar 里**已有**的 refmap；声明了 refmap 但文件没打进 jar 的 mod 拿不到任何映射，`@Inject(method=...)` 只能按注解里的 dev 名找目标 → `No refMap loaded`（yacl 的 `MinecraftMixin#closeImages` 即此类）
   - 补丁：`com.superloader.companion.repair.RefmapRepair`（companion 内，独立 main），启动前由 `superloader.py:_refmap_repair()` 调用；读 connector 的 `mappings/mappings.tiny`，解析每个 mixin 类的 `@Mixin`/注解字符串，合成 refmap 写回 mod jar
   - **tiny v1 列布局（别看错）**：表头 `v1 official intermediary mojang`，命名空间 0 基编号 official=0 / intermediary=1 / **mojang=2**（1 基是第 3 个）；成员行字段 0 基：`0 METHOD|FIELD, 1 owner(official), 2 desc(official), 3 official 名, 4 intermediary 名, 5 mojang 名`。即 `p[5]` 才是 mojang 名
   - **refmap 约定**：key = mixin 注解里写的原字符串（dev/intermediary，`method_1490`、`Lnet/minecraft/class_310;close()V`，保持原样）；value = **mojang** 描述符 `L<mojang 类>;<mojang 名><描述符>`，不能留 `class_`/`method_`/`field_`。refmap 的类 key 用 mixin 类全限定名（斜杠形式）
   - 覆盖类别：所有「`mixins.json` 声明 refmap 但 jar 内缺该文件」的 Fabric mod（实例里目前只有 yacl）；不针对单个 mod 行为打补丁
   - 备份/回滚：`mods/.superloader-refmap/backup/` + `manifest.txt`；`java -cp superloader_companion-*.jar com.superloader.companion.repair.RefmapRepair --mods <dir> --connector <jar> --report <json> --restore`
   - 开关：`SL_NO_REFMAP_REPAIR=1`
   - **0.5.2：每映射静态校验 + Yarn 兜底 + 来源标注**（2026-11-04 20:00）
     - `compat/mappings.lock.json` 锁 Yarn `1.21.1+build.3`，sha1 `53c8c972…18822`；下载后必须校验 sha1，不一致删除且不加载（`--yarn-version`/`--yarn-sha1` 成对传入）
     - 校验三态写进 `refmap_repair.json` 的每条 `mappings[]`：`verified: true`（校验通过）/ `false`（映射表说成员不存在）/ 无法判断（`unverifiable`，如 netty、DataFixerUpper、JDK 类）。totals 同时给 `entries / verified / unverified / unverifiable / unresolved / origins`
     - 校验不只针对合成出来的条目，也复核 mod **自带**的 refmap（`via: existing`）——自带 value 多是 intermediary，先翻 mojang 三元组再查运行期类
     - 查找链：`byInterName(owner)` → 全表 `byInterNameAnywhere`（父类声明成员，如 carpet 的 `AbstractArrow.tick` 实际在 `Entity`）→ 运行期类沿**父类 + 接口**链查（`Level.hasNeighborSignal` 在 `SignalGetter`）→ 映射表 `hasMojangMember`
     - 实例 25 jar 实测：`条目 556，校验通过 511，校验失败 0，无法校验 45，未解析 0`；来源 `玩家基线 6 / 评测台样本 10`（评测台残留 jar 在 corpus 里能识别）
     - 45 条无法校验均为非 MC 类或非 refmap value（netty/DFU/JDK、mod 自身类、`@At` 选择器），属预期
     - 启动验收（2026-11-04 20:06:39 → 20:08:13，**退出码 0**）：carpet 永久移出后进入存档「新的世界」（`Time elapsed` 2 条、`Saving chunks for level` 18 条、`YACLConfig` 正常反序列化），`closeImages` / `failing mixins` / `incompatible Fabric mod` 均 0；本次 refmap 199 条，校验通过 182，失败 0，无法校验 17；summary `stale=False`
   - 状态：**已启动验证（2026-11-04 14:23:59 → 14:24:54，退出码 0）**——yacl 7 个 mixin 在 `mixins.json` 里全部 `declared`（此前 `MinecraftMixin` 为 `failed`），`latest.log` 中 `closeImages` / `failing mixins` 命中 0；Mod List 完整列出全部 Fabric mod；进入存档「新的世界」（`Time elapsed: 338 ms`、`Steve logged in`）、FastQuit 正常存档退出；报告 `mods=105 mixins=549 events=93 apis_issues=0 cls_issues=0 stale=False`
   - 已永久移出 mods/ 的 jar：`fabric-carpet-1.21-1.4.147+v240613.jar`（已知 L2 负例，`Level_fillUpdatesMixin#addFillUpdatesInt` 常量修改注入失败），现在在 `D:\SuperLoader\logs\removed-mods\`，**不再放回实例**；实例 mods/ 为 24 jar
   - 已知噪音：FML 启动时提示 `superloader_companion (version 0.4.1 -> 0.5.1)`，但 `mods/` 只有 0.5.1、`mods.toml` 与 `VERSION` 均为 0.5.1，来源未定位，不影响启动
   - 已知噪音 2：`Skipping jar ... is a Fabric mod and cannot be loaded` 是 FML 第一遍扫描（Connector 接管前）的必现日志，成功启动里也有，不是失败信号

2. **bclib 去皮桥**（companion 0.6.0 → 0.6.3，2026-11-05）
   - 缺口：bclib 的 `AxeItemMixin` 把去皮逻辑挂在 `AxeItem.getStripped(BlockState)`（`@Inject` HEAD，cancellable），
     靠 `org.betterx.bclib.interfaces.tools.AxeCanStrip#strippedState(BlockState)` 给自定义方块提供结果。
     NeoForge 21.1 起斧头改走 `BlockState.getToolModifiedState(UseOnContext, ItemAbility, Z)` → 数据映射
     `NeoForgeDataMaps.STRIPPABLES`，`getStripped` 变成 private 且全 jar 无调用者 → 注入点成了死代码：
     不报错、也不生效（betterend/betternether 的方块斧头不去皮）
   - 补丁：`com.superloader.companion.AxeStripBridge` 监听 NeoForge 的 `BlockEvent.BlockToolModificationEvent`
     （`EventHooks.onToolUse` 会为斧头发这个事件），当 `getItemAbility() == ItemAbilities.AXE_STRIP`、
     方块实现 bclib `AxeCanStrip`、且 `finalState` 没有被换成**另一个方块**时，用 `strippedState(state)` 作为结果
   - **`finalState` 语义（0.6.0/0.6.1 的坑）**：NeoForge 把事件的 `finalState` 初始化成**原方块状态**，不是 null；
     用 `finalState != null` 判断"别人已经给了结果"会永远提前返回 → 桥装上了但从不命中。正确判据是
     `finalState.getBlock() != state.getBlock()`
   - 覆盖类别：所有依赖 bclib `AxeCanStrip` 的模组（betterend / betternether / 后续 betterx 系），不认 mod id、不认 jar 名
   - 兼容性：接口按**名字符串**递归判断（子接口 + 父类链），方法用反射 `getMethod("strippedState", BlockState.class)`；
     先用 `Class.forName` 判断 bclib 是否存在会在 Connector 的独立加载器下抛 `ClassNotFoundException` 并静默禁用（0.6.0 的坑）
   - 开关：`SL_NO_AXE_BRIDGE=1` 或 `-Dsuperloader.axeBridge.disabled=true`
   - 日志：安装 `[sl-bridge] axe strip bridge installed ...`（0.6.2+ 另打加载器可见性与首个 tool 事件）；前 5 次命中打 `[sl-bridge] axe strip: <旧> -> <新> (hit #n)`
   - 状态：**已实测生效（2026-11-05 20:55，companion 0.6.3，实例 65 jar）**——`latest.log` 里 5 条 `axe strip:`，
     `betterend:lacugrove_log -> betterend:lacugrove_stripped_log`、`betternether:nether_sakura_log -> betternether:nether_sakura_stripped_log`

| 板块 | 状态 | 数据来源 |
| --- | --- | --- |
| mixins | ✅ 285 条 | 路 B1 jar 扫描（含 `META-INF/jarjar/`）+ 路 C 日志解析（纯 Python） |
| environment | ✅ | companion `runtime.json` + Python |
| mods | ✅ 56 个 | companion `runtime.json` + Python jar 元数据 |
| summary | ✅ | Python 汇总 |
| events | ✅ v2（覆盖 73/73，32 类有耗时样本） | companion GAME bus spy + `@SubscribeEvent` 扫描 + `listenerLists` 全量补挂 + HIGHEST/LOWEST 双探针；Python `core/events_report.py` 渲染 |
| apis | ✅ v1（FFAPI 44/44、depends 13/13、adapter 审计） | Python：FFAPI jar 嵌套模块 + `fabric.mod.json` depends + Connector `patch_audit.txt`；与 `runtime.json` 求交 |
| classloading | ✅ v1（3 个 loader / 1030 重复全归 jar-in-jar / 0 顶层冲突） | Python：companion `runtime.json` 的 7 个 ClassLoader 探针 + `mods/*.jar` 嵌套静态扫描 + `libraries/` 交叉 |

## 数据链

```
companion（游戏内，NeoForge 侧）
FMLCommonSetupEvent → runtime.json (common_setup)
FMLLoadCompleteEvent → runtime.json (load_complete)
FMLLoadCompleteEvent → events.json (load_complete)
每 30s → events.json (periodic)
shutdown hook → events.json (shutdown，最终快照)
※ events v2（0.4.1）：load_complete 和每次 periodic 扫 GAME bus `listenerLists` keys 补挂 spy，
  所以进存档后延迟注册的事件类也能覆盖；每类 HIGHEST/LOWEST 双探针采耗时
※ events.json 三阶段互相覆盖，无历史；report 只读最后一份
▼
Python（core/report.py + core/events_report.py + core/apis.py + core/classloading.py，最终报告唯一写入者）
environment.json / mods.json / events_report.json / apis.json / classloading.json / refmap_repair.json / suspects.json / summary.txt
▲
└── jar 元数据扫描：mods/*.jar + runtime 实际加载的 jar + 嵌套 jar
└── apis 额外输入：runtime.json（加载集合/版本/Java）+ .cache/connector/patch_audit.txt（Connector 自己写）
└── classloading 额外输入：runtime.json 的 classloading 探针 + libraries/ 的 classpath jar 名
```

关键设计：**companion 只落原始事实，Python 渲染最终报告**。因此报告可以离线重算：

```bash
python superloader.py report     # 不启动游戏，重渲染 environment/mods/summary/mixins/events_report/apis/classloading（events 用上一次快照）
```

目前 `launch` 会阻塞到游戏退出才渲染报告；游戏运行期间只有 `runtime.json` / `events.json`。

### 报告文件

```
D:\SLData\instances\1.21.1\logs\superloader-report\
├── mixins_declared.json   # 路 B1：jar 扫描（285 条）
├── mixins_logged.json     # 路 C：日志解析（正常环境 []）
├── mixins.json            # 合并（285 条 declared）
├── launch.json            # 本次启动记录（时间/退出码/致命行；只跑 report 时复用上一次）
├── runtime.json           # companion 采集的原始运行时事实（~34KB）
├── events.json            # companion 事件快照（schema 2：全量 spy + timing；覆盖写）
├── events_report.json     # Python 渲染的事件报告（覆盖率 / 缺口 / 归属 / 耗时）
├── apis.json              # Python 渲染的 API 报告（FFAPI 模块 / Fabric depends / adapter 审计）
├── classloading.json      # Python 渲染的类加载报告（运行期 loader 分层 / 静态重复类 / classpath 冲突）
├── refmap_repair.json     # refmap 合成/校验结果（每条映射 verified；来源玩家基线/评测台样本）
├── suspects.json          # 可疑模组清单（整包验收：只核这几项，不用逐个点）
├── environment.json       # 版本 / Java / 系统 / 类加载器 / 统计
├── mods.json              # 每个 mod 的加载结果 / 来源 / 目标平台
└── summary.txt            # 人读摘要
```

## 代码结构

```
SuperLoader/
├── settings.json              # {"root": "D:\\SLData"}，数据根目录
├── superloader.py             # CLI：install / launch / report；ensure_runtime_mods；报告接入
├── README.md                  # 用户向文档
├── HANDOFF.md                 # 本文件
├── tools/
│   └── inspect_mdk.py         # 扫 MDK 项目结构 + 模板残留
├── core/
│   ├── paths.py               # 所有路径从 root 推，版本常量
│   ├── downloader.py          # 下载 + 重试 + SHA1
│   ├── modrinth.py            # Modrinth API
│   ├── installer.py           # installer + forgecdn 镜像替换
│   ├── libraries.py           # os_matches + 补全 + classpath
│   ├── natives.py             # natives jar + dll 平铺
│   ├── assets.py              # asset index + 3911 objects
│   ├── launcher.py            # 合并 JSON + 占位符 + 启动 + 日志落盘
│   ├── mixin_scan.py          # 路 B1
│   ├── mixin_audit.py         # 路 C
│   ├── mixin_merge.py         # 合并
│   ├── events_report.py       # events 渲染：覆盖率 / 程序化缺口 / 非 GAME bus / 归属 / 耗时
│   ├── apis.py                # apis 渲染：FFAPI 模块 / Fabric depends / adapter 审计
│   ├── classloading.py        # classloading 渲染：运行期 loader 分层 / 静态重复类 / classpath 冲突
│   └── report.py              # environment / mods / summary 渲染
└── logs/                      # (项目侧，实际数据在 instance 下)
```

Companion mod（独立 Gradle 项目，不在 SuperLoader/ 内）：

```
D:\IDEA_mods\nfprobe\
├── src/main/java/com/superloader/companion/
│   ├── SuperLoaderCompanion.java        # 审计采集器（0.4.1）
│   └── SuperLoaderCompanionClient.java  # 客户端配置屏骨架
├── src/main/templates/META-INF/neoforge.mods.toml
└── build/libs/superloader_companion-0.4.1.jar
```

## 数据目录结构

```
D:\SLData
├── cache\ # neoforge installer (+patched)
└── instances\1.21.1
├── libraries\ (106) versions\ natives\windows\x64\ (8 dll) assets
├── mods\ # Connector + FFAPI + 用户 mod + companion
├── .cache\connector\ # Connector 重映射产物（含已删 mod 残留）
├── config\connector.json
└── logs\superloader-report\ # 12 个报告文件（含 launch.json）
```

## JSON 结构陷阱（写消费代码前必读）

- `events.json`：顶层 dict（`schema / stage / generated_at / method / observed_since / registration_view / events / totals`）；`events` 是 **list[90]，异构**——spied=true 有 `registered`/`posts`，spied=false **可能缺这两个字段**，必须 `.get()`。`declared_by` 格式 = `modid:全限定类#方法`。三阶段覆盖写，无 history。schema 2（0.4.1）起每条可能带 `timing{count,total_ns,max_ns}`，**无样本时是 null**
- `events_report.json`：**Python 渲染产物，不要手改**。`events` 里每条 = 原始字段 + `simple` / `status` / `timing`；`status` ∈ `observed / never_triggered / programmatic / non_game_bus / unspied`；`timing` 为 `null` 表示该事件没有耗时样本（0.4.1 下刚启动/未触发时为 null）。`gaps` 只放事件全名列表，计数在 `totals`
- `launch.json`：**Python 写**。`started_at / finished_at / exit_code / dry_run / console_log / fatal[list]`。`report` 命令单独跑时复用上一次的 `launch.json`，不要手改；`fatal` 从 `superloader-launch.log` 按 `_FATAL_PATTERNS` 抓（最多 5 条，每条截 400 字符）
- `apis.json`：**Python 渲染产物**。顶层是 dict；`ffapi.modules` 是数组（`id / jar / version / loaded`），`fabric_depends[].depends[]` 每条带 `satisfied`（`true/false/null`），`connector_adapter` 带 `stale` 标志（过期时数字不可当本次结果用）。`issues` 是统一的问题列表，`totals` 只是计数
- `stale`：`environment.json` / `mods.json` / `events_report.json` / `apis.json` / `classloading.json` 顶层都有。`true` = 本次启动没有产出新的 `runtime.json`（启动失败/崩溃/被关窗），这四个文件里的数字是**上一次运行**的快照；`null` = 没有 launch 记录（只跑过 `report`）。`summary.txt` 的「启动」段会直接打警告
- `mods.json` 的 `issues` 有两个来源：`runtime.json` 的 `LoadingModList` issues（无格式化文本，只有 translationKey/args/cause），以及 `stale=false` 时补的 `mod_not_loaded`（jar 在 `mods/` 里但没进本次 ModList）
- `suspects.json`：**整包验收的入口**，顶层 `{schema, generated_at, count, suspects[], scanned}`。每项 `{mod_id, jar, severity(high/medium/low), reasons[{code,detail}], manual_check, evidence[]}`。`reasons[].code` 目前有 `mixin_failed` / `mod_not_loaded` / 依赖类 issue / `refmap_unverified` / `class_conflict` / `log_error`。日志归因用「模组 jar 的包目录前缀（最多三级）」匹配 `latest.log` 里的 `[ERROR]/[FATAL]/Exception/Caused by:`，所以 `carpet.mixins.json` 这种包级名字也能归到 carpet；不按 loader/vanilla 前缀硬过滤，靠"能否归到某个 mod"来丢弃无关行。`count=0` 不等于功能正常，只等于「本次启动没有模组级异常」
- `apis.json` 的 `fabric_depends[]` 带 `loaded`：`false` = 该 jar 在 `mods/` 里但没加载成功（顶层 jar 一律检查，嵌套 jar 仍只查已加载的）。`depends[].range` 可能是**字符串数组**（Fabric 语义「任一满足」），不要当字符串拼
- `classloading.json`：**Python 渲染产物**。`runtime.loaders[]` 按 ClassLoader identity 归组；`static.duplicates.reported[]` 每项是 `{class, category, occurrences:[{jar, nested}]}`，`category` 现在的取值是 `conflict`（只有顶层 jar 互相撞类才会进来）；`filtered.by_category` 含 `relocated` / `fabric_loader` / `jar_in_jar`（`jar_in_jar` 是 jar-in-jar 共存的兜底计数）；`classpath_conflicts` 的候选集是 `duplicates`（重复类），条件是类名在 `library_classes` 里**且 occurrences 至少有一个顶层出现**（`any(nested is None)`），不按包名前缀过滤。`environment.json` 的 `classloading` 是它的 compact 版（dict，**不再是原来的探针数组**）
- `mixins.json`：顶层 **list[285]**，不是 dict；字段 `config / mixin / full_name / mod / jar / nested_jar / env / required / targets / status / reason / source[list]`。`jar` 外层、`nested_jar` 内层
- `mods.json` 的 `target: "both"`：**不是“双 loader mod”**，而是“同一 mod 被 Fabric 和 FML 各带了一份”（jar-in-jar 让同一个模块出现在两个容器里）。当前 5 个 FFAPI 模块就是这种情况
- mod id 归一化依据：`fabric.mod.json` 的 `id` 用连字符（`fabric-screen-api-v1`），`neoforge.mods.toml` 的 `modId` 用下划线（`fabric_screen_api_v1`），两套命名指向同一模块。实测证据：Mod Menu 内嵌的 `fabric-screen-api-v1` 和 Forgified 的 `fabric_screen_api_v1` 是同一模块不同版本（2.0.24 vs 2.0.26）
- `mods.json`：Fabric 模组在 ModList 里是一等公民，**不能靠 ModList 判断 loader**，只能看 jar 元数据（`fabric.mod.json` vs `META-INF/neoforge.mods.toml`）。`mods[]` 按**归一化 mod_id** 唯一（Fabric 连字符 ↔ FML 下划线视为同一 mod），不再是 mod_id 原样唯一。多版本条目带 `versions: [...]` 和 `multi_version: true`，`version`/`jar`/`container` 取 FML 侧（`types` 含 `neoforge` 的 primary）。顶层有 `multi_version_mods: [{mod_id, versions}]`。`by_mod_id` 是归一化后去重数量，`count` 是条目数
- FFAPI：`fabric.mod.json` 被改名成 `.old`，46 个 Forgified 条目元数据上是 `neoforge`，报告必须单独分组
- mod id 双命名：Fabric 连字符 ↔ FML 下划线，索引必须双向归一化
- 扫 `.cache/connector/` 的任何统计必须与 `runtime.json` 实际加载集合求交（防幽灵 mod）

## 被否决的路线（试过，别再试）

- **mixin 计数 `EventBus` / `ListenerList`**：❌ `net.neoforged.bus.*` 由 `ModuleClassLoader` 加载，mixin 服务看不到。`-Dmixin.debug=true` 确认 `EventBusMixin` 无 Mixing，同配置 `SelfProbeMixin` 正常。任何"靠 mixin 改 FML/NeoForge 内部"的方案先做这个探针
- **`mixins.json` 与 runtime 求交防幽灵**：❌ 不需要。`mixin_scan.py` 只扫 `mods/*.jar`，不扫 `.cache/connector/`。`sl_cmp.py` 的 basename 对比是假阳性（runtime 路径是绝对路径/mapped 名）
- **`Mixins.getConfigs()`**：❌ 恒 0，与框架注册无关
- **`-javaagent` 做 mixin 审计**：❌ MixinTransformer 不实现 ClassFileTransformer
- **events 全量覆盖 90 个**：❌ MOD bus 17 个被 classChecker 拒绝，接受为边界
- **Forbric 路线**（双 runtime / 合并基底 / 伪造 loader 身份）：❌ 九层病因；`MergedBaseBuilder` 1000 处方法冲突、200+ Forge 事件丢失、103 个零触发、静默失效。Connector 单宿主 + API 兼容层是唯一可行方案
- **用包名前缀白名单判断重复类是否冲突**：❌ 前缀是开放集合（dev.architectury、me.shedaniel、com.github.*、io.github.*…），白名单永远补不完；A 组多模组测试里 362 条 jar-in-jar 全被误报成冲突。判据必须用结构：occurrences 里 `nested` 为 null 的才是顶层 jar，**只有顶层 vs 顶层才算冲突**
- **fork Connector / 合成 jar 改类 / 抄 GPL 代码**：❌
- **为 L3 渲染重写类 mod（Sodium / Iris / Indium / c2me）写逐 mod 兼容层**：❌ 这些直接改渲染管线或线程模型，失败层是 mixin remap 与注入点，属 L3 边界；官方有 NeoForge 构建就用原生（Sodium 见决策 29）。注意：**这不等于"不给 Connector 写兼容层"**——主线仍是 Connector 跑 Fabric 原生 mod，补丁打在 L1/L4 桥接层，见 `ROADMAP.md` §3
- **按 mod_id 单键建索引**：❌ jar-in-jar 生态下同名模块多版本是常态，单键必然覆盖。必须用 `(mod_id, version)` 建键，并在输出时按归一化 mod_id 合并

## 关键技术决策

1. installer 硬编码 `maven.neoforged.net`：下载后替换 `version.json` / `install_profile.json` 域名为 `neoforged.forgecdn.net`（82 处）
2. installer 要求 `launcher_profiles.json`，空目录报 "There is no minecraft launcher profile"
3. 21.1.265 不生成 `*_args.txt`：读两个 JSON，合并 libraries + arguments
4. classpath 去重：按 `downloads.artifact.path`，106 条，否则 BootstrapLauncher 抛 Duplicate key
5. installer 不下 natives 和部分 libraries：补 50 个原版库；dll 在 `windows/x64/org/lwjgl/...` 必须平铺（`java.library.path` 不递归）
6. `os_matches` 遇 features 直接 continue，否则拼进未替换占位符
7. Modrinth slug：`connector`（u58R1TMW）、`forgified-fabric-api`（Aqlf1Shp）
8. 离线参数：`--username Steve --uuid 全0 --accessToken 0 --userType legacy`
9. 防误删按前缀 `connector-*.jar` / `forgified-fabric-api-*.jar`，多文件报错不删
10. Companion 版本范围：connector 依赖 `[2.0.0-beta.17,)`
11. `Mixins.getConfigs()` 恒 0 → 路 B 转 jar 解析
12. `MixinApplyError` 是唯一 FATAL 信号；`@Mixin target not found` 是 debug 级
13. 控制台 GBK 崩溃：先写 utf-8 日志再 print
14. NeoForge 的 jar-in-jar 在 `META-INF/jarjar/` 不是 `META-INF/jars/`，扫描两个前缀都认
15. `LoadingModList` 的 issue 无格式化文本（只有 translationKey/args/cause）；正常环境 0 issue，**错误路径未用真实坏 mod 验证**
16. 报告单一写入者：companion 只写原始 json，Python 渲染最终报告 → 可离线重算、可测降级路径
17. 类加载器：MC / companion 在 `TransformingClassLoader`；NeoForge / Mixin / Connector / Fabric 在 `ModuleClassLoader`，跨模块 `Class.forName` 可达
18. `connector.mixins.json` 32 条在 `META-INF/jarjar/org.sinytra.connector-...-mod.jar` 里；运行时生成的只有 `adapter_generated_mixins.jar`（框架层，不进用户 mixin 报告）
19. events v1 实现：`ModList.getAllScanData()` 找 `@SubscribeEvent` → 反射取参数类型 = 事件类；对每个类在 GAME bus 挂计数 spy；反射读 `EventBus.listenerLists`（`LockHelper.getReadMap()` → `ListenerList.getListeners().length`）。注意 `EventBus.listeners` 按监听器对象索引，不是按事件类
20. events v1 覆盖率 42/90（历史值，v2 已废弃）：31 个程序化 `bus.addListener`（`declared_by` 空但 `registered>0`，v2 已补齐，验收 `programmatic=0`，见决策 23）；17 个 MOD bus 被 classChecker 拒绝（设计边界，v2 仍不覆盖）。**不能把 spied=false 全归给 classChecker**
21. events 统计口径：`observed_since` = companion 构造时刻，此前触发的事件计不到；`never_triggered` 只算"已挂 spy 且 registered>0"；验证 gameplay 事件需进存档（`SL_QUICKPLAY` 直进）
22. events 报告分层（2026-11-03）：`events.json` 保持 companion 原始事实（schema 1 = v1，schema 2 = v2/0.4.1），`core/events_report.py` 纯函数渲染 `events_report.json`；状态分类全部由数据推导（`observed` / `never_triggered` / `programmatic` / `non_game_bus`），**不写死 31、17、42 这些数字**。覆盖率分母 = 总数 - 非 GAME bus。v2 契约：per-event `timing{count,total_ns,max_ns}` + GAME bus 全量挂 spy；读不到就降级
23. events v2 实现要点（0.4.1）：
   - 全量挂 spy 用 `listenerLists.getReadMap()` 的 keys，只在 load_complete / periodic 快照前补挂，shutdown 不再动注册表；MOD bus 前缀 `net.neoforged.fml.event.` 继续跳过
   - 每类挂 2 个 listener（HIGHEST 记开始、LOWEST 记结束），`timing` ≈ 其他监听器耗时；注册数输出要扣掉 `SPY_LISTENERS`（1~2），否则 `registered` 会虚高
   - 热路径零分配：每类预建 4 个 `AtomicLong` + `ThreadLocal<long[]>{start,depth}`；嵌套 post 只采最外层，异常/负 delta 丢弃
   - 实测：主菜单 63/63（进存档前注册表只有 63 类），`SL_QUICKPLAY` 进存档后 periodic 补挂 10 类 → 73/73；耗时样本 32 类
24. apis v1 定义（2026-11-03）：
   - FFAPI 模块从 jar 的 `META-INF/jars/*.jar` 读 `META-INF/neoforge.mods.toml`（44 个，id 是下划线形式），与 `runtime.json` 加载集合求交；FFAPI 自己的 `fabric.mod.json` 已改名 `.old`
   - Fabric depends 从 `fabric.mod.json` 读；解析顺序：内置（minecraft / java / fabricloader）→ jar `provides` 别名（FFAPI 的 toml 提供 `fabric`、`fabric-api` 等）→ runtime mod（`-`/`_` 归一化）。`fabricloader` 版本取 FFAPI 内嵌 `forgified-fabric-loader-*.jar` 的 `Implementation-Version`（`2.5.68+0.18.4+1.21.1`）。版本比较支持 `>= <= > < = ~ ^`、空格 AND、`x` 通配；无法判定记 `null`，不猜
   - Connector adapter 计数来自 `.cache/connector/patch_audit.txt`（Connector 在 remap 时自己写）。**mtime 比 runtime.json 早 5 分钟以上就标 `stale`**：Connector 复用缓存时不会重写，文件里可能是已删 mod（钠）的补丁
   - 不判断"API 调用是否成功"，只报元数据和审计文件里的事实
25. classloading v1 定义（2026-11-03）：
   - 运行期：只消费 companion 的 7 个探针（role / class / loader / identity），按 identity 归组为 ClassLoader 实例；layer 由 loader 类名推断（TransformingClassLoader=transforming，ModuleClassLoader=module）。不枚举类、不做字节码归属
   - 静态：扫 `mods/*.jar` + `META-INF/jars|jarjar` 嵌套 jar 的 `.class`，同名即重复。**判据只看结构**：同一类在顶层 jar 出现 >= 2 次才算 `conflict`（进 `reported`）；顶层与嵌套、或嵌套与嵌套之间共存都是 `jar_in_jar`（Fabric 生态常态），记 filtered
   - `relocated`（reloc/shaded/shadow）/ `fabric_loader`（net/fabricmc/loader、net/fabricmc/api）前缀规则保留，但只做 jar-in-jar 的子分类标注（`filtered.by_category`），**不再决定是否冲突**
   - 交叉：`classpath_conflicts` 的候选集是 `duplicates`，条件是类名与 `libraries/` 某类相同**且至少一个顶层出现**（`any(p[1] is None)`）；不按包名过滤（library 命名空间撞名也报）
   - 实测：A 组 9 jar / 6269 类，重复 1147（relocated 585 + fabric_loader 200 + jar_in_jar 362），reported 0；当前 8 jar / 6151 类，重复 1030（jar_in_jar 245，少掉的 117 是顶层 placeholder-api 已移出 mods），conflicts 0
26. mod 索引与多版本：
   - `build_target_index` 按 `(mod_id, version)` 建键（version 来自元数据，占位符时从 jar 文件名回退）。`build_mods` 输出时按归一化 mod_id（`_` ↔ `-`）合并，同一 mod 的 Fabric 连字符版和 FML 下划线版合并成一条，`versions` 列全部版本，`version`/`jar`/`container` 取 FML 侧 primary。`multi_version_mods` 汇总多版本 mod_id。jar 元数据扫描按 `mods/*.jar` 顺序 + runtime 文件顺序，先扫到的 jar/container 保留，types 合并
27. 启动结果与数据新鲜度（2026-11-03 晚）：
   - `cmd_launch` 在 `launcher.launch()` 前后记 `started_at` / `finished_at`，连同 `exit_code` 传给 `write_reports`，落 `launch.json`
   - `runtime_stale(launch, runtime)`：`runtime.json` 缺失或 `runtime.generated_at < launch.started_at` → `true`；无 launch → `None`；否则 `false`。`report` 单独跑（无新 launch）时复用旧 `launch.json`，所以 `stale` 不会自己变 `false`
   - 「启动」段：开始/结束/退出码 + 致命行；`stale=true` 打两行警告，`stale=null` 打「无 launch 记录（只跑过 report）」
   - **退出码不可靠**：crash screen 点「退出游戏」/ 优雅关窗都是 0；判断失败要靠 `stale` + 致命行 + 退出码三者一起看，不能只看 `exit_code`
28. C 组实测结论（2026-11-03 晚，坏 mod 验证错误路径）：
   - dep-test（纯 `fabric.mod.json`，`depends: fabric-screen-api-v1 >=99.0.0`）→ FML **pre-loading 阶段 FATAL**「Some of your mods are incompatible」，生成 crash report，游戏**停在 crash screen 不退出**，`runtime.json` 不更新 → `stale=true`；`apis` 能报 `fabric_dep_missing`（`loaded:false` + 解析到 2.0.26）
   - **副作用**：Connector early remap 因前面的 mod 发现错误整轮跳过，该次运行里**所有** Fabric 顶层 mod（modmenu / appleskin / comforts / trinkets）都被「is a Fabric mod and cannot be loaded」跳过。纯元数据测试 jar 会毒化整轮 Fabric 加载，不能用它测「单个 mod 的 depends」
   - Sodium 0.8.13（`[钠] sodium-fabric-0.8.13+mc1.21.1.jar`）：Connector remap 成功、ModList 里有它，但 `@WrapMethod` 签名不匹配（Mojang 映射 `float[]` vs sodium 预期 `float`）→ `MixinApplyError` → exit 1。summary 抓到 4 条致命行 + Mixins `failed=1`
29. Sodium 与 Connector 的边界（2026-11-03 晚，ROADMAP P0 结论）：
   - Sodium 从 0.8.12 起提供**官方 NeoForge 1.21.1 构建**：`sodium-neoforge-0.8.13+mc1.21.1.jar`（Modrinth `mc1.21.1-0.8.13-neoforge`，1.29 MB，无外部依赖）。实测 22:16:13→22:17:15：ModList 出现 Sodium 0.8.13+mc1.21.1、进入「新的世界」、无 FATAL、无 crash report；`fabric_renderer_indigo` 自动让位（"Different rendering plugin detected"）；events 93 类 / spied 76 / 覆盖 1.0；classloading 11 jar / 7355 类 / 重复 1088 全 jar-in-jar / 冲突 0；apis `ffapi_missing=0`、`depends_total=42`、`unsatisfied=0`（Sodium 的 target 已是 neoforge，不再进 `fabric_depends`）
   - **不为 L3 写逐 mod 兼容层**：Fabric 版 Sodium 的失败层是 Connector 的 mixin 注解重映射（MixinExtras `@WrapMethod` handler 签名 `float[]` vs `float`），属上游核心；且官方已有 NeoForge 构建，写逐 mod 补丁等于重复维护一份移植。**主线判断不以"有没有原生构建"为准**：Fabric 原生 mod（无原生构建）走 Connector，补桥接层缺口；完整判据、90% 目标与 P1–P5 路线见 `ROADMAP.md`
30. 兼容主线与 90% 判据（2026-11-03 晚，用户 m00492 校正）：
   - 目标：**NeoForge 上通过 Connector 跑 Fabric 原生 mod，完美兼容率 ≥90%**，再逐步扩大阵营；
   - "完美"= 进游戏 + 进存档 + 核心功能可用 + 失败时报告说得清（四条合取），"能加载"不算通过；
   - 补丁只打 **Connector/FFAPI 桥接层**：一个补丁覆盖一类调用（缺 API 行为/事件/注册表桥），不按 mod id 特判；
   - 顺序 **L1（API 表面）→ L4（类加载/loader 身份）→ L2 个案 → L3 不做**；
   - 原生构建只是 L3 边界与可选建议，不是"放弃 Connector 支持"的理由；
   - 落地第一步是评测台（样本集 + 单 mod 隔离跑 + 判定器），没有通过率数字之前不谈"修哪个 mod"
   - 副作用：Sodium NeoForge 自带 jar-in-jar 的 FFAPI 模块（api-base 0.4.42 / block-view 1.0.10 / renderer-api 3.4.1 / rendering-data-attachment 0.3.48），与 Forgified 同名模块多版本共存（1.0.10/1.0.11、0.3.48/0.3.49），启动时提示 "version differences that were not resolved"；`multi_version_mods` 7 → 9。暂不处理，列 ROADMAP P3
   - 该次 `exit_code=1` 但日志完整（Stopping / saving 全走完）、无致命行、世界已保存——关窗路径的退出码不可信（决策 27 的又一例）；summary 措辞已改为「非 0；本次数据完整、无致命行，可能是关窗/强杀路径」
31. `@Invoker` 内部类 target 与 access widener（2026-11-05，样本 fallingleaves）：
   - 现象：`failed to access class net.minecraft.client.particle.ParticleEngine$MutableSpriteSet from class randommcsomethin.fallingleaves.mixin.SimpleSpriteProviderInvoker`
   - **不是 Connector 的重映射缺口**：Connector 产出的 mapped jar 里注解与接口签名已是 `ParticleEngine$MutableSpriteSet`（mojang），target 映射正确
   - 真因：target 是 **package-private** 内部类，而 `fabric.mod.json` **没有 `accessWidener` 键**（jar 里有 `fallingleaves.accesswidener`，是死文件）→ Fabric 与 Connector 都不加载 → `IllegalAccessError`
   - 上游 `build.gradle` 有 `loom.accessWidenerPath`，发布 jar 丢键 → 上游打包问题；正确修法是上游 issue，不是本地补丁（补 = 改第三方元数据 + 猜意图）
   - Connector 的 AW 管线正常（`AccessWidenerTransformer` + `reloc/net/fabricmc/classtweaker`），sodium / carpet / language-reload / repurposed_structures / the_bumblezone 声明了 AW 都生效
   - 扫描表：`compat/invoker_inner_target_scan.md`（22 jar / 53 mixin 类 / 64 条内部类 target，20 条 package-private，除 fallingleaves 外全部声明了 AW）；核实全文见 `compat/fallingleaves-investigation.md`
   - "内部类 target" 本身不是失败原因；区分点是 target 可见性 + AW 是否被加载。`suspects.py` 已能把这类行归到 `L2`
   - **最终处置（2026-11-05，用户决定）**：记为「**L2 / 上游缺陷（发布包丢 accessWidener 键）**」，移出、不修、不改 jar；不做 Fabric 对照实验；已从 `compat/corpus.json` 的 `main` 移入 `excluded_upstream_defects`（manual 分母 35 → 34）。该项关闭
32. suspects 的两个观测缺陷（2026-11-05，独立修复）：
   - `build_suspects(..., fatal=...)`：`stale=true` 或只跑 report 时，从 `launch.json` 的 `fatal[]` 补抓致命行（原来只读 `superloader-launch.log`，文件没有本次内容就 `suspects=0`）
   - 新增 Fabric Loader 依赖失败来源：`HARD_DEP_NO_CANDIDATE` / `HARD_DEP` / `Resolution failed` / `Some of your mods are incompatible`，归 `L0`，证据取 `- mod <name> (<id>) ... requires ...`；`LAYERS` 映射写在 `core/suspects.py`
   - 回放（`tools/replay_suspects.py`）：`connectiblechains`（真实 gz 日志，L0）与 `fallingleaves`（只给 fatal 行，L2）、`replaymod`（日志里只有 crash report 头，靠 `at TRANSFORMER/<modid>@` 栈帧归属，L2）均 PASS
33. replaymod 崩溃 = Connector 目标迁移缺口（2026-11-05，样本 replaymod 1.21-2.6.28）：
    - 现象：`Cannot invoke "GuiGraphics.flush()" because "stack" is null`，栈 `VanillaGuiScreen$EventHandler.onGuiRender` ← `PostRenderScreenCallback` ← `GameRenderer.handler$…$replaymod$postRenderScreen` ← `GameRenderer.render`
    - **不是 replaymod 自身 bug**：原注解 `@Inject(method="render", at=@At(INVOKE, target="Lnet/minecraft/client/gui/screen/Screen;renderWithTooltip(DrawContext;IIF)V", shift=AFTER))`；它的 `mixins.jgui.refmap.json` 里有这条的正确映射（`class_437;method_47413`），Fabric 上靠 refmap 正常工作
    - **是 Connector 的错误重定位**：mapped jar 里同一个方法变成 `at=@At(INVOKE, target="Lnet/minecraft/client/DeltaTracker;getGameTimeDeltaTicks()F")` 且 `shift=AFTER` 丢失 → handler 插到 `render()` 开头就执行的调用上，overlay 阶段每帧触发，`GuiGraphics` 还是 null → NPE
    - 根因：NeoForge 21.1 把 `GameRenderer.render` 里的 `Screen;renderWithTooltip` 调用换成了 `ClientHooks.drawScreen(Screen, GuiGraphics, int, int, float)`（javap `neoforge-21.1.265-client.jar` offset 745），原注入点不存在；Connector 没有对应的 mixin patch
    - 簇：扫 165 jar，只有 replaymod 的 `MixinGameRenderer` 注入这个被移走的调用；其余（chatpatches/cloth-config/JEI/Jade/sodium/midnightlib/lenientdeath）只是调用 `GuiGraphics.flush()` 或注入 `Screen` 自己的方法 → **不写特判**
    - 载体：Connector 无注解重写开关（config 只有 version/hiddenMods/globalModAliases/enableMixinSafeguard），companion 只能靠改别人 class 的注解 = 单 mod 硬编码 → 正确做法是给 Connector 提 issue/PR（加一条 patch：`Screen.renderWithTooltip` → `ClientHooks.drawScreen` 调用点，保留 AFTER 语义；或至少解析不出时不要改写成无关 target）
    - 记录：`compat/replaymod-investigation.md`（含 issue 草稿）、`compat/corpus.json.excluded_upstream_defects`
34. malilib 家族（malilib/litematica/tweakeroo/minihud）= 无 refmap + 目标被 NeoForge 改写（2026-11-05）：
    - 四个 jar 的 mixin config **都没有 refmap**（家族约定：直接写 intermediary 名，如 `method_29425`），Connector 的重映射本身是对的
      （mapped jar 里已是 `loadFromJson(...)` + `Lnet/minecraft/locale/Language;`）
    - minihud 的 `MixinLanguage` `@ModifyArgs(method="loadFromJson(InputStream, BiConsumer)", at=INVOKE BiConsumer.accept)`：
      NeoForge 21.1.265 把 2 参 `loadFromJson` 改成「只做 invokedynamic + 转发给 3 参重载」，`accept` 调用点（offset 128）搬进
      `loadFromJson(InputStream, BiConsumer, BiConsumer<Component>)` → 2 参方法体里 0 条匹配 → `InjectionError ... Scanned 0 target(s)`
    - 层级 L2（与 replaymod 同族：NeoForge 改方法体，Connector 无对应 patch）；Connector jar 里没有任何 `Language` 补丁
    - 簇：四个 jar 里只有 minihud 有 `Language` 的 mixin；litematica 的 4 个类只是普通引用
    - 处置：短期移出 minihud，单独验证其余三个；治本需要 Connector 加一条把注入点迁到 3 参重载的 patch（上游 issue/PR）
    - 记录：`compat/minihud-investigation.md`
35. the_bumblezone = Connector adapter 转换期 NPE（2026-11-05，样本 the-bumblezone-fabric 7.17.3+1.21.1）：
    - 现象：启动时 `[Connector] Error transforming file the_bumblezone-...jar`，随后 Sodium 在
      `ConfigManager.registerConfigs` 抛 "Sodium's config could not be found"（掩盖式连带崩溃，不是 Sodium 的问题）
    - 真因：`Failed to execute task .../LivingEntityMixin.class` → `NullPointerException: Cannot invoke
      "TargetPair.methodNode()" because "dirtyTarget" is null` at
      `ResolverSyntheticInstanceof.resolve(ResolverSyntheticInstanceof.java:54)`（adapter，转换 jar 阶段，
      早于任何模组代码）
    - **不是 mod 的 mixin 写错**：`LivingEntityMixin` 全是标准 `@Inject`/`@ModifyReturnValue`/`@ModifyExpressionValue`/
      `@WrapOperation`，没有自定义 plugin、没有 AW
    - **companion/FFAPI 修不了**：该阶段早于 FML 加载模组；Connector 配置无 adapter 开关；1.21.1 上 Connector
      最新就是 beta.17（更新的 3.x 只支持 MC 26.x）
    - 簇：目前只有这一个 mod 触发；与 replaymod/minihud 的 L2「目标迁移」不同，这是 adapter 的健壮性缺口（`dirtyTarget` 未判空）
    - 处置：短期移出 `mods/`；治本给 Sinytra/Connector 提 issue（null 时退回 `ResolutionResult.pass()`）
    - 归因器已修：`suspects` 新增 `scan_transform_errors()`（来源 `mixin_transform_failed`，L2，证据取
      `Failed to execute task` / `Caused by:`），本次已报出 the_bumblezone，并把根因排在连带崩溃（sodium）之前
    - 记录：`compat/bumblezone-investigation.md`（含 issue 草稿）

36. 农夫乐事（refabricated）= NeoForge 改了 `CropBlock.getGrowthSpeed` 的参数类型（2026-11-05）：
    - 现象：`@ModifyVariable` handler 签名校验失败 `Found unexpected argument type Block at index 1, expected BlockState`，required mixin → 启动崩
    - 证据：原 jar handler 是 `(float, Block, BlockGetter, BlockPos)`、注解 `method_9830`；mapped jar 里 Connector 已正确翻成 `getGrowthSpeed`（不是 remap 缺口）；vanilla 的 `CropBlock.getGrowthSpeed` 是 `(Block, BlockGetter, BlockPos)`，NeoForge 打补丁后变成 `(BlockState, BlockGetter, BlockPos)`
    - 结论：L2 参数类型替换；Connector 的 adapter 只处理参数增删/重排，不处理类型替换；companion 修不了（要改第三方 handler 字节码）
    - 处置：换官方 NeoForge 版 `FarmersDelight-1.21.1-1.3.4.jar`（实例已换，可正常加载）；若仍需要 refabricated，只能等 Connector 上游
37. friends-and-foes = Fabric 枚举 mixin 与 NeoForge 枚举扩展冲突（2026-11-05，样本 friendsandfoes-fabric-5.0.4+mc1.21.1）：
    - 现象：`MixinPreProcessorException: Attach error for …AddCustomSpawnGroupMixin … [Attach method -> <init>(Ljava/lang/String;ILjava/lang/String;IZZI)V]` → `NullPointerException … ClassInfo$Method.isUnique() because "method" is null`
    - 证据：该 mixin 是枚举 mixin，`@Mixin(MobCategory)` 加两个常量，`<clinit>` 调 7 参构造器；`MobCategory` 的 7 参构造器是 NeoForge 的**保留构造器**（`@ReservedConstructor`，由 `RuntimeEnumExtender` 消费/移除），所以 attach 时目标类里查不到 → Mixin NPE；Connector 对 `class_1311` 的映射正确
    - 结论：L2 结构性冲突（不是 mod 写错、不是 refmap 缺口）；Modrinth 上该 mod **没有 NeoForge 构建**，无处可换
    - 处置：移出 mods/（jar 已删除，可从 Modrinth `friendsandfoes-fabric-5.0.4+mc1.21.1.jar` 重新下载）；治本需要 Connector 把枚举 mixin 转成 `IExtensibleEnum` 扩展，issue 草稿在 `compat/friendsandfoes-investigation.md`
    - 顺带：Mixin 在目标方法缺失时抛 NPE 而不是 "method not found"，体验问题，可在 issue 里附带

38. bclib 去皮在 NeoForge 上是"注入点被抽空"，companion 用事件桥修复（2026-11-05，样本 betterend 21.0.11 / betternether 21.0.11 + bclib 21.0.13）：
    - 现象：能进世界，但斧头对 betterend/betternether 的方块不去皮，也不报错（用户描述"可能 mixin 失效了"）
    - 证据：bclib `AxeItemMixin` 注入 `AxeItem.getStripped`（refmap 正常、mixin 已应用）；NeoForge 21.1.265 的 `AxeItem.useOn` → `evaluateNewBlockState` → `BlockState.getToolModifiedState(..., ItemAbility, Z)`，`getStripped` 已是 private 且无调用者；新路径走数据映射 `NeoForgeDataMaps.STRIPPABLES`
    - 修复：companion 0.6.0 的 `AxeStripBridge` 监听 `BlockToolModificationEvent`（AXE_STRIP）→ 对方块调用 bclib `AxeCanStrip#strippedState` → `setFinalState`（补丁台账第 2 条）
    - 为什么不是单 mod 特判：按 bclib 接口匹配，不认 mod id / jar 名；任何 betterx 系模组都覆盖
39. language-reload 崩溃 = Connector 的 Language 补丁打破 mod 的构造顺序假设（2026-11-05）：
    - 现象：创造物品栏/JEI 输入搜索时 `Cannot invoke "java.util.Map.get(Object)" because "this.separateTranslations" is null`（`ClientLanguage.languagereload_get:554`）
    - 机制：`onLoad` 在 `ClientLanguage.loadFrom` HEAD 填静态表，`Language.<init>` TAIL 消费并置空，假设"一次加载只构造一个实例"；Connector 把 `loadFromJson` 2 参调用改写成 3 参后顺序变化，第二个实例拿到 null，`languagereload_get` 无 null 兜底
    - 判定：L2，不是 mod bug、不是 refmap 缺口；companion 修不了（要改别人字段消费逻辑）
    - 处置：用户已禁用该 mod；记录在 `compat/languagereload-investigation.md` 与 `corpus.json.excluded_upstream_defects`；main 移除（manual 分母 33 → 32）

## 环境事实

Windows 11（10.0.26200），Python 3.13.2，Java 25.0.4.1。

- `maven.neoforged.net` 不可达，大陆访问被墙；`neoforged.forgecdn.net` / `libraries.minecraft.net` / `piston-meta.mojang.com` / `resources.download.minecraft.net` / Modrinth API 可达
- Gradle 9.2.1；`javap` 在 `C:\Program Files\Java\jdk-25.0.4.1\bin\javap.exe`
- Gradle 构建 companion 用 JDK 21（`C:\Program Files\Java\jdk-21`，`JAVA_HOME` 指过去）；依赖已缓存，离线构建加 `--offline` 可过；运行游戏仍是 PATH 里的 Java 25
- **DSH 沙箱**：`workspace-write` 下 pwsh 启动即 `0xC0000142`；须 `danger-full-access` + 工作目录 `D:\SuperLoader`

## 已知限制

- 离线登录写死；仅 Windows x64；版本硬编码（`core/paths.py` + companion `gradle.properties` 同步）
- 无 `set-root`；assets 无镜像 fallback
- 报告在游戏退出后才渲染；停在 crash screen 时不会出报告（必须关窗/杀进程，`taskkill /PID <pid>` 不带 `/F` 是优雅关窗）
- 退出码不可信：crash screen 关窗、`taskkill /PID` 关窗都可能给 0 或 1（2026-11-03 22:16 那次原生 Sodium 正常进世界、日志完整到 saving，仍 `exit_code=1`）。summary 对「非 0 但 stale=false 且无致命行」只提示可能是关窗路径，不当成崩溃
- `mods` 错误路径已用 dep-test 验证（决策 28）：`apis` 能报 depends 不满足，但 FML 的 `LoadingModList` issue 仍无格式化文本；纯元数据测试 jar 会毒化 Connector remap，测单个 mod 失败要另想办法
- companion 需手动构建 + 手动复制进 `mods/`；目前只有审计采集，无实际 API 补丁
- events 只覆盖 GAME bus；17 个只在 MOD bus / classChecker 的类保持 unspied（设计边界）。`observed_since` 前触发的事件会被误记 never_triggered
- 耗时是**近似值**：HIGHEST/LOWEST 两个探针之间的间隔，不含与探针同优先级的监听器；同一线程嵌套 post 只采最外层；探针本身有每次几十 ns 开销（静态数据看 `timing.count` 与 `posts` 是否一致）
- 升级 companion 版本后旧存档会提示 "mods have version differences that were not resolved"（NeoForge 把 mod 版本记在 level.dat），属正常现象，进一次存档即更新
- apis v1 只覆盖三个事实（FFAPI 模块加载 / Fabric depends / adapter 审计），不判断调用是否成功，也没有 API 版本语义
- adapter 审计可能过期：Connector 复用 `.cache/connector/` 时不重写 `patch_audit.txt`，`apis.json` 会标 `stale`，数字仅供参考（当前就处于这种情况）
- fabricloader 版本用内嵌 loader 的 manifest 字符串（fork 2.5.68 + 上游 0.18.4），版本范围比较只取首段数字，不拆 fork/上游
- classloading 静态扫描只看 `mods/`（含嵌套）与 `libraries/`，不扫 `.cache/connector/` 的 remap 产物
- classloading 的 `reported` **只含顶层 jar 撞类**；jar-in-jar 共存（同一类在顶层与嵌套、或嵌套之间）归 `jar_in_jar`，不报——这是 Fabric 生态常态，不是异常
- classloading 的 `classpath_conflicts` 用 `duplicates` + `any(顶层出现)`：单次出现的非重复类不报；纯嵌套的重复类不报；「顶层 + 嵌套」混合的重复类会报
- `library_classes` 不含 `libraries/` 里嵌套 jar 的类（当前 131 个 jar 中 2 个有嵌套，共 513 个类），这些类与 mods 撞名检测不到
- `classpath_conflicts` 不再按包名过滤，`org/slf4j` 这类 library 命名空间撞名也会报
- 评测台的“进存档”仍是**日志启发式**（强证据 `Time elapsed: <n> ms` / `Saving chunks for level`），companion 的 `world_joined` 事件落地后才降级为交叉校验；宁可误判 fail，不误判 pass
- `sample_loaded` 靠「jar 原名 / 去 `_mapped` 前缀 / jar 内 mod id+provides」三路匹配 ModList；Connector 会重命名 jar，mod_id 也常与 slug 不同（`stackdeobf` → `stackdeobfuscator`），只按 slug 匹配会误判
- 评测台跑前会用 `logs/compat/fml.toml.good` 还原 `config/fml.toml`：早期强杀可能留下半截配置，导致下一轮在 `DisplayWindow.setupMinecraftWindow` NPE（与样本无关）
- classloading 运行期只有 companion 的 7 个代表类探针，不枚举全部类，也回答不了"某个 mod 的类由哪个 loader 加载"
- 多版本共存是 Fabric 生态常态：jar-in-jar 让同名模块多版本共存（Mod Menu 内嵌 FFAPI 旧版 + Forgified 新版），Connector 不去重（FML 和 Fabric 的 ModList 是两套注册路径）。`mods.json` 能报出多版本共存，但不判断运行时实际加载哪个版本（classloading 不做字节码归属）
- FML 的 `neoforge.mods.toml` 里 version 常是 `${file.jarVersion}` 占位符（Forgified 全系列、Jade、Connector 都是），`_jar_meta` 过滤占位符记 None，由 `_version_from_jar_name` 从 jar 文件名解析版本（`-(\d+\.\d+\.\d+[^/]*?)\.jar$`）
- `mods.json` 的 `version` 取 FML 侧 primary 的版本，`versions` 列出全部。如果消费方要“实际加载的版本”，需要看 `jar` 字段指向哪个文件，不能只看 `version`

## 下一步

A/B 组、C 组、Sodium 实测都已完成，验收数字见「当前状态」与决策 22–29，不要重做。

### C 组结论（2026-11-03 晚，已完成）

- 做法：构造纯 `fabric.mod.json` 测试 jar（`superloader_dep_test-1.0.0.jar`，`depends: fabric-screen-api-v1 >=99.0.0`），生成脚本在 `logs/dep-test/make_jar.py`
- 结果：FML pre-loading 阶段直接 FATAL「Some of your mods are incompatible」，写 crash report，游戏停在 crash screen **不退出**（关窗后 `exit_code=0`）；`runtime.json` 不更新 → `stale=true`
- `apis.json` 现在能报：`fabric_dep_missing` + `satisfied:false` + `loaded:false`（修复点：顶层 jar 未加载也查 depends，见决策 28）
- 副作用：该测试 jar 让 Connector early remap 整轮跳过，所有 Fabric mod 都被「is a Fabric mod and cannot be loaded」——这不是 depends 语义，是测试方法本身的问题
- 测完已删测试 jar；Sodium 已换官方 NeoForge 构建（决策 29），`mods/` 里现在是 `sodium-neoforge-0.8.13+mc1.21.1.jar`，Fabric 版备份在 `logs/tmp-mods-backup/`

### 后续方向

路线与判据见 `ROADMAP.md`（2026-11-03 修订）：主线是 Connector 跑 Fabric 原生 mod、目标 ≥90% 完美兼容；L0–L4 失败分层；补丁打桥接层、一个补丁覆盖一类调用；顺序 L1 → L4 → L2 个案 → L3 不做。

### 2026-11-05 收工时的状态（已交付，别重做）

- companion **0.6.3**，两个补丁都在实例里：①refmap 缺失修复（0.5.2 起，每映射三态校验）②bclib 去皮桥（0.6.3 实测生效）
- 实例 **65 jar**；内容组已进 betterend / betternether / 农夫乐事（NeoForge 官方版）/ friends-and-foes（NeoForge 构建）/ repurposed-structures 未试
- 已移出并记录：`replaymod`(L2 Connector 目标迁移)、`minihud`(L2 NeoForge 改写)、`the-bumblezone-fabric`(L2 adapter NPE)、
  `language-reload`(L2 构造顺序，用户已禁用)、`fallingleaves`(上游丢 AW 键)；jar 在 `D:\SuperLoader\logs\removed-mods\`
- 六个 L2 案例的取证文档都在 `compat/*-investigation.md`；英文 issue 草稿已按官方模板拆好（`compat/issues/`，一模组一份，提交前只需补 Logs 的粘贴链接）

候选下一步（按性价比排序，任选或停测）：

- **A. 重建基线 + 一次回归**：✅ 已完成（2026-11-06）——`compat/baseline-66jar.json`，
  启动 `exit 0 / fatal 0 / suspects 0 / stale false`，去皮桥在整包里无副作用
- **B. 内容组收尾**：装 `repurposed-structures-fabric`（依赖 midnightlib）试一次；这是 content_phase2 里唯一没试的
- **C. Connector issue 合集**：⚠ **草稿封存、不提交**（2026-11-06）——上游明示 1.21.1 不再接收兼容修复
  （“As our LTS support target, 1.21.1 will no longer receive new compatibility fixes. Please upgrade to the latest version for mod
  compatibility support.”），提交这 6 个 issue 只会得到 “won't fix for 1.21.1”。草稿保留在 `compat/issues/`（一模组一份英文、
  自洽可读、Logs 留 `<link>` 占位、待传文件在 `compat/issues/uploads/`），用途改为**已知 L2 档案 + 将来若升级到 26.x 的对照样本**；
  `compat/connector-issues.md` 保留为中文取证附录。结论：1.21.1 上能改变的只有我们自己能改的层（companion / FFAPI / 配置），
  上游修复按“不会来”处理
- **D. 停测**：当前 65 jar 已经能进世界、能徒手验功能点；把 `compat/corpus_v2.md` 与报告当作交付物

1. **P1 兼容评测台**（先有尺子）：样本集 v5 已定稿并跑完首轮 —— `compat/corpus.json`：主样本 44（auto 9 / manual 35）+ 负例 1（carpet，expected L2，实测 fail L2）+ 假设被推翻 1（mixintrace）+ 移植类 2 + 基础设施 7 + 内容组 6；jar 级负例控制 2 个（`logs/dep-test/` L0、`logs/tmp-mods-backup/` 的 Fabric Sodium L2）。每个 jar 带 `version_id` + `sha1`，闭包 61/61，口径见 `compat/corpus_v2.md`（v5）。`tools/compat_sweep.py` 判 `fatal_in_log > crash_screen > timeout_no_runtime > sample_not_loaded > no_world_join > pass`，隔离 = 实例 `mods/` 与 `mods.compat/<slug>/` 交换（`SL_MODS_DIR` 只影响 Python 侧报告，**不能**靠它隔离游戏），`--restore-mods` 善后。首轮 auto **9/9 pass**（`logs/compat/20261104-124552/`），全部 sample_loaded=true。缺 companion `world_joined` 事件（当前靠日志启发式：`Time elapsed: <n> ms` / `Saving chunks for level`）。下一步：manual 35 人工核（先挑 5–10 个明显功能点，如 modmenu 能开、zoomify 滚轮缩放）
2. **P2 归因器**（1 人日）：失败按 L0–L4 归类 + 证据（`NoSuchMethodError` 的 owner/name/desc、mixin 目标与异常、缺哪个 FFAPI 模块/类）；`mods.json` 每条 `verdict` + `layer` + `evidence`，`summary` 顶部「兼容结论」按层聚合。样本来源：carpet 的 crash report 已点名 3 个 failing mixin（`PistonStructureResolver_customStickyMixin` 两个方法 + `Level_fillUpdatesMixin#updateNeighborsMaybe`）——先拿它当 L2 归因的验收样例。
   **进度（2026-11-05）**：`core/suspects.py` 已上线（七来源 + `LAYERS` + `fatal[]` 兜底 + Fabric Loader 依赖失败来源 + 崩溃栈帧归属 `crash_frame`），输出 `suspects.json` 与 summary「可疑模组」段；回放 `connectiblechains`(L0)/`fallingleaves`(L2)/`replaymod`(L2) 全部通过。剩余：把层与证据并进 `mods.json`/summary 顶部的「兼容结论」聚合，并把 `suspects` 从"本次启动"扩到"整包历史"。
   **replaymod（2026-11-05）**：崩溃已定位为 Connector 的目标迁移缺口（NeoForge 用 `ClientHooks.drawScreen` 替换了 `Screen.renderWithTooltip`，Connector 把 `@At` 重写成无关的 `getGameTimeDeltaTicks` 且丢掉 `shift=AFTER`），不是 mod bug、也不是 refmap 缺口；簇只有它一个，**不在 companion 写特判**，按 Connector 上游 issue/PR 处理，详见决策 33 与 `compat/replaymod-investigation.md`
   **已关闭线索（不要重做）**：fallingleaves 的 `@Invoker` 内部类访问失败不是 Connector 重映射缺口（mapped jar 证明 target 映射正确），真因是发布包丢 `accessWidener` 键 + target 为 package-private；扫描表 `compat/invoker_inner_target_scan.md`，核实 `compat/fallingleaves-investigation.md`，决策 31。**处置：移出、不修、不改 jar，记录为 L2/上游缺陷，Fabric 对照不做，已关闭**
3. **P3 L1 桥接补丁**（按失败簇，每簇 ≤1 人日，主战场）：同一缺失 API 类/方法/事件归为一簇，在 companion 里加桥（或 FFAPI 模块/配置修复）；每簇验收 = 该簇样本 fail→pass 且全 corpus 无回归
4. **P4 L4 类加载**（0.5–1 人日）：jar-in-jar 同名模块多版本去重/择一（Sodium 自带 FFAPI 模块是现成样本）、Loader 身份与同名类冲突归因
5. **P5 L2 个案**（按需）：只做简单签名/目标改名；复杂的不做，记录 + 推荐原生
6. 其他 backlog（不阻塞主线）：换一种方式测「单个 mod 加载失败」（研究 `ConnectorEarlyLoader` 的错误处理）、多 loader、Go 重写外壳、companion 侧 mixin target 失效检测
7. **不做**：Sodium / Iris / Indium / c2me 等渲染或内核重写的兼容层——见「被否决的路线」与 ROADMAP §5 P6

## 项目原则

- 消灭变量：路径由启动器定、玩家选 root、从 root 常量拼接，不扫本机已有文件
- 可维护性优先：补丁打在接口层（companion / 配置 / 元数据），不改字节码、不 fork、不合基底
- 不猜：写代码前先读实际数据（JSON 结构、API 返回、磁盘内容）
- 合规：不打包 MC 本体和第三方 mod，运行时从官方源下载；NeoForge installer 可镜像，MC 本体不行
- MIT：抄 HMCL/Prism/PCL2 思路不复制代码

## 交接要点

- 路线看 `ROADMAP.md`：主线是 Connector 跑 Fabric 原生 mod、目标 ≥90% 完美兼容；按 L0–L4 分层，补丁只打 Connector/FFAPI 桥接层（一类调用一个补丁），顺序 L1 → L4 → L2 个案 → L3 不做；**不要因为"有原生构建"就放弃某个非 L3 mod 的 Connector 支持**
- 回归对照基线见 `compat/baseline.json`（24 jar）、`compat/baseline-30jar.json`（30 jar）、`compat/baseline-36jar-v2.json`（36 jar）、`compat/baseline-44jar.json`（44 jar）与 `compat/baseline-57jar.json`（57 jar）和 **`compat/baseline-66jar.json`（66 jar，2026-11-06 12:03 启动，当前基线）**；每次换包新增一份，通过集合不许比上一份小。生成工具 `tools/make_baseline.py`（自动带 `sha1`、版本、上次启动 verdict、`covers_current_mods`；`manual_checks` 从 `--manual` 传入）。当前手动验收 **31/33 pass**（分母 = main 里 `verdict_mode=manual` 且未被移出的样本），记录在 `compat/baseline-57jar.json` 与 `compat/corpus.json.manual_results`；待确认只剩 `modmenu`、`zoomify`
- 人工组进度（2026-11-05）：主样本只剩 `modmenu`、`zoomify` 未明确记录（两个都在跑，等用户确认后补 pass）；
  - 已完成 2026-11-05 第二批（8 个，全 pass）：`presence-footsteps`、`optigui`、`stendhal`、`custom-splash-screen`、`hold-my-items`、`universal-graves`、`lenient-death`、`totemcounter`
  - 已完成 malilib 家族（3 个 pass）：`malilib`、`litematica`、`tweakeroo`；`minihud` 因 L2 上游缺口移出
  - 新增样本 `itemscroller`（0.24.60，同作者、Fabric-only，pass）
  - 已移出：`replaymod`（Connector 目标迁移，决策 33）、`minihud`（NeoForge 改写 `Language.loadFromJson`，决策 34）、`fallingleaves`（上游丢 AW 键）
  - 内容组（`content_phase2`）2026-11-05 晚状态：`betterend` / `betternether` 已进实例（斧头去皮由 companion 0.6.3 桥修好，
  实测 `lacugrove_log -> lacugrove_stripped_log`、`nether_sakura_log -> nether_sakura_stripped_log`）；`farmers-delight-refabricated`
  换成官方 NeoForge `1.21.1-1.3.4`；`the-bumblezone-fabric` 移出（决策 35）；只剩 `repurposed-structures-fabric`（+midnightlib）没试。
  infra 5 个纯库由依赖闭包带进来，不作为人工项
- mixins / environment / mods / summary / events v2（采集 + 渲染）/ apis v1 / classloading v1 已完成，**不要重做**
- 启动结果看 `launch.json` + `summary.txt` 的「启动」段：`stale=true` 时下面的模组/事件/APIs/类加载器数字都是上一次运行的快照，别当本次结果读
- 判失败不能只看 `exit_code`：crash screen 关窗/点退出都是 0；要结合 `stale` 与 `fatal` 行
- companion 版本号：小改动只动第三位，别按功能跳大版本；改版本后记得同步 `gradle.properties` 与 `SuperLoaderCompanion.VERSION`
  （当前 **0.6.3**：refmap 修复 + bclib 去皮桥；构建 `cd D:\IDEA_mods\nfprobe; .\gradlew.bat build --offline`，
  产物 `build/libs/superloader_companion-0.6.3.jar` 复制进实例 `mods/` 并删旧版，实例 65 jar）
- events 报告改渲染逻辑：只动 `core/events_report.py`，跑 `python superloader.py report` 即可离线验证；改 companion 采集前先读本文件「下一步」里的 v2 契约
- apis 报告：只动 `core/apis.py`；输入是 jar 元数据 + `runtime.json` + `.cache/connector/patch_audit.txt`，全离线可重算
- classloading 报告：只动 `core/classloading.py`；输入是 `runtime.json` 探针 + `mods/` jar + `libraries/` 类名，全离线可重算
- **不要再试**：`Mixins.getConfigs()`、mixin 计数 `net.neoforged.bus.*`、`-javaagent` 审计、mixin 扫描求交防幽灵
- 报告可离线重算：改 `core/report.py` / `core/events_report.py` 后跑 `python superloader.py report`
- 新板块沿用数据链：companion 写原始 json → Python 渲染最终报告
- 按目录扫 jar 必须与 `runtime.json` 实际加载集合求交（**仅限扫 `.cache/connector/` 的路径**）
- 消费 `events.json` / `events_report.json` / `apis.json` / `classloading.json` / `mixins.json` / `suspects.json` 前先读「JSON 结构陷阱」节
- `logs/` 只放运行时证据：评测台运行用 `python tools/clean_logs.py --keep 3` 清理（旧的打包进 `logs/archive/`）；一次性脚本放 `tools/archive/`，不要再往 `logs/` 里丢 `.py`
