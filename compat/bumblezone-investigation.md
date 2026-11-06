# the_bumblezone 崩溃调查（2026-11-05）

**结论**：`the_bumblezone-7.17.3+1.21.1-fabric.jar` 在 **Connector 转换 jar 阶段**触发 Connector
（sinytra adapter）自身的空指针，崩在任何模组代码运行之前。mod 的 mixin 注解没有写错，
companion / FFAPI 也接不住 —— 只能上游修，或短期把这个 mod 移出。

## 1. 现象

`crash-reports/crash-2026-11-05_19.07.18-client.txt` 的表层异常是 Sodium 的掩盖式报错：

```
Description: Rendering overlay
java.lang.RuntimeException: Sodium's config could not be found; the game is in a broken state
  most likely caused by an earlier error from another mod.
    at net.caffeinemc.mods.sodium.client.config.ConfigManager.registerConfigs(ConfigManager.java:119)
```

真因在它之前 5 秒的 `latest.log`：

```
[19:07:10.344] [pool-3-thread-7/ERROR] [transformer.jar.JarTransformInstance/]:
  Encountered error while transforming jar file
  D:\SLData\instances\1.21.1\mods\the_bumblezone-7.17.3+1.21.1-fabric.jar
java.lang.RuntimeException: Failed to execute task
  com/telepathicgrunt/the_bumblezone/mixin/fabric/entity/LivingEntityMixin.class
    at ...JarTransformInstance.transformJar(JarTransformInstance.java:115)
    ...
Caused by: java.util.concurrent.ExecutionException: java.lang.NullPointerException
    ...
Caused by: java.lang.NullPointerException: Cannot invoke
  "org.sinytra.adapter.env.ctx.TargetPair.methodNode()" because "dirtyTarget" is null
    at org.sinytra.adapter.patch.resolver.special.ResolverSyntheticInstanceof.resolve(ResolverSyntheticInstanceof.java:54)
    at org.sinytra.adapter.patch.PipelineMethodTransformer.execute(PipelineMethodTransformer.java:92)
    at org.sinytra.adapter.patch.Patcher.processMixin(Patcher.java:131)
    at org.sinytra.adapter.patch.transformer.MixinPatchTransformer.process(MixinPatchTransformer.java:157)
```

随后 `[19:07:15.946] [Render thread/FATAL] Error during pre-loading phase: [Connector] Error transforming file
the_bumblezone-7.17.3+1.21.1-fabric.jar`，该 mod 被标记为 broken，Sodium 在初始化屏幕阶段连带崩溃。

## 2. 为什么判定是 Connector 的 bug

`ResolverSyntheticInstanceof.resolve(...)` 的字节码（`javap -c -p`，connector-2.0.0-beta.17）：

```
19: invokevirtual  Recipe.getDirtyTarget()   // 可能返回 null
22: astore 4                                  // local 4 = dirtyTarget
...
99: aload 4
101: invokevirtual TargetPair.methodNode()    // ← 这里直接解引用，没有 null 检查
```

`dirtyTarget` 为空时必然 NPE。也就是说，adapter 在“为这条 mixin 注解生成 patch”时拿不到
NeoForge 侧的方法节点，却没有走 `ResolutionResult.pass()` 的兜底路径 —— 是 adapter 的健壮性缺口，
不是 bumblezone 用了非法注解（同样的注解在 Fabric 上正常，`ResolverSyntheticInstanceof` 也只处理
`INVOKE` 注入点、`skipInsnComparison` 分支）。

## 3. bumblezone 那条 mixin 长什么样

`com/telepathicgrunt/the_bumblezone/mixin/fabric/entity/LivingEntityMixin`（`@Mixin(class_1309, priority=1200)`）：

| handler | 注解 | 目标（intermediary → 语义） |
|---|---|---|
| `bumblezone$onEntityVisibility` | `@ModifyReturnValue(method="method_18390", at=@At("RETURN"))` | `getVisibilityPercent(Entity)` |
| `bumblezone$onTick` | `@Inject(method="method_5773", at=@At("TAIL"))` | `Entity.tick()` |
| `bumblezone$onHurt` | `@Inject(method="method_5643", at=@At("HEAD"), cancellable=true)` | `hurt(DamageSource,F)` |
| `bumblezone$onActualHurt` | `@Inject(method="method_6074", at=@At(INVOKE, target="class_1309.method_6132(class_1282,F)F", ordinal=0))` | `actuallyHurt` |
| `bumblezone$breathing` | `@ModifyExpressionValue(method="method_5670()V", at=@At(INVOKE, target="class_1309.method_5777(class_6862)Z"))` | `baseTick()` 里的 `isEyeInFluid` |
| `bumblezone$correctSlotForItems` | `@ModifyReturnValue(method="method_32326", at=@At("RETURN"))` | `getSlotForHand` 之类 |
| `bumblezone$customFluidJumpWeaker` | `@WrapOperation(method="method_6007()V", at=@At(INVOKE, target="class_1309.method_5861(class_6862)D", ordinal=1), require=0)` | `aiStep()` 里的 `getFluidHeight` |

全部是标准 Mixin / MixinExtras 用法，没有自定义插件、没有 access widener 依赖。

## 4. 为什么 companion 修不了

- 失败发生在 **Connector 的 jar 转换阶段**（`JarTransformInstance.transformJar`），早于 FML 加载 mod、
  早于 companion 的任何入口；
- Connector 配置只有 `version` / `hiddenMods` / `globalModAliases` / `enableMixinSafeguard`，
  **没有关闭 adapter patch 的开关**；
- 唯一“能修”的位置是 Connector 的 adapter：在 `dirtyTarget == null` 时退回 `pass()`，
  或者为 `INVOKE` + synthetic-instanceof 场景补齐 neoForge 侧目标解析；
- 1.21.1 上 Connector 最新就是 `2.0.0-beta.17+1.21.1`（2026-08-15），之后的新版本都是 MC 26.x
  （`3.0.0-beta.*` / `3.1.0-beta.*`），升级不了。

## 5. 处置

1. **短期**：`the_bumblezone-7.17.3+1.21.1-fabric.jar` 移出 `mods/`（建议放 `logs/removed-mods/`），
   实例即可恢复；它属于 `content_phase2` 内容组，不影响主样本口径。
2. **治本**：给 Sinytra/Connector 提 issue（草稿见下）；如果愿意花时间，可以先把失败范围缩到
   “哪个 handler 的注解触发 adapter NPE”（做法：复制 jar 到 `logs/` 做诊断副本，逐个在 mixin config 里
   裁掉类/方法，跑 launch 观察转换日志），把结论补进 issue。
3. 报告侧已修：`core/suspects.py` 现在能抓到这类“转换期失败”（来源 `mixin_transform_failed`，
   归 L2，证据取 `Caused by:` / `Failed to execute task`），本次已报出 `the_bumblezone`。

## 6. Connector issue 草稿

> **Title**: `ResolverSyntheticInstanceof` NPEs when `Recipe.getDirtyTarget()` is null (jar transform aborts)
>
> **Environment**: Connector `2.0.0-beta.17+1.21.1`, NeoForge `21.1.265`, MC `1.21.1`, Windows, Java 25
>
> **Repro**: put `the_bumblezone-7.17.3+1.21.1-fabric.jar` in `mods/` and launch. Connector fails while
> transforming the jar:
> `Failed to execute task .../LivingEntityMixin.class` →
> `NullPointerException: Cannot invoke "TargetPair.methodNode()" because "dirtyTarget" is null`
> at `ResolverSyntheticInstanceof.resolve(ResolverSyntheticInstanceof.java:54)`.
>
> **Cause**: in `resolve(MixinContext, Recipe)`, the result of `Recipe.getDirtyTarget()` is used without a
> null check (bytecode: `astore 4` … `aload 4; invokevirtual TargetPair.methodNode()`), unlike the
> neighbouring `findInjectionTargetInsn` branch which falls back to `ResolutionResult.pass()`.
>
> **Suggested fix**: return `ResolutionResult.pass()` (or skip the resolver) when `dirtyTarget == null`,
> and let later pipeline stages handle the unmatched target.
>
> **Attachment**: the mixin is standard (`@Inject` on `INVOKE`, `@ModifyExpressionValue` on
> `isEyeInFluid`, `@WrapOperation` with `ordinal=1`, `priority=1200`); no custom Mixin plugin.
