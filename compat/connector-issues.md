# Connector 兼容性缺口合集（L2 类，2026-11-05/06）

> **提 issue 用 `compat/issues/` 下的英文草稿**（一个模组一份，按 Connector 官方
> `mod_incompatibility.yml` 模板字段顺序写）。本文件是中文取证附录：原始注解、mapped jar 注解、NeoForge 字节码偏移都在这里，
> 草稿正文里用 `compat/connector-issues.md §N` 指过来就行。

这一批全部是 **L2（目标迁移 / 签名迁移）**：mod 的 mixin 注解没错、Connector 的 refmap 也没错，
是 NeoForge 改了目标方法或类结构之后，Connector 的注解重定位/adapter 没有跟上。
全部**无法在 companion/FFAPI 层修**（要改第三方 jar 的注解或字节码），但都可以给 Connector 提 issue/PR。

## 统一环境

| 项 | 版本 |
| --- | --- |
| Minecraft | 1.21.1 |
| NeoForge | 21.1.265 |
| Connector | 2.0.0-beta.17+1.21.1（当前 1.21.1 最新） |
| Forgified Fabric API | 0.116.15+2.3.6+1.21.1 |
| SuperLoader companion | 0.6.3 |

## 汇总

| # | 案例 | 层 | 一句话根因 | companion 可修 | 详细取证 |
| --- | --- | --- | --- | --- | --- |
| 1 | replaymod | L2 | `@At(INVOKE Screen.renderWithTooltip, shift=AFTER)` 被重写成无关的 `DeltaTracker.getGameTimeDeltaTicks()`，shift 丢失 → 每帧在 GUI 之前触发 | ❌ | `compat/replaymod-investigation.md` |
| 2 | minihud | L2 | NeoForge 把 `Language.loadFromJson` 2 参版改成转发 3 参重载，`INVOKE BiConsumer.accept` 只在 3 参版里 | ❌ | `compat/minihud-investigation.md` |
| 3 | the_bumblezone | L2 | Connector（sinytra adapter）在转换 jar 时 `dirtyTarget` 为 null 未判空 → NPE，崩在任何 mod 代码运行前 | ❌ | `compat/bumblezone-investigation.md` |
| 4 | farmers-delight-refabricated | L2 | NeoForge 把 `CropBlock.getGrowthSpeed` 第一参从 `Block` 改成 `BlockState`，`@ModifyVariable` handler 签名校验失败 | ❌ | 本文件 §4 |
| 5 | friends-and-foes | L2 | NeoForge 枚举扩展（`IExtensibleEnum` / `RuntimeEnumExtender`）消费掉 `MobCategory` 的保留构造器，Fabric 枚举 mixin attach 时目标方法已不存在 | ❌ | `compat/friendsandfoes-investigation.md` |
| 6 | language-reload | L2 | Connector 的 `Language` 补丁改写 `loadFromJson` 调用链，破坏 mod"一次加载只构造一个 Language"的假设 → 字段为 null | ❌ | `compat/languagereload-investigation.md` |

> 说明：6 个案例里 1/2/4/6 是"目标方法还在、但调用点/签名变了"，3 是 adapter 健壮性 bug，5 是 NeoForge 新机制与 Fabric 枚举 mixin 的结构性冲突。

---

## 1. replaymod：`@At` 被重定位到无关调用，`shift=AFTER` 丢失

**Mod**：`replaymod-1.21-2.6.28.jar`（纯 Fabric，无 NeoForge 构建）

**复现**：进世界后模组初始化时/渲染时崩（`crash-2026-11-05_13.40.40-client.txt`）：

```
Cannot invoke "net.minecraft.client.gui.GuiGraphics.flush()" because "stack" is null
  at VanillaGuiScreen$EventHandler.onGuiRender(VanillaGuiScreen.java:232)
  at PostRenderScreenCallback.lambda$static$0(PostRenderScreenCallback.java:15)
  at GameRenderer.handler$zkp000$replaymod$postRenderScreen(GameRenderer.java:3814)
```

**原始注解**（`MixinGameRenderer`）：

```java
@Inject(method = "render",
        at = @At(value = "INVOKE",
                 target = "Lnet/minecraft/client/gui/screen/Screen;renderWithTooltip(Lnet/minecraft/client/gui/DrawContext;IIF)V",
                 shift = At.Shift.AFTER))
```

**Connector 产物**（`.cache/connector/replaymod-..._mapped_moj_1.21.1.jar`）：

```java
@Inject(method = "Lnet/minecraft/client/renderer/GameRenderer;render(Lnet/minecraft/client/DeltaTracker;Z)V",
        at = @At(value = "INVOKE",
                 target = "Lnet/minecraft/client/DeltaTracker;getGameTimeDeltaTicks()F"))   // shift 丢失
```

**为什么错**：NeoForge 21.1 的 `GameRenderer.render` 不再调用 `Screen.renderWithTooltip`，改成
`net.neoforged.neoforge.client.ClientHooks.drawScreen(...)`（`neoforge-21.1.265-client.jar` 字节码 offset 745）。
`getGameTimeDeltaTicks()` 在每帧都会执行（offset 288/654/740），于是 handler 在 GUI 渲染之前就被调用，
`context` 还是 null → NPE。

**建议修法**：目标调用点消失时不要静默改到"最近的可匹配调用"；要么保留注解原样让 Mixin 报清晰的
`target not found`，要么按 NeoForge 的等价调用（`ClientHooks.drawScreen`）重定位并保留 `shift`。

---

## 2. minihud：`Language.loadFromJson` 2 参版被改成转发 3 参

**Mod**：`minihud-fabric-1.21-0.32.60.jar`（malilib 家族，纯 Fabric）

**复现**：启动即崩（`crash-2026-11-05_18.41.34-client.txt`）：

```
InjectionError: Critical injection failure: Multi-argument modifier method loadCustomText(Args;Map$Entry;)V
  in mixins.minihud.json:client.MixinLanguage from mod minihud failed injection check,
  (0/1) succeeded. Scanned 0 target(s). No refMap loaded.
```

**注解**：

```java
@ModifyArgs(method = "method_29425(Ljava/io/InputStream;Ljava/util/function/BiConsumer;)V",
            at = @At(value = "INVOKE", target = "Ljava/util/function/BiConsumer;accept(Ljava/lang/Object;Ljava/lang/Object;)V"))
```

**原因**：NeoForge 21.1.265 的 `Language.loadFromJson(InputStream, BiConsumer)` 只剩
`invokedynamic` + `invokestatic loadFromJson(InputStream, BiConsumer, BiConsumer)` 转发；
真正的 `BiConsumer.accept` 在 **3 参重载** offset 128。vanilla 里 accept 在 2 参版 offset 102。

**建议修法**：检测到目标方法体被改成转发时，把注入点迁到实际实现的重载（或让 adapter 识别转发链）。

---

## 3. the_bumblezone：adapter 转换时 `dirtyTarget` NPE

**Mod**：`the_bumblezone-7.17.3+1.21.1-fabric.jar`

**复现**：启动即崩（`crash-2026-11-05_19.07.18-client.txt`）；表层是 Sodium 的掩盖式报错，
真因在 `latest.log`：

```
Encountered error while transforming jar file ...the_bumblezone-7.17.3+1.21.1-fabric.jar
Failed to execute task com/telepathicgrunt/the_bumblezone/mixin/fabric/entity/LivingEntityMixin.class
Caused by: java.lang.NullPointerException: Cannot invoke "org.sinytra.adapter.env.ctx.TargetPair.methodNode()"
  because "dirtyTarget" is null
  at org.sinytra.adapter.patch.resolver.special.ResolverSyntheticInstanceof.resolve(ResolverSyntheticInstanceof.java:54)
```

**原因**：`ResolverSyntheticInstanceof.resolve` 在 `Recipe.getDirtyTarget()` 为 null 时直接
`dirtyTarget.methodNode()`，没有判空/没有降级；相邻的 `findInjectionTargetInsn` 分支是有 `ResolutionResult.pass()` 兜底的。

**建议修法**：判空后走 `pass()`/跳过该 patch，不要整轮 transform 失败（一个可选 patch 出错不该让整个 mod 加载失败）。

---

## 4. farmers-delight-refabricated：`@ModifyVariable` handler 签名与新参数类型不匹配

**Mod**：`FarmersDelight-1.21.1-3.3.6+refabricated.jar`

**复现**：启动即崩（`crash-2026-11-05_19.52.58-client.txt`）：

```
Mixin apply for mod farmersdelight failed farmersdelight.mixins.json:refabricated.CropBlockMixin
InvalidInjectionException: @ModifyVariable handler has an invalid signature.
  Found unexpected argument type net.minecraft.world.level.block.Block at index 1,
  expected net.minecraft.world.level.block.state.BlockState.
  Handler signature: (F LBlock; LBlockGetter; LBlockPos;)F
  Expected signature: (F LBlockState; LBlockGetter; LBlockPos;)F
```

**注解**：

```java
@ModifyVariable(method = "method_9830", at = @At(value = "LOAD", ordinal = 1))
private static float farmersdelightrefabricated$modifyGrowthSpeedForNonFarmland(float, Block, BlockGetter, BlockPos)
```

**原因**：vanilla `CropBlock.getGrowthSpeed` 是 `(Block, BlockGetter, BlockPos)`，NeoForge 改成了
`(BlockState, BlockGetter, BlockPos)`（第一参类型替换）。Connector 的 adapter 支持参数**增删/重排**
（`ParametersProcessor` / `ParametersDiff`），但不支持**类型替换**，所以 handler 签名对不上。

**建议修法**：参数类型变化时同步改写 handler 的局部变量类型/描述符（本例是 `Block` → `state.getBlock()`），
或在 `require=0` 时降级为 warn 而不是硬失败。

---

## 5. friends-and-foes：NeoForge 枚举扩展吃掉保留构造器，Fabric 枚举 mixin attach 失败

**Mod**：`friendsandfoes-fabric-5.0.4+mc1.21.1.jar`（Modrinth 无 NeoForge 构建）

**复现**：启动即崩（`crash-2026-11-05_20.05.26-client.txt`）：

```
MixinTransformerError: An unexpected critical error was encountered
Caused by: MixinPreProcessorException: Attach error for friendsandfoes-fabric.mixins.json:AddCustomSpawnGroupMixin
  during activity: [Attach method -> <init>(Ljava/lang/String;ILjava/lang/String;IZZI)V]
Caused by: java.lang.NullPointerException: Cannot invoke "ClassInfo$Method.isUnique()" because "method" is null
```

**原因**：`AddCustomSpawnGroupMixin` 是枚举 mixin（`extends java.lang.Enum`，`@Mixin(MobCategory.class)`），
`<clinit>` 用 7 参构造器 `(String,int,String,int,Z,Z,I)` 创建新常量。NeoForge 的 `MobCategory` 实现了
`IExtensibleEnum`，该 7 参构造器是 NeoForge 的**保留构造器**，`RuntimeEnumExtender` 在运行期消费/移除它，
Mixin attach 时目标方法已不存在 → Mixin 内部 NPE（而不是清晰报错）。

**建议修法**：把 Fabric 枚举 mixin 的"新增常量"转成 NeoForge 的 `IExtensibleEnum` 扩展
（`RuntimeEnumExtender`/`EnumExtender` 路径），或至少在 attach 失败时给出"目标构造器不存在"的明确错误。

---

## 6. language-reload：构造顺序假设被 `Language` 补丁打破

**Mod**：`language-reload-1.7.6+1.21.1.jar`

**复现**：在创造模式物品栏 / JEI 搜索框输入时崩（`crash-2026-11-05_20.24.47-client.txt`）：

```
Cannot invoke "java.util.Map.get(Object)" because "this.separateTranslations" is null
  at ClientLanguage.languagereload_get(ClientLanguage.java:554)
  at TranslatableContents.getOverriddenTranslations(TranslatableContents.java:1056)
```

**原因**：mod 的 `TranslationStorageMixin` 假设一次加载只构造一个 `Language`：
`onLoad` 填静态表 → `Language.<init>` TAIL 消费并置空。Connector 的 `Language` 补丁改写
`loadFromJson` 调用链后，第二个 `ClientLanguage` 构造时静态表已为 null，字段保持 null；
`languagereload_get` 又没有 null 兜底。

**建议修法**（任一）：
- Connector 保持 2 参 `loadFromJson` 的调用链不被改写（更根本）；
- 或 mod 侧给 `languagereload_get` 加 null 兜底（上游一行修复）。

---

## 提 issue 需要附的信息

对每个案例，附上：

1. 环境表（本文件顶部）；
2. `crash-reports/...txt` 的崩溃头 + 相关栈；
3. `latest.log` 里 `Encountered error while transforming jar file` / `Mixin apply for mod ... failed` 段落；
4. `.cache/connector/<mod>_mapped_moj_1.21.1.jar` 里对应 mixin 类的注解（`javap -v` 片段）与原始 jar 的注解对照；
5. NeoForge 侧目标类的字节码证据（方法描述符/常量池），例如本文件 §1 的 `ClientHooks.drawScreen`。

提交地址：<https://github.com/Sinytra/Connector/issues>（先用搜索确认没有重复 issue）。
