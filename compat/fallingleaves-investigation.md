# fallingleaves `@Invoker` 访问失败 —— 核实报告

日期：2026-11-05
样本：`fallingleaves-1.17.1+1.21.1.jar`（170,056 B，93 条目）
现象：Connector 下 Render thread FATAL
`failed to access class net.minecraft.client.particle.ParticleEngine$MutableSpriteSet from class randommcsomethin.fallingleaves.mixin.SimpleSpriteProviderInvoker`

## 最终处置（用户决定，2026-11-05）

- **移出、不修、不改 jar**：fallingleaves 记为「**L2 / 上游缺陷（发布包丢 accessWidener 键）**」，
  从 `compat/corpus.json` 的 `main` 移入 `excluded_upstream_defects`（manual 分母 35 → 34）。
- **第④条 Fabric 对照不做**：没有 Fabric 实例，且结论不依赖它——无论 Fabric 侧崩不崩，
  都不是 Connector 的重映射问题，也不该由 companion 去改第三方 jar。
- 该项**关闭**，后续不再投入。

## 结论（先给结果）

**前提被推翻，簇不成立，本次不写补丁。**

1. Connector 的 `@Invoker` target **已经被正确重映射**。在 Connector 产出的 mapped jar
   （`D:\SLData\instances\1.21.1\.cache\connector\[落叶] fallingleaves-1.17.1+1.21.1_mapped_moj_1.21.1.jar`）里，
   注解与接口方法签名都是 `net.minecraft.client.particle.ParticleEngine$MutableSpriteSet`（mojang 内部类名），
   不再是 `class_702$class_4090`。所以这不是 mapping miss。
2. 真正的缺口是**访问权限**：`ParticleEngine$MutableSpriteSet` 是 **package-private** 类，
   而 fallingleaves 的 `fabric.mod.json` **没有 `accessWidener` 键** → 它的 `.aw` 文件是死文件，
   Fabric 与 Connector 都不会加载 → 模组包内的接口引用 `net.minecraft...` 包内类 → `IllegalAccessError`。
3. 上游 `build.gradle` 里明明配了 `loom { accessWidenerPath = ... }`，但 Modrinth 上发布的 1.17.1 包丢了
   `accessWidener` 键（Loom 正常会在 remapJar 阶段自动写入）。这是**上游打包问题**，不是 Connector 的坑。

## 逐条核实

| # | 命题 | 判定 | 证据 |
|---|---|---|---|
| ① | `SimpleSpriteProviderInvoker` 是 `@Invoker` | **成立** | `javap -v`：`public interface randommcsomethin.fallingleaves.mixin.SimpleSpriteProviderInvoker`，常量池含 `org/spongepowered/asm/mixin/gen/Invoker`，方法 `public static net.minecraft.class_702$class_4090 init();` |
| ② | target 是 `ParticleManager$SimpleSpriteProvider`(Yarn) = `ParticleEngine$MutableSpriteSet`(Mojang) | **成立** | 类注解 `@Mixin(value=[class Lnet/minecraft/class_702$class_4090;])`；tiny `CLASS ... class_702 ... ParticleEngine`、`class_4090 ... MutableSpriteSet` |
| ③ | `fabric.mod.json` 没有 `accessWidener` 键 | **成立** | 完整打印 fmj 只有 `schemaVersion/id/version/name/description/authors/contact/mixins/depends`；`accessWidener`、`aw`、`access_widener` 三种写法都不存在；上游 GitHub（分支 1.21）同一文件也没有 |
| ④ | 若 `.aw` 没被加载，它在 Fabric 上如何工作 | **无法判断（存疑）** | 静态证据不支持"Fabric 上能跑"：Fabric Loader 只从 `fabric.mod.json` 的键读 AW（`V1ModMetadataParser` 是唯一引用 `accessWidener` 字符串的 loader 类），不自动扫 `*.accesswidener`；Mixin 的 `AccessorInfo`/`AccessorGenerator` 里没有任何放宽类访问权限的逻辑。需要真实 Fabric 实例做对照才能确认；本项目没有 Fabric 环境 |
| ⑤ | `NativeImageAccessor`/`SpriteContentsAccessor` 的 target 不是内部类 | **成立** | 二者 `@Mixin(class_1011 = NativeImage)`、`@Mixin(class_7764 = SpriteContents)`，都是顶层 **public** 类；只有 `SimpleSpriteProviderInvoker` 的 target 是内部类且 package-private |
| ⑥ | `core/suspects.py` 在 `stale=true` 时的行为 | **成立（旧版确实看不到）** | 旧版 `build_suspects()` 只接收 `console_log`，`scan_console()` 只读该文件；完全不读 `launch.json` 的 `fatal[]`，也没有 `HARD_DEP`/`Resolution failed` 模式 → stale 或只跑 report 时 `suspects=0` |

补充的运行时证据（用于排除"映射错"这条假设）：

- `javap -p -cp client-1.21.1-...-srg.jar 'net.minecraft.client.particle.ParticleEngine$MutableSpriteSet'`
  → `class net.minecraft.client.particle.ParticleEngine$MutableSpriteSet implements SpriteSet`，**没有 `public`**，构造器也包私有。
- mapped jar 里的 refmap、`.accesswidener` 文件都原样保留，`fabric.mod.json` 仍无 `accessWidener` 键。
- Connector 自己的 AW 管线是完整的：jar 里有 `org/sinytra/connector/transformer/transform/AccessWidenerTransformer`、
  `reloc/net/fabricmc/classtweaker/...`。声明了 AW 的 mod（sodium / carpet / language-reload / repurposed_structures /
  the_bumblezone）在实例里都正常，只有 fallingleaves 是"有 .aw 文件、无键"。

## 为什么现在不写补丁

- 桥接层唯一能做的动作是"替 mod 往 `fabric.mod.json` 里补 `accessWidener` 键"——那等于**改第三方 jar 的元数据**，
  违反项目原则（不改第三方产物、不按 mod 特判）。而且自动推断"该给它补哪条 AW"本质是猜意图，猜错会把
  访问权限开给整个包，风险比不修大。
- Connector 的 AW 管线本身没问题（见上），所以不存在"Connector 没实现 → 我们补桥"的缺口。
- 反过来说，如果真要在我们这边做，属于"给上游打包错误打补丁"，收益只有 1 个 mod，不符合"一个补丁覆盖一类调用"。

## 该做什么

1. **上游 issue**：fallingleaves 的发布 jar 缺 `accessWidener` 键（`build.gradle` 已配 loom，说明是发布流程丢字段）。
   这是能一次修好、对所有用户生效的正确修法。
2. **本地记为已知不支持**：`compat/corpus.json` 的 exceptions 已追加说明；`suspects.json` 会以
   `fatal_in_log` / layer `L2` 报出来（见第四步修复），不会再静默。
3. 如果以后拿到 Fabric 实例，做一次对照：同一 jar 在 Fabric 上是否也崩。
   - 若崩 → 彻底确认是 mod 打包问题，关闭该线索；
   - 若不崩 → 说明 Fabric 侧另有放宽机制，需要单独研究；但即便那样也不是 Connector 的重映射问题，
     而是"Fabric 侧有、Connector 侧没有"的隐式行为，属于新的、更大的题目。

## 附：扫描表与 suspects 修复

- `compat/invoker_inner_target_scan.md`：22 个 jar / 53 个 mixin 类 / 64 条内部类 target，其中 20 条 target 是
  package-private；除 fallingleaves 外，其余全部声明了 `accessWidener`。
- `core/suspects.py` 两个缺陷已修（独立于本线索）：
  - 新增 `fatal` 参数，`stale=true` / 无 console 时从 `launch.json` 的 `fatal[]` 补抓致命行并推层；
  - 新增 Fabric Loader 依赖失败来源（`HARD_DEP_NO_CANDIDATE` / `HARD_DEP` / `Resolution failed` /
    `Some of your mods are incompatible`），归 `L0`，证据取 `- mod <name> (<id>) ... requires ...` 行。
  - 回放：`connectiblechains`（真实日志，L0）与 `fallingleaves`（只给 fatal 行，L2）均 PASS。
