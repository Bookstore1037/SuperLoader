<!-- Suggested title:
[1.21.1] The Bumblezone 7.17.3 cannot be transformed: NullPointerException in ResolverSyntheticInstanceof.resolve (dirtyTarget == null)
-->

### Mod Name

The Bumblezone

### Mod Homepage

https://modrinth.com/mod/the-bumblezone-fabric

### Minecraft version

1.21.1 (LTS)

### Describe the bug

With Connector, the game never reaches the main menu. The Connector jar transformer fails on the mod and everything after it fails as a
consequence (in our instance Sodium then reports `Sodium's config could not be found`, which is just the first unrelated code that
notices the broken mod state).

`latest.log`:

```
[pool-3-thread-7/ERROR] [transformer.jar.JarTransformInstance/]:
  Encountered error while transforming jar file .../mods/the_bumblezone-7.17.3+1.21.1-fabric.jar
java.lang.RuntimeException: Failed to execute task com/telepathicgrunt/the_bumblezone/mixin/fabric/entity/LivingEntityMixin.class
    at org.sinytra.connector.transformer.jar.JarTransformer.transform(JarTransformer.java:...)
Caused by: java.lang.NullPointerException: Cannot invoke "org.sinytra.adapter.env.ctx.TargetPair.methodNode()"
  because "dirtyTarget" is null
    at org.sinytra.adapter.patch.resolver.special.ResolverSyntheticInstanceof.resolve(ResolverSyntheticInstanceof.java:54)
    at org.sinytra.adapter.patch.PipelineMethodTransformer.execute(PipelineMethodTransformer.java:92)
    at org.sinytra.adapter.patch.Patcher.processMixin(Patcher.java:131)
    at org.sinytra.adapter.patch.MixinPatchTransformer.process(MixinPatchTransformer.java:157)
```

`ResolverSyntheticInstanceof.resolve` takes the result of `Recipe.getDirtyTarget()` and calls `.methodNode()` on it without a null
check (bytecode: the value goes into local 4 and is dereferenced at offsets 99–104). A neighbouring branch in the same method does
have a `ResolutionResult.pass()` fallback, so it looks like an unintended omission rather than a deliberate failure path.

The mixin being processed is a plain Fabric mixin with standard annotations (no custom plugin, no access widener):

```java
@Mixin(value = LivingEntity.class, priority = 1200)
public abstract class LivingEntityMixin {
    @ModifyReturnValue(method = "getVisibilityPercent", at = @At("RETURN")) ...
    @Inject(method = "tick", at = @At("TAIL")) ...
    @Inject(method = "hurt", at = @At("HEAD"), cancellable = true) ...
    @Inject(method = "actuallyHurt", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/LivingEntity;getDamageAfterMagicAbsorb(Lnet/minecraft/world/damagesource/DamageSource;F)F", ordinal = 0)) ...
    @ModifyExpressionValue(method = "baseTick", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/Entity;isEyeInFluid(Lnet/minecraft/tags/TagKey;)Z")) ...
    @ModifyReturnValue(method = "getSlotForHand", at = @At("RETURN")) ...
    @WrapOperation(method = "aiStep", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/LivingEntity;getFluidHeight(Lnet/minecraft/tags/TagKey;)D", ordinal = 1), require = 0) ...
}
```

### Steps to reproduce

1. NeoForge 21.1.265, Connector 2.0.0-beta.17+1.21.1, Forgified Fabric API 0.116.15+2.3.6+1.21.1 (Java 25).
2. Put `the_bumblezone-7.17.3+1.21.1-fabric.jar` in `mods/`.
3. Launch the game.
4. The jar transform fails, then startup aborts with `Error during pre-loading phase: [Connector] Error transforming file ...`.

Minimal set believed to reproduce: Connector + Forgified Fabric API + The Bumblezone.

### Logs

- `debug.log` (NeoForge debug log, crashing run): <link>
- `crash-report.txt`: <link>

### Additional context

- Connector: 2.0.0-beta.17+1.21.1 (newest 1.21.1 build) · NeoForge: 21.1.265 · Java: 25.0.4 · OS: Windows 11
- The mod has no NeoForge build on Modrinth; the Fabric build works on Fabric 1.21.1.
- 7.17.3+1.21.1 is the latest build for 1.21.1 (2026-10-27), so there is nothing to update to.
- The crash report alone is misleading: it points at Sodium. The useful lines are the `Encountered error while transforming jar file` /
  `Failed to execute task ... LivingEntityMixin.class` / `dirtyTarget` ones in `latest.log`.
- Suggestion: null-check `dirtyTarget` in `ResolverSyntheticInstanceof.resolve` and fall back to the same `pass()` behaviour the
  neighbouring branch uses; a failed resolver should produce a normal "cannot apply patch" result, not an NPE that fails the whole jar
  transform.
