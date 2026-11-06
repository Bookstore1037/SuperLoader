# friends-and-foes 崩溃调查（2026-11-05）

## 现象

- 模组：`friendsandfoes-fabric-5.0.4+mc1.21.1.jar`（Modrinth 上 1.21.1 的最新 Fabric 构建，2026-10-26，没有 NeoForge 构建）
- 环境：NeoForge 21.1.265 + Connector 2.0.0-beta.17 + FFAPI 0.116.15
- 启动即崩（`crash-2026-11-05_20.05.26-client.txt`），`superloader-launch.log`：

```
MixinTransformerError: An unexpected critical error was encountered
Caused by: MixinPreProcessorException: Attach error for friendsandfoes-fabric.mixins.json:AddCustomSpawnGroupMixin
  from mod friendsandfoes during activity: [Attach method -> <init>(Ljava/lang/String;ILjava/lang/String;IZZI)V]
Caused by: java.lang.NullPointerException: Cannot invoke
  "org.spongepowered.asm.mixin.transformer.ClassInfo$Method.isUnique()" because "method" is null
```

## 证据

1. `AddCustomSpawnGroupMixin` 是**枚举 mixin**：`extends java.lang.Enum<AddCustomSpawnGroupMixin>`，
   `@Mixin(value=[class Lnet/minecraft/class_1311;])`（= `net.minecraft.world.entity.MobCategory`），
   声明常量 `FRIENDSANDFOES_GLARES` / `FRIENDSANDFOES_RASCALS`，`<clinit>` 调自己的
   `<init>(String,int,String,int,boolean,boolean,int)`。
2. 该构造器的 7 参描述符 `(Ljava/lang/String;ILjava/lang/String;IZZI)V` 在 **vanilla 1.21.1** 的
   `MobCategory.class` 里存在（也在 NeoForge 的 `MobCategory.class` 里存在）。
3. Mixin 报的是"在目标类里 attach 这个构造器时 `method == null`"——即运行时它查不到这个构造器。
4. NeoForge 的 `MobCategory` 实现了 `IExtensibleEnum`，其 7 参构造器是 NeoForge 的**枚举扩展保留构造器**；
   运行时 `RuntimeEnumExtender`（`loader-4.0.45.jar`，`ILaunchPluginService`）持有
   `RESERVED_ANNOTATION`（`@ReservedConstructor`）并在扩展枚举时消费/移除该构造器。
5. Connector 的重映射没有问题：`class_1311` → `net.minecraft.world.entity.MobCategory` 正确。

## 判定

**L2 / 结构性冲突**：Fabric 的"枚举 mixin 加常量"依赖目标枚举的原始构造器存在；NeoForge 的枚举扩展机制接管了同一个构造器。
两者没有交集，Connector 也不会把 Fabric 枚举 mixin 翻译成 NeoForge 的 `IExtensibleEnum` 扩展。

- 不是 friendsandfoes 写错（它在 Fabric 1.21.1 上是正常工作的）；
- 不是 refmap/注解重映射缺口（错误发生在 attach 阶段，注解本身已正确解析）；
- 顺带暴露 Mixin 的一个体验问题：目标方法不存在时抛 NPE 而不是"method not found"。

## 处置

- 短期：移出 `friendsandfoes-fabric-5.0.4+mc1.21.1.jar`（Modrinth 无 NeoForge 构建，无处可换）；
- 治本：Connector 上游支持"枚举 mixin → NeoForge 枚举扩展"的转换（或至少在 attach 失败时给出可读错误）；
- companion / FFAPI 层无法处理（发生在 Mixin 预处理阶段，且需要改写第三方类的字节码）。

## 给 Connector 的 issue 草稿

> **Title**: Enum mixins fail to attach on NeoForge-extended enums (e.g. `MobCategory`) — NPE in `ClassInfo$Method.isUnique`
>
> **Summary**: A Fabric enum mixin that adds constants to `net.minecraft.world.entity.MobCategory`
> fails at attach time on NeoForge 21.1.265 with
> `MixinPreProcessorException: Attach error ... <init>(Ljava/lang/String;ILjava/lang/String;IZZI)V`
> and an NPE (`method is null`). The same 7-arg constructor exists in the vanilla class but is the
> NeoForge *reserved* constructor consumed by `RuntimeEnumExtender`.
>
> **Expected**: either translate the enum mixin to NeoForge's enum extension, or fail with a clear
> diagnostic ("cannot extend NeoForge-managed enum").
>
> **Repro**: NeoForge 21.1.265 + Connector 2.0.0-beta.17 + friendsandfoes-fabric-5.0.4+mc1.21.1.
