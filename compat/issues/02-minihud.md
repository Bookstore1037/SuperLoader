<!-- Suggested title:
[1.21.1] MiniHUD crashes at Bootstrap: @ModifyArgs on Language.loadFromJson(InputStream, BiConsumer) no longer matches (NeoForge moved the call into the 3-arg overload)
-->

> **Note on duplicates:** issue #2258 ("Incompatible with minihud", 1.21.1, open) reports MiniHUD 0.32.58 crashing at startup, but the
> logs attached there contain no mixin/injection error, so it looks like a different failure. This report is the `MixinLanguage`
> injection failure on 0.32.60 and cross-references #2258.

### Mod Name

MiniHUD

### Mod Homepage

https://modrinth.com/mod/minihud

### Minecraft version

1.21.1 (LTS)

### Describe the bug

With Connector, the game crashes during Bootstrap (before the main menu) with:

```
org.spongepowered.asm.mixin.injection.throwables.InjectionError: Critical injection failure:
  Multi-argument modifier method loadCustomText(Args;Map$Entry;)V in mixins.minihud.json:client.MixinLanguage
  from mod minihud failed injection check, (0/1) succeeded. Scanned 0 target(s). No refMap loaded.
```

`MixinLanguage` is a standard `@ModifyArgs` mixin:

```java
@Mixin(Language.class)
public abstract class MixinLanguage {
    @ModifyArgs(
        method = "loadFromJson(Ljava/io/InputStream;Ljava/util/function/BiConsumer;)V",
        at = @At(value = "INVOKE", target = "Ljava/util/function/BiConsumer;accept(Ljava/lang/Object;Ljava/lang/Object;)V"))
    private static void loadCustomText(Args args, Map.Entry<String, String> entry) { ... }
}
```

On vanilla 1.21.1 the `BiConsumer.accept` call is inside the two-argument `Language.loadFromJson(InputStream, BiConsumer)` (vanilla 1.21.1 client classes,
offset 102), so Fabric resolves it fine. On NeoForge 21.1.265 that method was rewritten into a thin delegate:

```
loadFromJson(InputStream, BiConsumer)        -> invokedynamic accept + invokestatic loadFromJson(InputStream, BiConsumer, BiConsumer) + return
loadFromJson(InputStream, BiConsumer, BiConsumer<Component>)  -> ... invokeinterface BiConsumer.accept (offset 128) ...
```

so the `INVOKE` target no longer exists in the method named by the mixin, `Scanned 0 target(s)`, and because
`mixins.minihud.json` is `required: true` with `injectors.defaultRequire: 1`, the failed injection aborts startup.

Connector's annotation remapping is not at fault here: the transformed jar already contains
`method = "loadFromJson(Ljava/io/InputStream;Ljava/util/function/BiConsumer;)V"` and `@Mixin(Language.class)` — the problem is that the
NeoForge-patched method body no longer contains the target.

### Steps to reproduce

1. NeoForge 21.1.265, Connector 2.0.0-beta.17+1.21.1, Forgified Fabric API 0.116.15+2.3.6+1.21.1 (Java 25).
2. Put `malilib-fabric-1.21-0.21.10.jar` and `minihud-fabric-1.21-0.32.60.jar` in `mods/`.
3. Launch the game.
4. Crash during Bootstrap with the message above.

Minimal set believed to reproduce: Connector + Forgified Fabric API + MaLiLib + MiniHUD.

### Logs

- `debug.log` (NeoForge debug log, crashing run): <link>
- `crash-report.txt`: <link>

### Additional context

- Connector: 2.0.0-beta.17+1.21.1 · NeoForge: 21.1.265 · Java: 25.0.4 · OS: Windows 11
- Same class of failure as the closed 26.2 report #2326 (`MaLiLib's MixinLanguage @ModifyArgs fails to resolve`), but on 1.21.1 and with
  the `loadFromJson` overload split as the direct cause.
- Connector jars contain no `Language` patch (grep of all classes for `loadFromJson`/`locale/Language` returns nothing), so the runtime
  class is the NeoForge-patched one.
- Only MiniHUD ships a `Language` mixin among the MaLiLib family (MaLiLib, Litematica, Tweakeroo load fine); they all use
  `refmap: null` and write intermediary names directly.
- Suggestion: when a NeoForge patch splits a method into delegates, remap `@At(INVOKE ...)` targets into the delegate that actually
  contains the call (here the 3-arg overload), or at least detect the "0 targets" case for required injectors and report the
  method-rewrite as the cause.
