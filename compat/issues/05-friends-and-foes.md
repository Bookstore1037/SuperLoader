<!-- Suggested title:
[1.21.1] Friends & Foes (Fabric) crashes at mixin attach: enum mixin cannot find MobCategory's constructor because NeoForge's enum extension consumes it
-->

### Mod Name

Friends & Foes

### Mod Homepage

https://modrinth.com/mod/friends-and-foes

### Minecraft version

1.21.1 (LTS)

### Describe the bug

With Connector, the Fabric build of Friends & Foes crashes while attaching a mixin to the `MobCategory` enum:

```
org.spongepowered.asm.mixin.transformer.throwables.MixinTransformerError: An unexpected critical error was encountered
Caused by: org.spongepowered.asm.mixin.transformer.throwables.MixinPreProcessorException:
  Attach error for friendsandfoes-fabric.mixins.json:AddCustomSpawnGroupMixin from mod friendsandfoes
  during activity: [Attach method -> <init>(Ljava/lang/String;ILjava/lang/String;IZZI)V]
Caused by: java.lang.NullPointerException: Cannot invoke "org.spongepowered.asm.mixin.transformer.ClassInfo$Method.isUnique()"
  because "method" is null
```

`AddCustomSpawnGroupMixin` is a standard "add enum constants" mixin:

```java
@Mixin(value = MobCategory.class)
public abstract class AddCustomSpawnGroupMixin extends Enum<AddCustomSpawnGroupMixin> {
    // two new constants built through the 7-argument constructor, e.g.
    private static final MobCategory FRIENDSANDFOES_GLARES  = new MobCategory(..., 12, ..., 64, true, true, 128);
    private static final MobCategory FRIENDSANDFOES_RASCALS = new MobCategory(..., 13, ..., 64, true, true, 128);

    @Shadow private static MobCategory[] $VALUES;
    @Shadow private int max; ...
}
```

On Fabric the target `MobCategory` has the 7-argument constructor `(String, int, String, int, boolean, boolean, int)` and the mixin
appends entries through it. On NeoForge 21.1.265, `MobCategory` implements
`net.neoforged.fml.common.asm.enumextension.IExtensibleEnum`, and NeoForge's `RuntimeEnumExtender` consumes/removes that reserved
constructor at runtime (`loader-4.0.45.jar` contains `enumextension/ReservedConstructor`, and the extender's constant pool references
`ReservedConstructor` and `remove`). When Mixin tries to "attach" the mixin's `<init>` to the target enum, the corresponding target
method is gone, and Mixin reports it as `method is null` instead of a clear "target not found".

The mod is not at fault and neither is Connector's remapping (`class_1311` → `net.minecraft.world.entity.MobCategory` is correct).

### Steps to reproduce

1. NeoForge 21.1.265, Connector 2.0.0-beta.17+1.21.1, Forgified Fabric API 0.116.15+2.3.6+1.21.1 (Java 25).
2. Put `friendsandfoes-fabric-5.0.4+mc1.21.1.jar` in `mods/` (the Fabric build; the NeoForge build of the same version works).
3. Launch the game.
4. Crash while attaching mixins, before the main menu.

Minimal set believed to reproduce: Connector + Forgified Fabric API + Friends & Foes (Fabric build).

### Logs

- `debug.log` (NeoForge debug log, crashing run): <link>
- `crash-report.txt`: <link>

### Additional context

- Connector: 2.0.0-beta.17+1.21.1 · NeoForge: 21.1.265 · Java: 25.0.4 · OS: Windows 11
- 5.0.4+mc1.21.1 is the latest 1.21.1 Fabric build (2026-10-26).
- Workaround: use the NeoForge build (`friendsandfoes-neoforge-5.0.4+mc1.21.1.jar`), which we use now and which works.
- Suggestion: convert "enum mixin that adds constants through a reserved constructor" into an `IExtensibleEnum` extension at transform
  time (the way NeoForge intends enums to be extended), or detect the consumed reserved constructor and fail with a clear message.
