# replaymod 崩溃调查（2026-11-05）

## 结论

**不是 replaymod 自身在 1.21.1 的 bug，也不是 refmap 缺口。** 是 Connector 在
"目标方法已被 NeoForge 移走"时的注解重定位产生了错误的 `@At`：

- 原始（replaymod 1.21-2.6.28）：
  `@Inject(method="render", at=@At(value="INVOKE", target="Lnet/minecraft/client/gui/screen/Screen;renderWithTooltip(Lnet/minecraft/client/gui/DrawContext;IIF)V", shift=AFTER))`
- Connector 产物（`.cache/connector/replaymod-..._mapped_moj_1.21.1.jar`）：
  `method=["Lnet/minecraft/client/renderer/GameRenderer;render(Lnet/minecraft/client/DeltaTracker;Z)V"]`，
  `at=[@At(value="INVOKE", target="Lnet/minecraft/client/DeltaTracker;getGameTimeDeltaTicks()F")]`
  —— target 换成了无关调用，**`shift=AFTER` 丢失**。

后果：handler 被插到 `render()` 开头就执行的 `getGameTimeDeltaTicks()` 调用上，每帧都会跑；
overlay 阶段此时还没有 `GuiGraphics`，`VanillaGuiScreen$EventHandler.onGuiRender(GuiGraphics, float)`
第一句就是 `stack.flush()`（无 null 检查）→ NPE。

## 证据链

1. 崩溃报告 `crash-2026-11-05_13.40.40-client.txt`：
   `Description: Rendering overlay`，
   `Cannot invoke "GuiGraphics.flush()" because "stack" is null`，
   栈顶 `VanillaGuiScreen$EventHandler.onGuiRender` ← `PostRenderScreenCallback` ←
   `GameRenderer.handler$zkp000$replaymod$postRenderScreen` ← `GameRenderer.render`。
2. `javap -v` 原 jar 的 `MixinGameRenderer`：`@Inject(method="render", at=@At(INVOKE, target=Screen;renderWithTooltip, shift=AFTER))`。
3. `javap -v` mapped jar 的同一个类：target 变成 `DeltaTracker;getGameTimeDeltaTicks()F`，无 shift。
4. `javap -c` NeoForge 21.1.265 的 `GameRenderer.render`：
   原版 offset 741 的 `Screen.renderWithTooltip(GuiGraphics,IIF)V` 已被替换为
   `ClientHooks.drawScreen(Screen, GuiGraphics, int, int, float)`（offset 745），
   而 `getGameTimeDeltaTicks()` 在 offset 288/654/740 都出现（每帧必执行）。
   → 原注入点在这个 NeoForge 版本里**确实不存在**，属 L2 目标迁移。
5. replaymod 自己的 refmap（`mixins.jgui.refmap.json`）里有这条：
   `"...Screen;renderWithTooltip(...)V": "Lnet/minecraft/class_437;method_47413(Lnet/minecraft/class_332;IIF)V"`
   → 在 Fabric 上 Mixin 用 refmap 就能解析到正确方法；Connector 改写注解后又让 refmap key 失配，
   两者叠加才崩。
6. 同类的 `@ModifyArg`（`captureContext`）的 `@At` 在 mapped jar 里**保持原样**（Yarn 名未动），
   运行时靠 refmap 正常解析 —— 说明 Connector 对 `@Inject` 做了额外重写，而 `@ModifyArg` 没有。

## 簇判定

扫 165 个 jar（`mods/*.jar` + `.cache/connector/*.jar`，常量池含 `renderWithTooltip` 或
`GuiGraphics`+`flush`）：chatpatches `ScreenMixin`、cloth-config `GlobalizedClothConfigScreen`、
JEI `ItemStackBatchRenderer`、Jade `DisplayHelper`、sodium `GameRendererMixin`、
midnightlib、lenientdeath 都只是**调用** `GuiGraphics.flush()` 或注入到 `Screen` 自己的方法，
只有 replaymod 的 `MixinGameRenderer` 是在 `GameRenderer.render` 里注入被移走的
`Screen;renderWithTooltip`。**簇只有一个成员**。

## 为什么不在 companion 里修

- Connector 的配置只有 `version` / `hiddenMods` / `globalModAliases` / `enableMixinSafeguard`，
  没有关闭注解重写的开关；connector jar 内也没有可编辑的 mixin patch 资源。
- 要在桥接层修，只能：改 replaymod 的 class 注解（改 jar，不允许），
  或给 companion 加一个 ModLauncher 级 class transformer 去改别人 mixin 类的注解（等于在 companion 里
  硬编码单个 mod 的修补，违反"不特判 mod id"）。
- 正确载体是 **Connector 上游**：这是一次"目标方法迁移"的适配缺口，应该作为一条 mixin patch
  （`GameRenderer.render` 里的 `Screen.renderWithTooltip` → `ClientHooks.drawScreen` 调用点，
  保留 `shift=AFTER` 语义）提交给 Connector；或者至少让 Connector 在无法解析时**不要**改写成无关 target。

## 已提交给上游的 issue 草稿（要点）

- 版本：Connector 2.0.0-beta.17+1.21.1 / NeoForge 21.1.265 / 1.21.1
- mod：replaymod 1.21-2.6.28（Fabric，无 NeoForge 版）
- 现象：`@Inject` 的 `@At(INVOKE target=Screen;renderWithTooltip, shift=AFTER)` 被重写成
  `@At(INVOKE target=DeltaTracker;getGameTimeDeltaTicks)` 且 shift 丢失，导致 handler 在 overlay
  阶段每帧执行、`GuiGraphics` 为 null 时 NPE。
- 原因：NeoForge 把 `Screen.renderWithTooltip` 调用替换成 `ClientHooks.drawScreen`，
  Connector 的目标迁移没有对应 patch。
- 期望：为这个注入点加 patch（或至少保留原 `@At` 让它按 refmap 失败可见）。
