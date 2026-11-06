# 兼容样本集 v4 — 逐条回应（2026-11-03）

对象：m00902 的 6 个阻塞项 + 3 个追问 + 2 条声明。A1–A3、nf_build、loader、B3、C2、C3 你已确认，不再重复。

数据源：`compat/corpus.json`（输入）、`compat/deps_closure.json`（闭包 + 元数据）、`compat/corpus_v2.md`（可读版，已重渲染为 v4）。

| # | 项 | 状态 | 落点 |
|---|---|---|---|
| 1 | fastquit / tooltipfix 的 `depends.minecraft` | 已读 jar，均不触发 L0 | `corpus_v2.md` §10、本文件 §1 |
| 2 | 反例判定列 | 判定列改 `negative`，单独成节 | `corpus_v2.md` §3 |
| 3 | fabric-api(桥接) 拼装 | 写死 = 运行时模组 FFAPI，不从 Modrinth 装 | `corpus_v2.md` §0.3、`corpus.json.assembly` |
| 4 | auto 未处理 crash screen | 加 `timeout_no_runtime` / `crash_screen` 两条 fail | §0.3、`tools/compat_sweep.py` |
| 5 | 隔离实例拼装 | 每样本独立 mods 目录 + 存档恢复 | §0.3、`core/paths.py`、`compat_sweep.py` |
| 6 | 移植类移出 | 2 个移出分母，auto 9 / manual 35 | `corpus_v2.md` §4 |
| 7 | auto 选样逻辑 | 承认是“能自动判”驱动，已写进口径 | `corpus_v2.md` §0 |
| 8 | jar-in-jar 依赖 | 新增 `conn_dep` 列，3 个 yes | `corpus_v2.md` §1 |
| 9 | manual 分母漂移 | 写死 35 | `corpus.json.rate_definition` |
| 10 | 覆盖范围声明 | 已加在口径首行 | `corpus_v2.md` §0 |
| 11 | distancetransform 404 | 两个 slug 都 404，确认不在名单 | `corpus_v2.md` §7 |

---

## 1. fastquit / tooltipfix：`depends.minecraft` 实测

读了两个 jar 内的 `fabric.mod.json`（`logs/check_fmj.py`）：

| 样本 | `depends` 全文 | `minecraft` 范围 | 1.21.1 是否满足 |
|---|---|---|---|
| fastquit 3.0.0+1.20.6 | `fabricloader >=0.15.7`、`minecraft >=1.20.5`、`fabric-resource-loader-v0 *`、`cloth-config *`、`java >=17` | `>=1.20.5`（开区间，无上界） | ✅ 满足 |
| tooltipfix 1.1.1-1.20 | `fabricloader >=0.12.5`、`fabric *` | **没有 minecraft 项** | ✅ 无约束，不会被 FML 拒绝 |

- fastquit 不会触发 L0；它的风险在“编译于 1.20.6”，如果出问题应在 L2/L4（映射/方法签名），不是版本校验。
- tooltipfix 连 MC 约束都没写，FML 层不会拦；同样是 1.20 编译，风险在 L2/L4。
- 两条已写进 `corpus_v2.md` §10「已知口径例外」，避免下次再被当成“1.21.1 版本校验收紧”误判。

## 2. 反例判定列

`corpus_v2.md` §1 主样本表已不含反例（主样本从 48 降到 44 = 48 − 2 移植 − 2 反例）。
反例单独放 §3，列名就是 `判定 = negative` + `预期层`，不再混在 manual 里。

## 3. fabric-api(桥接) 到底是什么

写死在 `corpus.json.assembly.ffapi` 与 `corpus_v2.md` §0.3：

> fabric-api(桥接) = SuperLoader 运行时模组 `forgified-fabric-api-<ver>+<n>+1.21.1.jar`（44 个模块），
> 由 `superloader.py` 的 `MOD_SLUGS = ["connector", "forgified-fabric-api"]` 负责下载到 `<mods>/`；
> 不是样本依赖，不从 Modrinth 装 fabric-api。

证据：实例 `mods/` 里现存 `forgified-fabric-api-0.116.15+2.3.6+1.21.1.jar`（5.6 MB）与 `connector-2.0.0-beta.17+1.21.1-full.jar`；
`core/apis.py` 也是从这个 jar 的 `META-INF/jars/*.jar` 里读 44 个模块。
所以评测台**不额外装** `fabric-api`，样本闭包只装 Fabric 构建的普通 mod + 这 3 个运行时模组。

## 4. auto 判定：新增两条 fail

判定器（`tools/compat_sweep.py`）的判定顺序：

1. `crash_screen`：进程存活但出现**新的** `crash-reports/*.txt`，或日志命中 `Cowardly refusing` / `crash screen` → **fail**。关窗 `exit_code = 0` 不算 pass（决策 27/29 的坑）。
2. `timeout_no_runtime`：启动后 240 秒内 `runtime.json` 的 mtime 与 `generated_at` 都不变 → **fail**（卡在 crash screen / 主菜单假死都落这里）。
3. `fatal_in_log`：日志命中致命行（10 条模式）。
4. `no_world_join`：没有进存档证据。
5. 全过才 `pass`。

## 5. 隔离：mods 目录级隔离，不复制整实例

写死：

- 每样本独立 mods 目录 `instances/1.21.1/mods.compat/<slug>/`，只放该样本闭包 + 3 个运行时模组。
- 通过新增的 `SL_MODS_DIR` 环境变量指过去（`core/paths.py` 的 `Paths.mods` 支持覆盖），`libraries/versions/assets` 仍只读共享。
- 存档：首次运行前把 `saves/新的世界`（17 MB）备份到 `logs/compat/save-backup/`，之后每次运行前恢复，样本之间不互相污染。

**为什么不在磁盘上复制整个 instance**：`libraries + versions + assets` 是 1 GB 量级的只读数据，
复制 46 份只增加磁盘占用、不增加隔离强度；决策 28 的“毒化”发生在 mods 目录里，隔离 mods 即命中要害。
如果后续发现存档之外的共享状态（如 `.cache/connector` 的 remap 缓存）也会串味，再升级为整实例 junction。

## 6. 移植类移出主样本

| 样本 | 原判定 | 处置 | 理由 |
|---|---|---|---|
| `sophisticated-core-unofficial-fabric-port` | auto | 移出（§4） | 第三方 Unofficial port（Salandora），失败优先归因移植质量 |
| `beautify-refabricated` | manual | 移出（§4） | 社区 refabrication（Suel-ki），同上 |
| `farmers-delight-refabricated` | 内容组 | 保持内容组，标 `provenance=ported` | 本就不进分母 |

- 数字：**auto 9 / manual 35**（不再凑 10）。没有从 manual 里挑 `better-selection`/`reacharound` 来补，理由是这两个的“功能可用”只能靠人眼（选中框颜色/交互距离），硬塞进来等于给 auto 掺水。
- `provenance: official | ported` 列已加到主样本与内容组，ported 不进分母。
- `sophisticated-backpacks` / `sophisticated-storage` / `deuf-refabricated`：**不在任何名单里**（既不在主样本、也不在 infra/content/L3/移植类），早期表里只是候选，没被选进来；已确认。

## 7. auto 子集选样逻辑（承认局限）

是“能自动判”驱动，不是“值得测”驱动：新增的 `yosbr`（写 options.txt）、`stackdeobf`（日志标记）、
`faster-random`（无 UI 库）都是因为产物可断言才进的。

因此口径里写死一句：**auto_rate 只描述这 9 个样本，不代表主样本集分布**（`corpus_v2.md` §0 的 ⚠ 行）。
对外报数时写成“auto 9/9（仅自动可判子集）”，不写成“兼容率 100%”。

## 8. jar-in-jar 与 Connector 的关系

新增 `conn_dep` 列（`yes` = 闭包里有 `kind=jij` 的依赖），主样本里 3 个：

| 样本 | 内嵌依赖 |
|---|---|
| `lenient-death` | `jackfredlib-lying`、`fabric-permissions-api-v0` |
| `presence-footsteps` | `kirin` |
| `custom-splash-screen` | `midnightlib` |

裁定规则写进报告：`conn_dep=yes` 的样本失败时，**先查 Connector 是否 remap 内层 jar**（L4），
再谈 L1/L2；对应日志关键词 `Skipping jar`、`nested`、`META-INF/jars`。
内容组里的 `the-bumblezone-fabric` 也是 `yes`（resourcefullib 内嵌）。

## 9. manual 分母写死

`rate_definition` 里固定：`auto_n = 9`、`manual_n = 35`，`fixed = true`。
`manual_pass` 只算你人工核过的样本；没核的不进分子，也**不改分母**（否则数字随时间漂移）。
报告里同时给“已核样本数”，方便看出 35 里核了几个。

## 10. 覆盖范围声明

- `corpus_v2.md` §0 首行即：**覆盖范围：客户端侧（UI/HUD/QoL/性能/库）；内容层与服务端不在 90% 口径内**。
- `tools/compat_sweep.py` 产出的 `compat.md` 头部同样带这一行。
- `summary.txt` 暂时没有兼容率段（那是 P2 归因器的活），P2 落地时这条声明会一起进 summary 头部，避免裸报 90%。

## 11. distancetransform

`distancetransform` 与 `distance-transform` 两个 slug 都是 **404**，没能确认是改名重发。
处置：从 L3 排除名单删除（项目已不存在，不属于“L3 不做”），`corpus_v2.md` §10 记一句，
避免下次有人拿它当兼容性案例。

---

## 开跑前 3 项预检（2026-11-04）

### P1. `SL_MODS_DIR` 未设时行为不变（实跑验证）

`python tools/compat_sweep.py --live` —— 不设 `SL_MODS_DIR`，用实例现有 `mods/` 跑完整 launch：

- 11 个 jar：connector / FFAPI / companion / Sodium(NeoForge) / JEI / Jade / JadeAddons / ModMenu / Comforts / AppleSkin / Trinkets
- 结果 `pass`：`runtime_fresh=True`、强证据命中、`level_dat_touched=True`、退出码 0
- 报告重新渲染：`运行时数据 … ✓ 本次启动`、`退出码 0`、`mods.json count=67`、`加载问题 0`
- 结论：新增的 `SL_MODS_DIR` 分支在未设时完全走原路径（`Paths.mods` 返回 `instance/mods`），报告与基线一致。

**过程中修掉了评测台的一个真 bug**：原来超时/判定后杀的是 `python superloader.py` 包装器，
游戏（java）成了孤儿继续跑，而且包装器被杀 → 报告不再渲染（第一次 `--live` 拿到的是
昨天 22:19 的旧 summary）。现在改为按“启动时间之后新出现的 java/javaw 进程”优雅 taskkill，
再等包装器自己退出并渲染报告；包装器超时才强杀。实测第二次 `--live` 退出码 0、报告新鲜。

### P2. 带前置的样本闭包拼装（zoomify）

`python tools/compat_sweep.py --prepare --sample zoomify` → 6 个 jar：

```
connector-2.0.0-beta.17+1.21.1-full.jar
forgified-fabric-api-0.116.15+2.3.6+1.21.1.jar
superloader_companion-0.4.1.jar
fabric-language-kotlin-1.14.2+kotlin.2.4.21.jar   （直接前置，Fabric 构建）
yet_another_config_lib_v3-3.8.2+1.21.1-fabric.jar（直接前置，Fabric 构建；原生版不装）
zoomify-2.15.2+1.21.1.jar
```

全部通过 sha1 校验。闭包展开正确：zoomify 的两个前置来自闭包而不是运行时模组，
且 yacl 用的是 Fabric 构建（`+1.21.1-fabric`），符合“默认装 Fabric 构建”的政策。

### P3. “进存档”的证据来源（`world_joined` 还没加，现在靠什么）

companion 现在只有 `common_setup` / `load_complete` / `periodic` / `shutdown`，**没有 `world_joined`**。
判定器用客户端日志的**强证据**，任一条命中即算进入世界：

| 级别 | 证据 | 为什么可信 |
|---|---|---|
| 强 A | `LoggerChunkProgressListener: Time elapsed: <n> ms` | 出生点区块加载完成时打印，一次性；没进世界不会出现 |
| 强 B | `Saving chunks for level '<dim>'` | 世界被保存过（按 ESC 退出/自动保存），只可能在进入之后 |
| 弱 | `AdvancementTree: Loaded <n> advancements`、`Preparing spawn area` | 只记录，不作为判定依据（失败前也可能打印） |

旁证：记录 `saves/新的世界/level.dat` 的 mtime 是否推进。实测（2026-11-04 12:06 原生 Sodium 那轮）：
强证据 `Time elapsed: 273 ms`、弱证据 `Loaded 1465 advancements`、`level.dat` 被写。

局限（写在这里，避免以后误读）：这是**日志启发式**，不是游戏内事件。如果某个 mod 让日志变了格式，
判定会退化为 `no_world_join`（宁可误判 fail，不误判 pass）。等 companion 的 `world_joined` 事件落地后，
这两条降级为交叉校验。

---

## 本轮仍未做（按顺序）

1. 首轮实测结果回填（auto 9 + 反例 2 的 `actual_layer`）——见下一节。
2. companion 加 `world_joined` 事件，替换上面的日志启发式。
3. 归因器（P2）+ summary 里的兼容结论段。

---

## 12. 开跑前 3 项预检 + 首轮隔离失效（2026-11-04 12:06–12:26）

### 12.1 预检 1：默认 launch 行为不变（通过，但先踩了一个坑）
第一次 `--live` 拿到的是 **11-03 22:19 的旧 summary**：超时后杀的是 `python superloader.py`
包装器，java 游戏成孤儿继续跑，包装器一死报告不再渲染。
修法：`java_pids_since()` + `stop_game()` 只杀本次启动后出现的 java/javaw，然后
`proc.wait(120)` 让包装器自己退出并渲染。第二次 `--live` 通过：exit 0、11 jar、
`runtime_fresh=True`、强证据 `Time elapsed: 273 ms`、`level_dat_touched=True`、
报告 `✓ 本次启动`、`mods.json count=67`、`加载问题 0`。

### 12.2 预检 2：带前置样本的闭包拼装（通过）
`--prepare --sample zoomify` → 6 个 jar：connector / FFAPI / companion /
`fabric-language-kotlin-1.14.2+kotlin.2.4.21.jar` / `yet_another_config_lib_v3-3.8.2+1.21.1-fabric.jar` /
`zoomify-2.15.2+1.21.1.jar`，sha1 全通过；yacl 用 Fabric 构建符合政策。

### 12.3 预检 3：进存档证据来源（写死，不再含糊）
- 强 A：`LoggerChunkProgressListener: Time elapsed: <n> ms` —— 出生点区块加载完成，一次性；
- 强 B：`Saving chunks for level` —— 世界被保存过；
- 弱（只记录不判定）：`Loaded <n> advancements`、`Preparing spawn area`；
- 旁证：`saves/新的世界/level.dat` mtime 是否推进。
写入 `corpus.json.assembly.join_evidence`。局限：日志启发式，宁可误判 fail；companion 的
`world_joined` 落地后降级为交叉校验。

### 12.4 首轮实测 → 发现隔离根本没生效（本轮最重要的事）
12:16 跑 auto 9，全部 pass；但查 krypton 那轮报告发现：
- `mods.json` 里 krypton `loaded=false`，issue `krypton（krypton-0.2.8.jar）在 mods/ 里，但不在本次 ModList 中`；
- 日志里加载的是实例 `mods/` 的 11 个 jar（sodium / modmenu / comforts / appleskin / trinkets…）。

**根因**：`SL_MODS_DIR` 只改了 Python 侧的 `Paths.mods`（下载与报告扫描用），启动参数仍是
`--gameDir D:\SLData\instances\1.21.1`，FML 扫的是 `gameDir/mods`。mods.compat 从未被游戏读取。
所以那 9 个 pass 是“基线实例进世界成功”，不是“样本进世界成功”。

修法（两层）：
1. **目录交换**：运行前把实例 `mods/` 改名为 `mods.__baseline`，把 `mods.compat/<slug>/` 复制成
   `mods/`；跑完 `finally` 里立即换回。异常中断用 `--restore-mods` 收尾。已验证：krypton 那轮
   `mods.json` 里 sodium 不存在、krypton 存在且 loaded=true、count 52。
2. **判定加门槛**：`pass` 多一个必要条件 `sample_loaded=true`（样本自己的 jar 在本次 ModList 且
   loaded 非空），否则 `fail(sample_not_loaded)`。判定顺序改为
   `fatal_in_log > crash_screen > timeout_no_runtime > sample_not_loaded > no_world_join > pass`。

附带修正：样本 FATAL 后不再空等 `--timeout`（检测到致命行再等 3 秒就收）；run 目录从“每样本一个
时间戳目录”改成“每次调用一个 run_dir，样本子目录在其下”。

### 12.5 反例：原假设被推翻，换了两个真负例
`carpet`（原假设 L2）与 `mixintrace`（原假设 L4）在首轮都 pass——但那轮隔离失效，结论无效；
二者 `expected` 暂改为 `pass` 并标 `hypothesis_falsified`，等修好隔离后重跑再定。
新增两个**可复现**的负例控制（`corpus.json.negative_controls`）：
| 控制 | jar | 预期层 | 实测 |
|---|---|---|---|
| `neg_dep_test` | `logs/dep-test/superloader_dep_test-1.0.0.jar` | L0 | fail(fatal_in_log)：`Error during pre-loading phase ... requires version 99.0.0 or later of fabric_screen_api_v1` |
| `neg_sodium_fabric` | `logs/tmp-mods-backup/[钠] sodium-fabric-0.8.13+mc1.21.1.jar` | L2 | fail(fatal_in_log)：`Mixin apply for mod sodium failed ... Found unexpected argument type float[] at index 2, expected float` |

两个都跑通判定闭环，证明 fatal_in_log 这一档对 L0/L2 有效。

### 12.6 首轮实测结果（`logs/compat/20261104-124552/`）

| 样本 | 判定 | 用时 | sample_loaded | 备注 |
|---|---|---|---|---|
| krypton | pass | ~40 s | yes | 4 jar（含 yacl/night-config） |
| debugify | pass | ~40 s | yes | |
| fastquit | pass | ~40 s | yes | |
| no-resource-pack-warnings | pass | ~40 s | yes | |
| forcecloseworldloadingscreen | pass | ~40 s | yes | |
| lazy-language-loader | pass | ~40 s | yes | 首跑曾因 fml.toml 被写坏 NPE，见 12.7 |
| yosbr | pass | ~40 s | yes | |
| stackdeobf | pass | ~40 s | yes | Connector 重命名成 `_mapped_moj_1.21.1.jar` |
| faster-random | pass | ~40 s | yes | |

**auto 9/9 pass**；全部 `sample_loaded=true`、有强进存档证据、无 FATAL。manual 35 个未测（分母不动）。

负例：`carpet` 在真实隔离下 **fail(L2)**——crash report 点名
`PistonStructureResolver_customStickyMixin#onAddBranchingBlocksCanStickToEachOther`、
`Level_fillUpdatesMixin#updateNeighborsMaybe`，原假设成立；
`mixintrace` **pass**，L4 假设推翻，移入 `hypotheses_falsified`。

### 12.7 判定器又修了两个坑（都是实测暴露的）

1. **样本身份匹配过窄**：`own_jar` 原先按 `install[i].slug` 找，实际字段叫 `id`；
   且 Connector 把 jar 重命名成 `<原名>_mapped_moj_1.21.1.jar`、mod_id 常与 slug 不同
   （`stackdeobf` → `stackdeobfuscator`）。改成三路匹配：原名 / 去掉 `_mapped` 前缀 / jar 内
   `fabric.mod.json` 的 id+provides。修前 stackdeobf 与 lazy-language-loader 被误判
   `sample_not_loaded`。
2. **fml.toml 被写坏会连累下一轮**：早期强杀在启动中段，`config/fml.toml` 留下半截，
   下一轮在 `DisplayWindow.setupMinecraftWindow` 抛
   `NullPointerException ... FMLConfig$ConfigValue.getConfigValue(...) is null`（与样本无关）。
   现在跑前用 `logs/compat/fml.toml.good` 还原一份已知good（首次自动建立备份）。

另外：FATAL 判定优先于 crash_screen（更具体），并在检测到 FATAL 后再等 3 秒收尾，不再空等
`--timeout`；`mods.json` 里 `mixins_failed` 缺失时记 0 而不是 `?`。


