# SuperLoader 路线：把 Connector 的 Fabric 兼容率做到 90%（2026-11-03 修订）

更新时间：2026-11-03 22:40
关联：[HANDOFF.md](HANDOFF.md)（事实与实现细节在那边，这里只讲目标、判据与顺序）

> 修订说明：初版把"推荐原生构建"当成 ROI 最高的主线，方向错了。本版按正确目标重写：
> **主线是 Connector 跑 Fabric 原生 mod，目标 ≥90% 完美兼容；原生构建只是 L3 边界的特例。**

## 0. 一句话

**验收目标是玩家的整包**：把喜欢的 mod 全塞进 `mods/`，能连续玩、不崩、崩了知道为什么。
[NEEDS.md](NEEDS.md) 是 North Star——任何功能回答不了那里的问题就不做。

兼容率是修好之后的副产品，不是产品：每涨一个点都应来自 Connector/FFAPI/companion 桥接层的一个可复用补丁，
而不是某个 mod 的特判。隔离测试只在整包失败且报告不足时用于事后二分，不是验收方式。

Sodium 这类案例的结论不变（渲染重写、有原生构建、建议换原生），但它**是边界，不是路线**；
不能用它推出"有原生版就放弃 Connector"——那会把主线砍掉。

## 1. 目标与判据

### 1.1 什么叫"完美兼容"（四条的合取）

1. **能进游戏**：启动到主菜单，无 `FATAL`、无 crash report（`fatal_lines()` 为空）；
2. **能进存档**：quickPlay 进入"新的世界"并稳定运行（无 tick 崩溃、无致命异常）；
3. **核心功能可用**：不是"能加载但功能缺失"——每类 mod 有抽查项（例：zoomify 缩放、fallingleaves 落叶粒子、
   debugify 的修复项生效）；抽查项按 mod 类型写进样本清单，人工/脚本各半；
4. **失败时报告能说清为什么**：失败条目带层（L0–L4）+ 证据（缺哪个 API / 哪个 mixin 目标 / 哪个类），
   而不是只有一句 FATAL。

四条缺一不算通过；1、2 可自动化，3 用抽查，4 是失败的验收条件。

### 1.2 样本集（分母）

- **主样本集 = Fabric 原生 mod**：1.21.1、只有 Fabric 构建、无 NeoForge 构建、按下载量排序的头部；
  排除 API/运行时库（fabric-api、fabric-language-kotlin、placeholder-api、malilib 这类），但库作为依赖随样本装入。
- 规模目标 **≥40 个**（每个失败占 ≤2.5%，90% 判据才有分辨率）。实测（2026-11-03，Modrinth 前 300 个 Fabric mod，
  数据在 `logs/compat_corpus_300.json`）：**55 个 Fabric-only、245 个 both**。扣掉 API/运行时库（fabric-api、
  fabric-language-kotlin、placeholder-api、malilib、cicada、cardinal-components-api、bclib、ukulib、yosbr…）
  和明显 L3 边界（indium、c2me、ebe、animatica、skyboxify、flashback、threadtweak…）后剩 **29 个候选**
  （`compat/corpus_draft.json`），不足 40；正在把探测扩到前 600 补足（`logs/probe_corpus600.py`，
  结果写 `logs/compat_corpus_600.json`）。
- **副样本集 = 同时有 Fabric/NeoForge 构建的 mod 的 Fabric 版**（前 100 里 83 个）：不进 90% 主指标，
  但用来观察"Connector 对主流 mod 的 Fabric 版"行为，修 L1/L4 时也要跑回归。
- 每轮结果落 `logs/compat/YYYYMMDD-HHMM/compat.json` + `compat.md`（逐 mod 一行：verdict / layer / evidence / 耗时）。

### 1.3 通过率

- 主指标：`pass / 主样本数`，目标 **≥90%**；
- 辅助：下载量加权通过率（防止只修冷门 mod）、头部 10 个样本必须 100%；
- 每次桥接补丁提交前对比："本次通过的集合"不得比"上次通过的集合"小（回归护栏，见 §6）。

## 2. 失败层模型

| 层 | 内容 | 现有观测 | 处置 |
| --- | --- | --- | --- |
| L0 元数据/依赖解析 | `fabric.mod.json` depends、loader 版本、MC 版本 | `apis.json` / `mods.json` | 报告说清；用户侧可修（装依赖/换版本） |
| L1 API 表面 | FFAPI 模块缺失、模块版本不够、Fabric API 类/方法在 NeoForge 侧不存在 | `apis.json` ffapi_missing / depends；`NoSuchMethodError`/`NoClassDefFoundError` 归因（待做） | **主战场，可补**（companion shim / FFAPI 模块补全） |
| L2 mixin 重映射 | 注解重映射、`@WrapMethod` 签名、注入点、access widener | `mixins.json` failed | **个案**：简单签名/目标改名可补，复杂的不补 |
| L3 渲染/内核重写 | Sodium / Iris / Indium / c2me 类直接改渲染或线程模型 | 观测得到 | **不做**；推荐原生构建 + 记录 + 上报 |
| L4 类加载/loader 身份 | ClassLoader 分层、同名类、jar-in-jar 去重、mod id 冲突 | `classloading.json`（当前 11 jar / 7355 类 / 1088 重复 / 冲突 0） | **第二战场，可补** |

顺序：**L1 → L4 → L2 个案 → L3 不做**。L1 覆盖最大面（绝大多数"NoClassDefFound/NoSuchMethod"），
L4 影响"能不能起来"，L2 只在个案上做，L3 明确划界。

## 3. 补丁哲学：补桥接层，不补单个 mod

- 一个补丁必须覆盖**一类调用**：例如"Fabric `ScreenEvents.AFTER_INIT` 在 NeoForge 侧没有触发点" →
  在 companion 里补一个事件桥，而不是给 zoomify 写特判。
- 补丁载体优先级：
  1. **companion mod**（我们自己的 NeoForge 侧 mod，`companion/`）：注册缺失的 API 行为、事件、注册表桥；
  2. **FFAPI 模块补全/升级**（配置层，不改 jar）；
  3. **Connector 配置/兼容开关**（能用配置解决的，不改代码）；
  4. 仅在确认是 Connector 缺陷且无法绕开时，才考虑给 Connector 提 issue/PR——**不 fork、不内嵌改过的 Connector**。
- 禁止：改第三方 jar 字节码、按 mod id 写开关、给单个 mod 的 mixin 注入点打补丁（那等价于维护该 mod 的移植）。
- 每个补丁必须能回答三问：**覆盖哪类调用？证据是哪几条 corpus 失败？修完哪几个样本从 fail 变 pass？**

## 4. 现状基线（2026-11-03 22:17，原生 Sodium 那次）

- 实例 `D:\SLData\instances\1.21.1`：11 个 jar（不含 Sodium Fabric；Sodium 原生 `sodium-neoforge-0.8.13+mc1.21.1.jar` 已装入），
  报告 `mods=67 issues=0 mixins=429 events=93 apis_issues=1 cls_issues=0 stale=False`。
- 已验证可用的 Fabric 原生 mod：**modmenu、comforts、appleskin、trinkets**（基础实例里一直在跑）。
- FFAPI：44/44 模块在位，`ffapi_missing=0`、`depends_total=42`、`unsatisfied=0`；
  Sodium 原生版自带 jar-in-jar 的 FFAPI 模块造成 2 处多版本共存（已知副作用，见 HANDOFF 决策 29）。
- 类加载：11 jar / 7355 类 / 1088 个重复 FQCN（Connector 的 FFAPI 与 Forgified 同名模块）/ 顶层冲突 0。
- **当前通过率未知**——没有样本集、没有逐 mod 判定，这是 P1 要补的第一块。
- 已知 L2 失败案例：Fabric 版 Sodium（`@WrapMethod` 签名 `float[]` vs `float`），归 L2/L3 边界，不做。

## 5. 路线图

### P0（✅ 已完成）报告可信化 + Sodium 边界结论
- `launch.json`（启动记录）、`stale` 判定、致命行提取、`mod_not_loaded` issue、apis 对未加载 mod 的 depends 检查；
- Sodium：Fabric 版 L2/L3 崩溃已能说清；原生 NeoForge 版实测通过；结论落 HANDOFF 决策 27–29。

### P1（1–1.5 人日）兼容评测台（先有尺子）
1. **样本清单**：扩到 Modrinth 前 300–500 个 Fabric mod，筛 Fabric-only、去 API/库，人工确认 40+ 个，
   写 `compat/corpus.json`（slug、版本、下载量、依赖、抽查项、是否 L3 边界）。
2. **单 mod 隔离跑**：脚本 `tools/compat_sweep.py`：备份 `mods/` → 放入"基础前置集 + 1 个候选" → `superloader.py launch`
   （quickPlay 进世界）→ 收 `summary/mixins/apis/classloading/launch.json` → 判定 verdict → 恢复 `mods/`。
   必须单 mod/小批，因为坏 jar 会毒化 Connector early remap（dep-test 实测：一个纯元数据 jar 让所有 Fabric mod 被跳过）。
3. **进档信号**：companion 增加 `world_joined` 事件（`ClientPlayerNetworkEvent.LoggingIn` 或等价），写进 events，
   让"能进存档"从人眼看日志变成可判定；同时记首次 tick 后 20s 无异常。
4. **判定器**：`pass` = 无 fatal + 有 world_joined + 无 crash report；`fail` 带层与证据（见 P2）；输出 `compat.json` / `compat.md`。
5. 验收：40 个样本全量跑完（约 1.5–2 小时机器时间），产出当前通过率与失败分布——**这就是 90% 的起点数字**。

### P2（1 人日）归因器（把失败翻译成"缺什么"）
- 从 `superloader-launch.log` + `mixins_logged.json` + classloading 抽证据，归类到 L0–L4：
  - `NoSuchMethodError` / `NoSuchFieldError` → owner/name/desc，映射到"哪个 Fabric API 类/方法"→ L1；
  - `NoClassDefFoundError` / `ClassNotFoundException` → 类名 → L1（API 缺类）或 L4（类加载隔离）；
  - mixin `InvalidInjectionException` / `MixinApplyError` → 配置、目标类、目标方法、异常原因 → L2；
  - `DuplicateModsFoundException` / 同名类冲突 → L4。
- `mods.json` 每条加 `verdict ∈ {pass, fail}` + `layer` + `evidence[]`；`summary.txt` 顶部「兼容结论」：`N 通过 / M 失败`，
  失败按层聚合（"L1：3 个，缺 `fabric-screen-api-v1` 的 X 方法"）。
- 验收：拿 P1 的 40 个样本结果回放，每个失败都有层与证据，没有"未知"。

### P3（L1 桥接补丁，按失败簇逐个，每簇 ≤1 人日）主战场
- 从 P2 结果里聚类：**同一 API 类/方法/事件缺失**的归为一簇；每簇一个 companion 补丁（或 FFAPI 配置修复）。
- 典型候选（待 P2 证实，不预设）：Screen/UI 事件、`ClientTickEvents` 类、注册表扩展点、`ItemGroup` 显示、
  `RenderLayer` 相关（注意：跟 L3 渲染管线区分，只是 API 层调用）、网络 payload 编解码。
- 每簇补丁验收：该簇样本从 fail→pass，且全 corpus 无回归；补丁默认开启、有开关可回滚。

### P4（L4 类加载修复，0.5–1 人日）
- 已观测 1088 个重复 FQCN（FFAPI 与 Forgified 同名模块），当前"顶层冲突 0"但需验证是否真无影响；
- jar-in-jar 去重策略：同名模块按版本择一（Sodium 原生版的多版本共存是现成样本）；同名类但不同实现 → 隔离或上报；
- 验收：`classloading.json` 的 conflicts 归因清楚，corpus 里因类加载失败的样本转 pass。

### P5（L2 个案，按需）
- 只做"简单签名/目标改名"：mixin 目标方法改名但描述符兼容、`@Inject` at 常量变化、`@Redirect` 目标未变；
- 复杂的不做（跨版本大改、`@WrapMethod` 参数类型变化、渲染管线注入）→ 记录 + 推荐原生构建。

### P6（不做）
- Sodium / Iris / Indium / c2me 等渲染或内核重写的兼容层；
- 改第三方 jar、fork Connector、改 MC 本体。

## 6. 护栏（每个补丁的 Definition of Done）

1. **回归**：全 corpus 重跑，通过集合 ⊇ 上次通过集合（新增 pass 可以，丢 pass 必须解释）；
2. **证据**：补丁描述里贴"修前/修后"的 compat.json 差异与失败样本名单；
3. **可回滚**：补丁有配置开关；关掉后行为回到修前；
4. **不特判**：代码里不出现 mod id / jar 名分支（白名单只允许"库 mod 版本兼容"这类通用规则）；
5. **可解释**：报告对修复后的行为有对应说明（不是"悄悄能跑了"）。

## 7. 反模式（明确不做）

- 逐个 mod 打补丁、堆特判（用户原话："兼容性和可维护性地狱……100 个补丁互相冲突"）；
- 因为"有原生版"就把该 mod 从 Connector 目标里划掉（除 L3 边界）；
- 把"能加载"当"兼容"（功能缺失不算通过）；
- 用退出码判断成败（关窗路径 exit=1 已知不可信，判据用 fatal + crash report + world_joined）。

## 8. 风险与观察点

- **上游漂移**：Connector beta.17 → 后续版本可能改 mixin remap / API 面，corpus 需能一键重跑；
- **前置依赖**：单 mod 跑会因为缺前置误判，基础前置集（FFAPI + kotlin + 常用库）要固定并随 corpus 版本化；
- **假阳性/假阴性**：quickPlay 进世界受存档/渲染环境影响；判定器要区分"mod 失败"与"环境失败"（如显卡驱动、OOM）；
- **样本选择偏差**：前 300 名以 Fabric-only 为主才够 40 个；若不足，把"both 的 Fabric 版"作为补充集并单独标指标；
- **L2 的诱惑**：修好一个 `@WrapMethod` 很容易让人继续修第二个，需守住"复杂签名不做"的线。

## 9. 与 HANDOFF 的关系

- 本文件管**方向与判据**，HANDOFF 管**事实与实现**；冲突以 HANDOFF 最新实测为准；
- 每完成一个 P 阶段：HANDOFF「关键技术决策」加一条、「下一步」划掉一项，并把 corpus 通过率写进「当前状态」。
