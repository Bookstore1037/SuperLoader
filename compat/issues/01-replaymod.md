<!-- Suggested title:
[1.21.1] ReplayMod 2.6.28 crashes when joining a world: Connector rewrites @At(Screen.renderWithTooltip, shift=AFTER) to DeltaTracker.getGameTimeDeltaTicks()
-->

### Mod Name

ReplayMod

### Mod Homepage

https://modrinth.com/mod/replaymod

### Minecraft version

1.21.1 (LTS)

### Describe the bug

With Connector, joining a singleplayer world with ReplayMod installed crashes on the render thread with:

```
java.lang.NullPointerException: Cannot invoke "net.minecraft.client.gui.GuiGraphics.flush()" because "stack" is null
    at com.replaymod.lib.de.johni0702.minecraft.gui.versions.VanillaGuiScreen$EventHandler.onGuiRender(VanillaGuiScreen.java:232)
    at com.replaymod.lib.de.johni0702.minecraft.gui.versions.callbacks.PostRenderScreenCallback.lambda$static$0(PostRenderScreenCallback.java:15)
    at net.minecraft.client.renderer.GameRenderer.handler$zkp000$replaymod$postRenderScreen(GameRenderer.java:3814)
    at net.minecraft.client.renderer.GameRenderer.render(GameRenderer.java:1081)
```

The mod itself is fine on Fabric: it registers a `postRenderScreen` callback with
`@Inject(method = "render", at = @At(value = "INVOKE", target = "Lnet/minecraft/client/gui/screen/Screen;renderWithTooltip(Lnet/minecraft/client/gui/DrawContext;IIF)V", shift = At.Shift.AFTER))`
and stores the `GuiGraphics` instance in a `@Unique` field from a matching `@ModifyArg`. The callback then calls `GuiGraphics.flush()` on it.

Inside the Connector-transformed jar, that annotation is no longer the original one. `MixinGameRenderer.postRenderScreen` comes out as:

```
method  = "Lnet/minecraft/client/renderer/GameRenderer;render(Lnet/minecraft/client/DeltaTracker;Z)V"
at      = @At(value = "INVOKE", target = "Lnet/minecraft/client/DeltaTracker;getGameTimeDeltaTicks()F")
```

Two things went wrong at once:

1. the `@At` target was replaced with `DeltaTracker.getGameTimeDeltaTicks()`, which is an unrelated call near the top of
   `GameRenderer.render` (vanilla 1.21.1 client classes: offset 289, before any GUI work), and
2. `shift = AFTER` was dropped.

As a result the handler runs on every frame *before* the screen is rendered, the `@Unique` `GuiGraphics` field is still `null`, and
`VanillaGuiScreen$EventHandler.onGuiRender` calls `stack.flush()` without a null check → NPE → crash.

On NeoForge 21.1.265 the original target does not exist any more either: `GameRenderer.render` calls
`net.neoforged.neoforge.client.ClientHooks.drawScreen(...)` at offset 745 instead of `Screen.renderWithTooltip`. So this is a
"Connector rewrote a target that NeoForge has since moved" case — the rewrite hides the incompatibility instead of surfacing it.

### Steps to reproduce

1. NeoForge 21.1.265, Connector 2.0.0-beta.17+1.21.1, Forgified Fabric API 0.116.15+2.3.6+1.21.1 (Java 25).
2. Put `replaymod-1.21-2.6.28.jar` in `mods/`.
3. Launch the game and join any singleplayer world (the crash happens while the world's screens render; no ReplayMod recording is needed).
4. Game exits with the stack trace above.

Minimal set believed to reproduce: Connector + Forgified Fabric API + ReplayMod.

### Logs

- `debug.log` (NeoForge debug log, crashing run): <link>
- `crash-report.txt`: <link>

### Additional context

- Connector: 2.0.0-beta.17+1.21.1 · NeoForge: 21.1.265 · Java: 25.0.4 · OS: Windows 11
- The mod has no NeoForge build; it is a Fabric-native mod and works on Fabric 1.21.1.
- #556 ("ReplayMod Incompatibilities", open since 2023, 1.20.1 launcher/FancyMenu failures) is the general ReplayMod thread; this report
  is a different, 1.21.1-specific crash (no FancyMenu involved).
- The two annotation variants above come from the original jar and from the Connector-remapped copy of it; the offsets 289
  (`getGameTimeDeltaTicks`) and 745 (`ClientHooks.drawScreen`) are from the vanilla 1.21.1 client classes and the
  NeoForge 21.1.265 patched classes. I can paste the full `javap -v` output in a comment if useful.
- Suggestion: when an `@At` target cannot be resolved after NeoForge's changes, keep the annotation unresolved (so the mixin fails
  loudly) rather than substituting an unrelated call; or apply the known `Screen.renderWithTooltip` → `ClientHooks.drawScreen`
  migration for this target.
