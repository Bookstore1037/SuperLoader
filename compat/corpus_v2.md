# SuperLoader 兼容样本集 v5（2026-11-04，含首轮 auto 实测）

> 数据源：`compat/deps_closure.json`（每个 jar 带 `version_id` + `sha1`，可复现安装）。
> 首轮实测：`logs/compat/20261104-124552/`（auto 9 个，9 pass / 0 fail）。
> 逐条修订说明见 `REVISION.md` §12 / §v4。

## 0. 判定口径

- **覆盖范围：客户端侧（UI/HUD/QoL/性能/库）；内容层与服务端不在 90% 口径内**
- `auto`：样本 jar 真的进 ModList（`sample_loaded=true`）+ 进存档 + 无 FATAL + 无 crash report（超时未产生新 runtime.json 判 fail）
- `manual`：auto 四条 + 人工核查“核心功能可用”
- 通过率：`auto_rate = auto_pass_n / 9`；`manual_rate = manual_pass_n / 34（分母写死；未核样本既不计入分子也不改分母）。截至 2026-11-05 已核 20 条、全 pass（见 manual_results）`
- 负例（expected=fail）与移植类（provenance=ported）不进任何分母
- 90% 数字旁边必须带覆盖范围声明，不允许裸报
- ⚠ auto 子集是按“能否自动断言”挑的（无 UI / 有文件产物 / 有日志标记），不代表主样本集分布；auto_rate 只描述这 9 个样本
- 首轮实测（None）：auto **9/9 pass**；manual 尚未人工核（分母仍 33）

## 0.1 v1 覆盖范围

- 覆盖：**客户端侧（UI/HUD/QoL/性能/库）**
- 不覆盖：**服务端/内容层（worldgen、结构、配方、生物）**
- 理由：内容正确性无法用“进存档 + 无崩溃”判定（要按种子比对地形/结构/掉落），smoke 测试只会给出假数字；仅保留 6 个内容组样本在阶段 2 做“能进世界”的 smoke，单独报告

## 0.2 其他约定

- 主样本 = 分母（auto 9 / manual 35）；负例、移植类、infra、内容组都不进分母。
- 依赖一律装 Fabric 构建（测 Connector remap 路径）；cloth-config / yacl / resourceful-lib 的原生构建只作参照组，评测台不自动装。
- fabric-api(桥接) 指运行时模组 forgified-fabric-api（44 模块），不是 Modrinth 上的 fabric-api，见 assembly.ffapi。
- 坏 jar 会毒化 Connector early remap，必须单样本隔离跑（HANDOFF 决策 28）：隔离粒度是 mods 目录 + 存档，不是整实例复制。
- 依赖闭包 61/61 完整；每个 jar 带 version_id + sha1，评测台装完必须校验（compat/deps_closure.json）。
- replaymod 1.21-2.6.28 在 NeoForge 21.1 下必崩（L2 目标迁移 + Connector 错误重定位 @At），不是 mod 自身 bug，也不是 refmap 缺口；详见 compat/replaymod-investigation.md。

## 0.3 实例拼装与判定规则（写死）

| 项 | 规则 |
|---|---|
| fabric-api(桥接) | fabric-api(桥接) = SuperLoader 运行时模组 forgified-fabric-api-<ver>+<n>+1.21.1.jar（44 个模块），由 superloader.py 的 MOD_SLUGS 下载到 <mods>/；不是样本依赖，不从 Modrinth 装 fabric-api |
| 运行时模组 | `connector-*-full.jar`、`forgified-fabric-api-*.jar`、`superloader_companion-*.jar` |
| mods 隔离 | 每样本 mods.compat/<slug>/ → 运行时把实例 mods/ 暂存为 mods.__baseline、复制样本目录到 mods/（FML 只扫 gameDir/mods），跑完立即换回；异常中断用 --restore-mods |
| 判定门槛 | pass 还要求 sample_loaded=true：样本自己的 jar 必须出现在本次 ModList 且 loaded 非空，否则 fail(sample_not_loaded)——首轮 12:16 的 9 个 pass 就是没过这道门（游戏读的是实例 mods/） |
| fail 顺序 | fatal_in_log > crash_screen > timeout_no_runtime > sample_not_loaded > no_world_join > pass |
| 存档 | 运行前从 logs/compat/save-backup/新的世界 恢复存档（首次运行先备份，17 MB），避免样本间污染 |
| 超时 | 启动后 240 秒内 runtime.json 未更新（mtime 与 generated_at 都不变）→ verdict=fail reason=timeout_no_runtime |
| crash screen | 进程存活但出现新的 crash-reports/*.txt 或日志出现 crash screen 标记 → fail reason=crash_screen（关窗 exit_code=0 不算 pass） |
| 进存档证据 | companion 的 world_joined 事件尚未实现（P1 待办）。当前用客户端日志的强证据判定：(A) LoggerChunkProgressListener 的 `Time elapsed: <n> ms`（出生点区块加载完成，一次性打印）；(B) `Saving chunks for level`（世界被保存过，只可能发生在进入之后）。弱证据只记录不判定：AdvancementTree 的 `Loaded <n> advancements`、`Preparing spawn area`。同时记录 `level.dat` mtime 是否推进作为旁证。实测 2026-11-04 12:06 原生 Sodium 启动：强证据命中 `Time elapsed: 273 ms`，弱证据命中 `Loaded 1465 advancements`，level.dat 被写。 |

## 1. 主样本集（42 个；auto 9 / manual 33）

| # | 样本 | 版本 | 判定 | 实测 | 来源 | NeoForge 构建 | 直接前置〔loader〕 | conn_dep | 闭包 | 安装集 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | modmenu | 11.0.5 | manual | 未测 | official | 无 | fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕、fabric-screen-api-v1@2.0.26+9991ca2f19〔ffapi(桥接)〕、fabric-key-binding-api-v1@1.0.47+62cc7ce119〔ffapi(桥接)〕、fabric-lifecycle-events-v1@2.6.0+e40d8add19〔ffapi(桥接)〕 | no | 6 | 1 jar / 0.9 MB |
| 2 | zoomify | 2.15.2+1.21.1 | manual | 未测 | official | 无 | fabric-language-kotlin@1.14.2+kotlin.2.4.21〔fabric〕、yacl@3.8.2+1.21.1-fabric〔fabric〕 | no | 6 | 3 jar / 9.7 MB |
| 3 | krypton | 0.2.8 | auto | pass/none | official | 无 | — | no | 2 | 1 jar / 0.2 MB |
| 4 | language-reload | 1.7.6+1.21.1 | manual | 未测 | official | 无 | fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕 | no | 3 | 1 jar / 0.1 MB |
| 5 | presence-footsteps | 1.11.2+1.21 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕、kirin（内嵌） | yes | 5 | 1 jar / 5.4 MB |
| 6 | debugify | 1.21.1+1.1 | auto | pass/none | official | 无 | fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕 | no | 4 | 1 jar / 0.3 MB |
| 7 | visuality | 0.7.7+1.21 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕、cloth-config@15.0.140〔fabric〕 | no | 5 | 2 jar / 1.2 MB |
| 8 | morechathistory | 1.3.1 | manual | 未测 | official | 无 | — | no | 2 | 1 jar / 0.0 MB |
| 9 | litematica | 0.19.61 | manual | 未测 | official | 无 | malilib@0.21.10〔fabric〕 | no | 4 | 2 jar / 2.9 MB |
| 10 | optigui | 2.3.0-beta.9+1.21 | manual | 未测 | official | 无 | fabric-events-interaction-v0@0.7.14+057f5afd19〔ffapi(桥接)〕、fabric-key-binding-api-v1@1.0.47+62cc7ce119〔ffapi(桥接)〕、fabric-lifecycle-events-v1@2.6.0+e40d8add19〔ffapi(桥接)〕、fabric-networking-api-v1@4.3.1+204211bf19〔ffapi(桥接)〕、fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕、fabric-language-kotlin@1.14.2+kotlin.2.4.21〔fabric〕 | no | 9 | 2 jar / 8.4 MB |
| 11 | better-mount-hud | 1.2.4 | manual | 未测 | official | 无 | — | no | 2 | 1 jar / 0.0 MB |
| 12 | fastquit | 3.0.0+1.20.6 | auto | pass/none | official | 无 | fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕、cloth-config@15.0.140〔fabric〕 | no | 5 | 2 jar / 1.2 MB |
| 13 | fabrishot | 1.14.1 | manual | 未测 | official | 无 | fabric-lifecycle-events-v1@2.6.0+e40d8add19〔ffapi(桥接)〕、fabric-key-binding-api-v1@1.0.47+62cc7ce119〔ffapi(桥接)〕 | no | 3 | 1 jar / 0.0 MB |
| 14 | paginatedadvancements | 2.5.1 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕、cloth-config@15.0.140〔fabric〕 | no | 4 | 2 jar / 1.2 MB |
| 15 | main-menu-credits | 1.2.0 | manual | 未测 | official | 无 | — | no | 3 | 1 jar / 0.0 MB |
| 16 | tooltipfix | 1.1.1-1.20 | manual | 未测 | official | 无 | — | no | 2 | 1 jar / 0.0 MB |
| 17 | better-ping-display-fabric | 1.1.1 | manual | 未测 | official | 无 | — | no | 2 | 1 jar / 0.0 MB |
| 18 | no-resource-pack-warnings | 1.3.1 | auto | pass/none | official | 无 | — | no | 0 | 1 jar / 0.0 MB |
| 19 | stendhal | 1.4.1-1.21 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕 | no | 2 | 1 jar / 0.5 MB |
| 20 | forcecloseworldloadingscreen | 2.2.3 | auto | pass/none | official | 无 | — | no | 3 | 1 jar / 0.1 MB |
| 21 | tweakeroo | 0.21.61 | manual | 未测 | official | 无 | malilib@0.21.10〔fabric〕 | no | 4 | 2 jar / 2.0 MB |
| 22 | status-effect-bars | 1.0.6 | manual | 未测 | official | 无 | cloth-config@15.0.140〔fabric〕 | no | 3 | 2 jar / 1.1 MB |
| 23 | cave-dust | 3.0.1 | manual | 未测 | official | 无 | — | no | 4 | 1 jar / 0.2 MB |
| 24 | wakes | 0.4.1+1.21.1 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕 | no | 4 | 1 jar / 0.3 MB |
| 25 | better-selection | 1.6.8 | manual | 未测 | official | 无 | — | no | 1 | 1 jar / 0.0 MB |
| 26 | chatpatches | 8.0.0 | manual | 未测 | official | 无 | fabric-lifecycle-events-v1@2.6.0+e40d8add19〔ffapi(桥接)〕、fabric-networking-api-v1@4.3.1+204211bf19〔ffapi(桥接)〕、fabric-screen-api-v1@2.0.26+9991ca2f19〔ffapi(桥接)〕、yacl@3.8.2+1.21.1-fabric〔fabric〕 | no | 8 | 2 jar / 2.5 MB |
| 27 | custom-splash-screen | 2.2.2 | manual | 未测 | official | 无 | midnightlib（内嵌） | yes | 1 | 1 jar / 0.6 MB |
| 28 | held-item-info | 1.7.0 | manual | 未测 | official | 无 | — | no | 2 | 1 jar / 0.1 MB |
| 29 | hold-my-items | 4.3 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕 | no | 4 | 1 jar / 0.1 MB |
| 30 | connectiblechains | 2.5.7+1.21.1 | manual | 未测 | official | 无 | cloth-config@15.0.140〔fabric〕 | no | 4 | 2 jar / 1.6 MB |
| 31 | lazy-language-loader | 0.3.7 | auto | pass/none | official | 无 | — | no | 2 | 1 jar / 0.0 MB |
| 32 | fpsdisplay | 4.2.1+1.21.1 | manual | 未测 | official | 无 | fabric-key-binding-api-v1@1.0.47+62cc7ce119〔ffapi(桥接)〕、fabric-lifecycle-events-v1@2.6.0+e40d8add19〔ffapi(桥接)〕 | no | 3 | 1 jar / 0.1 MB |
| 33 | reacharound | 1.3.1 | manual | 未测 | official | 无 | fabric-key-binding-api-v1@1.0.47+62cc7ce119〔ffapi(桥接)〕 | no | 3 | 1 jar / 0.0 MB |
| 34 | inmis | 2.8.2-1.21.1 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕 | no | 4 | 1 jar / 0.1 MB |
| 35 | universal-graves | 3.4.4+1.21 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕 | no | 4 | 1 jar / 1.6 MB |
| 36 | lenient-death | 1.2.5+1.21.1 | manual | 未测 | official | 无 | fabric-api〔ffapi(桥接)〕、fabric-permissions-api-v0（内嵌）、jackfredlib-lying（内嵌） | yes | 5 | 1 jar / 0.9 MB |
| 37 | totemcounter | 1.6.1+mc1.21 | manual | 未测 | official | 无 | fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕、fabric-key-binding-api-v1@1.0.47+62cc7ce119〔ffapi(桥接)〕、fabric-command-api-v2@2.2.28+36d727be19〔ffapi(桥接)〕、ukulib@1.4.1+1.21〔fabric〕 | no | 6 | 2 jar / 0.4 MB |
| 38 | malilib | 0.21.10 | manual | 未测 | official | 无 | fabric-networking-api-v1@4.3.1+204211bf19〔ffapi(桥接)〕、fabric-resource-loader-v0@1.3.1+4ea8954419〔ffapi(桥接)〕 | no | 3 | 1 jar / 1.3 MB |
| 39 | yosbr | 0.1.2 | auto | pass/none | official | 无 | — | no | 1 | 1 jar / 0.0 MB |
| 40 | stackdeobf | 1.4.3+08e71cc | auto | pass/none | official | 无 | — | no | 3 | 1 jar / 0.3 MB |
| 41 | faster-random | 5.1.0 | auto | pass/none | official | 无 | — | no | 2 | 1 jar / 0.0 MB |
| 42 | itemscroller | 0.24.60 | manual | 未测 | official | 无 | — | no | 0 | 0 jar / 0.0 MB |

`conn_dep=yes` 表示闭包里带 jar-in-jar 依赖，失败时先查 Connector 是否 remap 内层 jar（L4）。

## 2. auto 子集（9 个；第一版通过率只用它）

| # | 样本 | 自动断言点 | 首轮实测 |
|---|---|---|---|
| 1 | krypton | 无感；进世界后网络正常（无断连） | pass（none） |
| 2 | debugify | F3 调试屏出现 debugify 补充项；配置菜单可开 | pass（none） |
| 3 | fastquit | 关闭游戏立即退出（无卡顿） | pass（none） |
| 4 | no-resource-pack-warnings | 无资源包警告弹窗 | pass（none） |
| 5 | forcecloseworldloadingscreen | 加载世界时关闭界面不崩 | pass（none） |
| 6 | lazy-language-loader | 切换语言不卡死 | pass（none） |
| 7 | yosbr | 客户端 | pass（none） |
| 8 | stackdeobf | 客户端 | pass（none） |
| 9 | faster-random | 客户端 | pass（none） |

auto 判定 = sample_loaded + 进存档 + 无 FATAL + 无 crash report，再叠加表里断言点；不满足任一即 fail。

## 3. 负例（1 个，expected=fail，不进分母）

| 样本 | 判定 | 预期层 | 预期原因 | 实测层 |
|---|---|---|---|---|
| carpet | negative | L2 | mixin 改 vanilla 活塞/方块更新行为（PistonStructureResolver_customStickyMixin、Level_fillUpdatesMixin），经 Connector 重映射后 apply 失败 | fail（L2） |

用途：验证判定器“判得出失败、层归得对”。若实测通过说明假设错，改回 pass 并记录。

### 3.1 负例控制（可直接复现的已知失败，不进分母）

| 控制 | jar | 预期层 | 实测 | 证据 |
|---|---|---|---|---|
| neg_dep_test | `logs/dep-test/superloader_dep_test-1.0.0.jar` | L0 | fail（fatal_in_log） | 纯元数据 jar，depends fabric-screen-api-v1 >=99.0.0；证明判定器能抓到初始化阶段依赖失败 |
| neg_sodium_fabric | `logs/tmp-mods-backup/[钠] sodium-fabric-0.8.13+mc1.21.1.jar` | L2 | fail（fatal_in_log） | Fabric 版 Sodium 经 Connector 重映射后 @WrapMethod handler 签名不匹配；证明判定器能抓到 mixin 注解重映射失败 |

## 4. 移植类（2 个，provenance=ported，不进分母）

| 样本 | 版本 | 判定 | 移出理由 |
|---|---|---|---|
| beautify-refabricated | 3.6.5 | manual | 社区 refabrication（Suel-ki），非原作者发布 |
| sophisticated-core-unofficial-fabric-port | 1.21.1-1.2.9.21.168 | auto | Unofficial Fabric port（Salandora） |

理由：失败优先归因移植质量，对 Connector 桥接补丁无指导意义。内容组里的移植类只影响内容组，不影响主指标。

## 5. 基础设施（7 个，评测台预装，不计通过率）

| 样本 | 版本 | NeoForge 构建 | 装哪一版 | 直接前置〔loader〕 |
|---|---|---|---|---|
| fabric-language-kotlin | 1.14.2+kotlin.2.4.21 | 无 | Fabric（测 remap） | — |
| cardinal-components-api | 6.1.3 | 无 | Fabric（测 remap） | — |
| cloth-config | 15.0.140 | 有 | Fabric（测 remap） | — |
| yacl | 3.8.2+1.21.1-fabric | 有 | Fabric（测 remap） | — |
| resourceful-lib | 3.0.12 | 有 | Fabric（测 remap） | — |
| placeholder-api | 2.4.2+1.21 | 无 | Fabric（测 remap） | — |
| ukulib | 1.4.1+1.21 | 无 | Fabric（测 remap） | — |

`yacl` 的 `fabric-api(桥接)` 由运行时模组 FFAPI 提供，见 §0.3。

## 6. 内容组（5 个，阶段 2；不进 90% 分母）

| 样本 | 版本 | 来源 | 直接前置〔loader〕 | 安装集 |
|---|---|---|---|---|
| farmers-delight-refabricated | 1.21.1-3.3.6+refabricated | ported | fabric-api〔ffapi(桥接)〕 | 1 jar / 3.1 MB |
| betterend | 21.0.11 | official | fabric-api〔ffapi(桥接)〕、bclib@21.0.13〔fabric〕 | 4 jar / 93.1 MB |
| betternether | 21.0.11 | official | fabric-api〔ffapi(桥接)〕、bclib@21.0.13〔fabric〕 | 4 jar / 26.1 MB |
| the-bumblezone-fabric | 7.17.3+1.21.1-fabric | official | resourcefullib（内嵌）、midnightlib@1.10.0〔fabric〕 | 2 jar / 79.8 MB |
| repurposed-structures-fabric | 7.5.22+1.21.1-fabric | official | midnightlib@1.10.0〔fabric〕 | 2 jar / 7.9 MB |

## 7. L3 排除名单

### (a) L3 且无原生构建（真不做）

vulkanmod、exordium、nvidium、cull-less-leaves、indium、c2me-fabric、ebe、animatica、skyboxify、flashback、threadtweak、bobby、axiom、cit-resewn、particular、eating-animation、capes、gamma-utils

### (b) L3 但有原生构建（记录 + 推荐原生，不算兼容性失败）

| 样本 | 原生构建证据 | 结论 |
|---|---|---|
| sodium | mc1.21.1-0.8.13-neoforge（2026-08-28，官方构建，已实测进世界通过：决策 29） | 推荐原生；Connector 路径不追，不计失败 |
| iris | 1.8.14-beta.1+1.21.1-neoforge（2026-06-13） | 推荐原生；Connector 路径不追，不计失败 |
| sodium-extra | mc1.21.1-0.9.5+neoforge（2026-10-25） | 推荐原生；Connector 路径不追，不计失败 |

Sodium 与 c2me 不并列：Sodium 有官方 NeoForge 构建且实测通过（HANDOFF 决策 29），c2me 没有。

## 8. 共用前置统计（主样本）

| 前置 | 被几个主样本依赖 |
|---|---|
| cloth-config | 5 |
| fabric-language-kotlin | 2 |
| yacl | 2 |
| malilib | 2 |
| ukulib | 1 |

## 9. jar 清单（去重，含 version_id + sha1）

共 **66** 个去重 jar。

| jar | loader | version_id | sha1 |
|---|---|---|---|
| `modmenu-11.0.5.jar` | fabric | `6lgOkclV` | `2321d890a25b5985` |
| `zoomify-2.15.2+1.21.1.jar` | fabric | `6jrMC48Z` | `9ec9c47e1d3465ea` |
| `fabric-language-kotlin-1.14.2+kotlin.2.4.21.jar` | fabric | `SKW1BTL3` | `f1d4ab6ecd54d978` |
| `yet_another_config_lib_v3-3.8.2+1.21.1-fabric.jar` | fabric | `o3cDn8Vp` | `e075503382f70715` |
| `krypton-0.2.8.jar` | fabric | `Acz3ttTp` | `73e792eb5f120787` |
| `language-reload-1.7.6+1.21.1.jar` | fabric | `lLMGPiZe` | `95c1266f43e330d4` |
| `PresenceFootsteps-1.11.2+1.21.jar` | fabric | `CrvsDgLW` | `2e0228905a1e5a2d` |
| `Debugify-1.21.1+1.1.jar` | fabric | `pyIdu3f1` | `3388ba4c0f973f0a` |
| `visuality-0.7.7+1.21.jar` | fabric | `dhKbgdIb` | `8d239710c1c1983d` |
| `cloth-config-15.0.140-fabric.jar` | fabric | `HpMb5wGb` | `5d82342a2df53fd6` |
| `morechathistory-1.3.1.jar` | fabric | `3siYJiWG` | `b4337ef9dc0a6cdf` |
| `litematica-fabric-1.21-0.19.61.jar` | fabric | `o7i8oi1Z` | `efce2dd7118b1e61` |
| `malilib-fabric-1.21-0.21.10.jar` | fabric | `C99LEy6r` | `e2699ef71618c54f` |
| `fallingleaves-1.17.1+1.21.1.jar` | fabric | `Y0zS16Bk` | `5210b4cb359a95c5` |
| `optigui-2.3.0-beta.9+1.21.jar` | fabric | `npnKNaoI` | `9f72bd8077911862` |
| `bettermounthud-1.2.4.jar` | fabric | `yyJushgo` | `4df822bd5bd7d2e1` |
| `fastquit-3.0.0+1.20.6.jar` | fabric | `dIGKewCo` | `9c4bf4fc3292d627` |
| `fabrishot-1.14.1.jar` | fabric | `HfdXLVRy` | `c8afc690bb3508df` |
| `replaymod-1.21-2.6.28.jar` | fabric | `DKvQ3lQq` | `528894b52cf3a35a` |
| `paginatedadvancements-2.5.1.jar` | fabric | `fQnpir9a` | `23a4570fb52d6213` |
| `main-menu-credits-1.2.0.jar` | fabric | `eUN0SbET` | `37ad23f76336eedb` |
| `tooltipfix-1.1.1-1.20.jar` | fabric | `B2L4LeMV` | `de704792c691e3d1` |
| `BetterPingDisplay-Fabric-1.21.1-1.1.1.jar` | fabric | `xCWQ8iLW` | `534ba30ec8a7ea23` |
| `beautify-3.6.5-fabric+1.21.1.jar` | fabric | `qpzaFKKc` | `0842c2a4abc37097` |
| `fabric-carpet-1.21-1.4.147+v240613.jar` | fabric | `f2mvlGrg` | `54f2907d83e67283` |
| `no-resource-pack-warnings-1.3.1.jar` | fabric | `73nzTFDd` | `7a21f4604fab9462` |
| `stendhal-1.4.1-1.21.jar` | fabric | `I3a5043B` | `a653cc8d30a28d60` |
| `forcecloseloadingscreen-2.2.3.jar` | fabric | `G95MOUIu` | `58a3ba92c29cbe91` |
| `tweakeroo-fabric-1.21-0.21.61.jar` | fabric | `XweKE6fy` | `0abe7330be5d4d6c` |
| `status-effect-bars-1.0.6.jar` | fabric | `ramqgou6` | `c44856cace7ab4cc` |
| `cave_dust-3.0.1.jar` | fabric | `8zG4dQ2R` | `a9f2b1af1dc26b23` |
| `wakes-0.4.1+1.21.1.jar` | fabric | `WuY7eJX9` | `c4f4d09a4b9362bc` |
| `better-selection-1.6.8.jar` | fabric | `XjB8wIwx` | `b7d49d2bb41fa673` |
| `chatpatches-8.0.0+1.21.1-fabric.jar` | fabric | `lIUP93Uo` | `2701c37aa71ed3e1` |
| `customsplashscreen-2.2.2.jar` | fabric | `LspxE3dn` | `c5567c7efc6a305e` |
| `held-item-info-1.7.0.jar` | fabric | `EvcC3qTM` | `32f34e6b481e2d3c` |
| `HMI 4.3 - 1.21.(1).jar` | fabric | `QvoJWaYG` | `19ff289fa00d3380` |
| `connectiblechains-2.5.7+1.21.1.jar` | fabric | `bix8ndct` | `ad08f0f3a6c6cc18` |
| `lazy-language-loader-0.3.7.jar` | fabric | `4cZkq7uT` | `ea6349ba680dc616` |
| `fpsdisplay-4.2.1+1.21.1.jar` | fabric | `nWbgJNPj` | `d91988c71ccf830c` |
| `reacharound+1.21-1.3.1.jar` | fabric | `QbLX7jsn` | `4d56d0a9beac6de9` |
| `inmis-2.8.2-1.21.1.jar` | fabric | `iE11BIfP` | `466363e2abf837ed` |
| `graves-3.4.4+1.21.jar` | fabric | `Fg64B87Y` | `e289663f13de87ed` |
| `lenientdeath-1.2.5+1.21.1.jar` | fabric | `FUbtsgt9` | `cca7eb614db1053e` |
| `totemcounter-1.6.1+mc1.21.jar` | fabric | `IKkXFg8J` | `fb1d6035bd1d7833` |
| `ukulib-1.4.1+1.21.jar` | fabric | `WIHBQHSG` | `069701cb77c775ae` |
| `minihud-fabric-1.21-0.32.60.jar` | fabric | `v23Owcjb` | `302a3cf8a3054b59` |
| `yosbr-0.1.2.jar` | fabric | `KMOzdYko` | `f0340e9c0bc95d67` |
| `StackDeobfuscatorFabric-1.4.3+08e71cc.jar` | fabric | `pyiVLk9R` | `c36982af69e6d9d9` |
| `fasterrandom-5.1.0.jar` | fabric | `BbFqiKvi` | `440720daaf51d5ad` |
| `sophisticatedcore-1.21.1-1.2.9.21.168.jar` | fabric | `ZLVrtF0Q` | `43a95dfa338a2a6b` |
| `ForgeConfigAPIPort-v21.1.6-1.21.1-Fabric.jar` | fabric | `N5qzq0XV` | `18bf1f21cd2db6dc` |
| `mixintrace-1.1.1+1.17.jar` | fabric | `LGYOH4RN` | `7fbb0130db0e427e` |
| `cardinal-components-api-6.1.3.jar` | fabric | `nLsCe2VD` | `e762f5205c0fd0f9` |
| `resourcefullib-fabric-1.21-3.0.12.jar` | fabric | `Hf91FuVF` | `cb67e1302b511695` |
| `placeholder-api-2.4.2+1.21.jar` | fabric | `U5bhVym2` | `aa1b9a49f9f190df` |
| `FarmersDelight-1.21.1-3.3.6+refabricated.jar` | fabric | `wbVXT4Ua` | `6d75a472d56c7cf0` |
| `better-end-21.0.11.jar` | fabric | `4qhBEg6J` | `625f4340bd9ab67a` |
| `bclib-21.0.13.jar` | fabric | `TxWM7AW8` | `6a46eb6a8fb9cc0a` |
| `wunderlib-21.0.8.jar` | fabric | `NWOZ9B7R` | `ad8c66609db36376` |
| `worldweaver-21.0.13.jar` | fabric | `mPmeykPR` | `01e7196395386bbd` |
| `better-nether-21.0.11.jar` | fabric | `M1o6hR2m` | `c6dcee6fd46d25d0` |
| `friendsandfoes-fabric-5.0.4+mc1.21.1.jar` | fabric | `uh0ha6mZ` | `f9c011beb6731531` |
| `the_bumblezone-7.17.3+1.21.1-fabric.jar` | fabric | `WXjHJFB3` | `9fecf79de2158c90` |
| `midnightlib-fabric-1.10.0+1.21.1.jar` | fabric | `jQ0KXdpD` | `3120b1329ab0d01b` |
| `repurposed_structures-7.5.22+1.21.1-fabric.jar` | fabric | `JRMMCb1O` | `5cd080074996fbb0` |

## 10. 已移出：上游缺陷（不修、不改 jar）

| slug | version | 层 | 原因 | 处置 | 证据 |
|---|---|---|---|---|---|
| `fallingleaves` | 1.17.1 | L2 | 上游缺陷：发布包 fabric.mod.json 丢 accessWidener 键，jar 内 .aw 是死文件；@Invoker target ParticleEngine$MutableSpriteSet 为 package-private → IllegalAccessError | 已移出实例 mods/，不修、不改 jar；做上游 issue 才是正确修法 | compat/fallingleaves-investigation.md; compat/invoker_inner_target_scan.md |
| `replaymod` | 1.21-2.6.28 | L2 | NeoForge 21.1 把 GameRenderer.render 里的 Screen;renderWithTooltip 调用换成 ClientHooks.drawScreen，原注入点消失；Connector 把 @At target 重写成 DeltaTracker;getGameTimeDeltaTicks 且丢掉 shift=AFTER，handler 每帧在 overlay 阶段执行，GuiGraphics 为 null 时 VanillaGuiScreen$EventHandler.onGuiRender 的 stack.flush() NPE | 不在 companion 写特判；作为 Connector 上游 mixin patch 缺口处理，issue 草稿见 compat/replaymod-investigation.md | compat/replaymod-investigation.md; crash-reports/crash-2026-11-05_13.40.40-client.txt |
| `minihud` | None | L2 | NeoForge 21.1.265 把 Language.loadFromJson(InputStream,BiConsumer) 改成转发给 3 参重载，BiConsumer.accept 的调用点搬走；minihud 的 @ModifyArgs 在 2 参方法体里扫到 0 条 → required mixin 注入失败，启动即崩 | 移出 mods/，不修；需要 Connector 上游加 patch 把注入点迁到 3 参重载 | ['compat/minihud-investigation.md', 'crash-2026-11-05_18.41.34-client.txt', 'neoforge-21.1.265-client.jar: net/minecraft/locale/Language'] |
| `the-bumblezone-fabric` | 7.17.3+1.21.1 | L2 | Connector 的 adapter（ResolverSyntheticInstanceof）在 Recipe.getDirtyTarget() 为 null 时直接解引用，转换 the_bumblezone 的 LivingEntityMixin 时 NPE，整个 jar 转换中止 | 短期移出 mods/；治本给 Sinytra/Connector 提 issue（adapter null 检查） | compat/bumblezone-investigation.md |
| `friends-and-foes` | 5.0.4+mc1.21.1 | L2 | NeoForge 枚举扩展机制接管了 MobCategory 的 7 参保留构造器，Fabric 枚举 mixin（AddCustomSpawnGroupMixin）在 attach 阶段找不到该构造器，Mixin 抛 NPE（method is null） | 移出 mods/（保留在 logs/removed-mods/）；Modrinth 无 NeoForge 构建；治本需 Connector 支持枚举 mixin → IExtensibleEnum 转换，上游 issue 已起草 | compat/friendsandfoes-investigation.md |

## 11. 已知口径例外

- fastquit 3.0.0+1.20.6：jar 内 depends.minecraft = ">=1.20.5"（读自 fabric.mod.json），1.21.1 满足，不会触发 L0；版本号只是旧命名（1.21.1 上无更新构建）。
- tooltipfix 1.1.1-1.20：jar 内 depends 里**没有 minecraft 项**（只有 fabricloader>=0.12.5 与 fabric），FML 不会因 MC 版本拒绝加载；但它是 1.20 编译的，风险落在 L2/L4（映射/方法签名），不在 L0。
- distancetransform / distance-transform 在 Modrinth 均 404，没能确认是改名重发；已从 L3 排除名单删除（项目不存在，不属于“L3 不做”）。
- appleskin 换 NeoForge 版 3.0.9（不内嵌 cloth-config）后，顶层放 NeoForge 版 cloth-config 15.0.140，Fabric 侧 depends cloth-config 的样本（* 与 >=15.0.140）全部解析成功，modmenu 正常，suspects=0。旧结论「Fabric 版 appleskin 内嵌 15.0.127 锁死 cloth-config」仅对 Fabric 版成立。fallingleaves 的 L2（@Invoker 访问 ParticleEngine$MutableSpriteSet 失败）与 cloth-config 无关，已移出。
- fallingleaves 1.17.1+1.21.1：L2 访问失败（@Invoker target ParticleEngine$MutableSpriteSet 是 package-private，而发布包 fabric.mod.json 无 accessWidener 键，jar 内 .aw 是死文件）。不是 Connector 重映射缺口——mapped jar 里 target 已正确映射为 mojang 名；上游 build.gradle 有 loom.accessWidenerPath，发布丢键。核实见 compat/fallingleaves-investigation.md，扫描表 compat/invoker_inner_target_scan.md。
- malilib 家族（malilib/litematica/tweakeroo/minihud）的 mixin config 都不带 refmap（直接用 intermediary 名），Connector 重映射正常；minihud 的 MixinLanguage 在 NeoForge 上失败是因为 NeoForge 把 Language.loadFromJson(InputStream,BiConsumer) 改成转发给 3 参重载、BiConsumer.accept 调用点搬走，@ModifyArgs 扫到 0 条（L2，见 compat/minihud-investigation.md）。
- friends-and-foes 5.0.4+mc1.21.1 在 NeoForge 下崩在枚举 mixin attach：MobCategory 的 7 参构造器是 NeoForge 的保留构造器（RuntimeEnumExtender 消费），Fabric 枚举 mixin 找不到它 → Mixin NPE。不是 mod bug、不是 refmap 缺口，见 compat/friendsandfoes-investigation.md；已移出 mods/。

## 12. manual 验收进度（用户实测）

已核 **31 / 33** 条，pass **31**（分母来自 main 里 `verdict_mode=manual` 且未被移出的样本；未核不计入分子）。明细：

| mod | 检查点 | 结果 | 日期 | 备注 |
|---|---|---|---|---|
| `better-mount-hud` | 骑乘时 HUD 显示血量/跳跃条 | pass | 2026-11-05 |  |
| `language-reload` | F3+T 重载语言不崩、界面文字正确 | pass | 2026-11-05 |  |
| `morechathistory` | 聊天记录条数超出原版上限 | pass | 2026-11-05 |  |
| `tooltipfix` | 长提示文本换行而非溢出屏幕 | pass | 2026-11-05 |  |
| `main-menu-credits` | 主菜单右下角出现版本/署名文本 | pass | 2026-11-05 |  |
| `fabrishot` | 截图快捷键生成本地高清截图文件 | pass | 2026-11-05 |  |
| `visuality` | 粒子效果按配置出现 | pass | 2026-11-05 |  |
| `paginatedadvancements` | 进度界面分页可用 | pass | 2026-11-05 |  |
| `inmis` | 背包物品栏可用、存取正常 | pass | 2026-11-05 |  |
| `status-effect-bars` | 状态效果 HUD 条显示且位置正确 | pass | 2026-11-05 |  |
| `connectiblechains` | 链条连接相邻栅栏 | pass | 2026-11-05 |  |
| `appleskin` | 饱食度/饱和度 HUD 显示（换 NeoForge 3.0.9 后重验） | pass | 2026-11-05 | NeoForge 构建，不是 Fabric 样本；只作为整包功能检查，不进 manual_n |
| `better-ping-display-fabric` | 多人服务器中 HUD 显示 ping/延迟条 | pass | 2026-11-05 |  |
| `held-item-info` | 手持物品时 HUD 显示附魔/耐久信息 | pass | 2026-11-05 |  |
| `fpsdisplay` | HUD 显示帧率且数值随场景变化 | pass | 2026-11-05 |  |
| `reacharound` | 远距离放置方块时手臂伸展 | pass | 2026-11-05 |  |
| `cave-dust` | 洞穴尘埃粒子可见 | pass | 2026-11-05 |  |
| `wakes` | 水中尾迹粒子可见 | pass | 2026-11-05 |  |
| `better-selection` | 方块选中框样式改变 | pass | 2026-11-05 |  |
| `chatpatches` | 聊天记录持久化、重启后仍在 | pass | 2026-11-05 |  |
| `presence-footsteps` | 走路/落地音效与粒子正常 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `optigui` | 打开箱子/工作台界面正常，无 GUI 错位 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `stendhal` | 按 F 打开书本式界面，文本渲染正常 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `custom-splash-screen` | 启动画面显示自定义 splash | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `hold-my-items` | 移动物品时模型在手中保持 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `universal-graves` | 死亡后墓碑生成、可拾取物品 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `lenient-death` | 死亡不掉落配置生效 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `totemcounter` | 不死图腾计数 HUD 显示 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `malilib` | Mods → MaLiLib → Config 能开 GUI，热键注册无异常 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `litematica` | 能打开投影菜单并加载一个 .litematic（无投影可只看菜单） | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `tweakeroo` | 能打开 tweakeroo 配置 GUI | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |
| `itemscroller` | 滚轮在背包/箱子间移动物品正常 | pass | 2026-11-05 | 用户在 57 jar 实例（2026-11-05 18:57 启动，exit 0、fatal 0、suspects 0）实测通过 |

