# minihud 崩溃调查（2026-11-05）

## 现象

`crash-2026-11-05_18.41.34-client.txt`，`Description: Bootstrap`，退出码 -1：

```
Caused by: org.spongepowered.asm.mixin.injection.throwables.InjectionError: Critical injection failure:
  Multi-argument modifier method loadCustomText(Args;Map$Entry;)V
  in mixins.minihud.json:client.MixinLanguage from mod minihud failed injection check,
  (0/1) succeeded. Scanned 0 target(s). No refMap loaded.
```

栈：`CreativeModeTabs.validate` → `TranslatableContents.decompose` → 反射加载 → 类加载 `Language` → Mixin 应用失败。

## 证据

1. minihud 的 `mixins.minihud.json` **没有 refmap**（整个 malilib 家族都不带 refmap，直接用 intermediary 名），所以 `MixinLanguage` 里写的是
   `@ModifyArgs(method="method_29425(Ljava/io/InputStream;Ljava/util/function/BiConsumer;)V", at=@At(INVOKE, target="Ljava/util/function/BiConsumer;accept(Ljava/lang/Object;Ljava/lang/Object;)V"))`。
2. Connector 的重映射是对的：mapped jar 里同一条注解已经是
   `method="loadFromJson(Ljava/io/InputStream;Ljava/util/function/BiConsumer;)V"`，`@Mixin` 也换成了 `Lnet/minecraft/locale/Language;`。
   → **不是 refmap 缺口、不是 mapping 漏翻**。
3. NeoForge 21.1.265 的 `neoforge-21.1.265-client.jar` 里 `net/minecraft/locale/Language` 被打过补丁：
   - 2 参 `loadFromJson(InputStream, BiConsumer)` 现在只有一个 `invokedynamic` + 转发到 **3 参** `loadFromJson(InputStream, BiConsumer, BiConsumer<Component>)`；
   - `BiConsumer.accept` 的真实调用点（offset 128）搬到了 3 参重载里；
   - 于是 minihud 的 `@ModifyArgs` 在 2 参方法体里扫到 **0 条** `INVOKE BiConsumer;accept` → 注入失败 → `required=true` 的 mixin 让启动直接失败。
4. Connector 里没有任何 `Language`/`loadFromJson` 的补丁（扫 connector jar 0 命中），所以运行时用的就是 NeoForge 打过的版本。

## 判定

- 层级：**L2（目标方法被 NeoForge 改写）**，与 replaymod 同一族（NeoForge 改了方法体/调用点，Connector 没有对应 patch）。
- 不是 mod 自身 bug（Fabric 上 2 参方法里确实有 `accept`，能注入）；不是 refmap 缺口。
- 簇：malilib 家族四个 jar 里只有 minihud 有 `Language` 的 mixin（litematica 有 4 个普通类用到 `Language`，不是 mixin）。

## 处置

- 短期：把 `minihud-fabric-1.21-0.32.60.jar` 移出 `mods/`，单独验证 malilib / litematica / tweakeroo 能否进存档。
- 治本：需要 Connector 加一条 mixin patch，把注入点从 2 参 `loadFromJson` 迁到 3 参重载（保留两个 consumer 的语义），属于上游 issue/PR；companion 不能改别的 mod 的 class 注解。
- 记录：`compat/corpus.json.exceptions`、`HANDOFF.md` 决策 34。
