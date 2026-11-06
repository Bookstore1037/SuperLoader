<!-- Suggested title:
[1.21.1] Farmer's Delight Refabricated crashes at load: @ModifyVariable handler signature unchanged while NeoForge changed CropBlock.getGrowthSpeed's parameter from Block to BlockState
-->

### Mod Name

Farmer's Delight Refabricated

### Mod Homepage

https://modrinth.com/mod/farmers-delight-refabricated

### Minecraft version

1.21.1 (LTS)

### Describe the bug

With Connector, the game crashes while applying mixins to Farmer's Delight Refabricated:

```
org.spongepowered.asm.mixin.injection.throwables.InvalidInjectionException:
  @ModifyVariable handler method farmersdelightrefabricated$modifyGrowthSpeedForNonFarmland in
  farmersdelight.mixins.json:refabricated.CropBlockMixin from mod farmersdelight has an invalid signature.
  Found unexpected argument type net.minecraft.world.level.block.Block at index 1,
  expected net.minecraft.world.level.block.state.BlockState.
  Handler signature: (F Lnet/minecraft/world/level/block/Block; Lnet/minecraft/world/level/BlockGetter; Lnet/minecraft/world/level/BlockPos;)F
  Expected signature: (F Lnet/minecraft/world/level/block/state/BlockState; Lnet/minecraft/world/level/BlockGetter; Lnet/minecraft/world/level/BlockPos;)F
```

The mixin is a plain `@ModifyVariable`:

```java
@ModifyVariable(method = "getGrowthSpeed", at = @At(value = "LOAD", ordinal = 1))
private static float farmersdelightrefabricated$modifyGrowthSpeedForNonFarmland(
        float original, Block block, BlockGetter level, BlockPos pos) { ... }
```

On vanilla 1.21.1, `CropBlock.getGrowthSpeed` is `(Block, BlockGetter, BlockPos)F`, so the handler signature matches.
On NeoForge 21.1.265 the patched method is `(BlockState, BlockGetter, BlockPos)F` — the first parameter was replaced.
Mixin validates the handler signature against the target descriptor before injecting, so it rejects the handler and, because the mixin
is required, aborts startup.

Connector's remapping of the annotation itself is correct: the transformed jar has
`@ModifyVariable(method = "getGrowthSpeed", ...)` with the handler still typed `Block`. The adapter handles parameter *insertion* and
*reordering* (`ParametersProcessor`, `ParametersDiff`), but not parameter *type replacement*.

### Steps to reproduce

1. NeoForge 21.1.265, Connector 2.0.0-beta.17+1.21.1, Forgified Fabric API 0.116.15+2.3.6+1.21.1 (Java 25).
2. Put `FarmersDelight-1.21.1-3.3.6+refabricated.jar` in `mods/` (the Fabric build; the official NeoForge build of Farmer's Delight
   works and is not affected).
3. Launch the game.
4. Crash while loading mixins with the `InvalidInjectionException` above.

Minimal set believed to reproduce: Connector + Forgified Fabric API + Farmer's Delight Refabricated.

### Logs

- `debug.log` (NeoForge debug log, crashing run): <link>
- `crash-report.txt`: <link>

### Additional context

- Connector: 2.0.0-beta.17+1.21.1 · NeoForge: 21.1.265 · Java: 25.0.4 · OS: Windows 11
- Distinct from the open #2304 (26.1.2, tomato block tick crash): here it is a load-time signature failure on 1.21.1, no world needed.
- 3.3.6 is the latest 1.21.1 Fabric build (2026-08-31), so there is nothing to update to.
- Suggestion: when a NeoForge patch replaces a target parameter type, rewrite the handler's local-variable descriptor and insert a
  conversion (here `BlockState` → `Block` via `state.getBlock()`), or skip that handler with a warning instead of failing the mixin.
