# 已知装不上的 mod，以及为什么

这份清单是 2026-11 在 66 jar 的整包上逐个查出来的。每一条都读过字节码、不是猜的，证据的原话在
[docs/handoff-archive.md](handoff-archive.md) 的决策段和 `compat/*-investigation.md`。

**结论先说**：Connector 上游已经不再给 1.21.1 发兼容修复，所以下面这些在 1.21.1 上不会变好。遇到就按「处置」列处理。

## 一、需要移出的（L2，mixin / NeoForge 目标迁移）

| mod | 版本 | 症状 | 真正原因 | 处置 |
| --- | --- | --- | --- | --- |
| ReplayMod | 1.21-2.6.28 | 进存档时渲染线程崩，`GuiGraphics.flush()` 对 null 调用 | NeoForge 把 `GameRenderer.render` 里的 `Screen.renderWithTooltip` 换成 `ClientHooks.drawScreen`；Connector 把 `@At` 目标重写成无关的 `DeltaTracker.getGameTimeDeltaTicks` 并丢掉 `shift=AFTER`，回调每帧提前执行，字段还是 null | 移出（无替代） |
| MiniHUD | 0.21-0.32.60 | 启动期 Bootstrap 崩，`loadCustomText … Scanned 0 target(s)` | NeoForge 把 `Language.loadFromJson(InputStream, BiConsumer)` 改成转发给 3 参重载，`BiConsumer.accept` 调用点被搬走，`@ModifyArgs` 找不到注入点 | 移出；MaLiLib / Litematica / Tweaker 单独用没问题 |
| The Bumblezone | 7.17.3 | jar 转换阶段 NPE，日志里是 `dirtyTarget is null` | Connector 的 adapter（`ResolverSyntheticInstanceof`）在 `getDirtyTarget()` 为 null 时直接解引用，整个 jar 转换中止（崩在 Sodium 的配置检查只是连带） | 移出 |
| Farmer's Delight Refabricated | 3.3.6 | 加载 mixin 时 `InvalidInjectionException`，签名不符 | NeoForge 把 `BlockState getGrowthSpeed(Block, …)` 改成了 `BlockState` 首参，`@ModifyVariable` 的 handler 还是 `Block` | **换官方 NeoForge 版** `FarmersDelight-1.21.1-1.3.4.jar` |
| Friends & Foes | 5.0.4（Fabric） | attach 枚举 mixin 时 NPE | NeoForge 的枚举扩展机制接管了 `MobCategory` 的保留构造器，Fabric 枚举 mixin 找不到它 | **换 NeoForge 版** `friendsandfoes-neoforge-5.0.4+mc1.21.1.jar` |
| Language Reload | 1.7.6 | 在创造物品栏 / JEI 里搜索几个字符后 NPE，`separateTranslations` 为 null | 它假设「每次加载只构造一次 Language」，Connector 的 Language 补丁改了内部调用链，第二个实例拿到 null | 禁用（它的功能是热重载语言，可用重启代替） |

## 二、上游自己的问题（不是 Connector，也不是我们的锅）

| mod | 症状 | 原因 | 处置 |
| --- | --- | --- | --- |
| Falling Leaves | `@Invoker` 访问 `ParticleEngine$MutableSpriteSet` 失败 | 发布包 `fabric.mod.json` 丢了 `accessWidener` 键，jar 里的 `.aw` 是死文件；而那个内部类是 package-private | 移出；上游发新包修 |
| Carpet | `@ModifyConstant(16)` 注入失败，`Scanned 0 target(s)` | NeoForge 把 `flags & 16` 的 fill-updates 逻辑从 `Level.setBlock` 挪到 `markAndNotifyBlock`，目标方法里已经没有常量 16 | 移出 |

## 三、渲染重写类：不碰，直接用 NeoForge 原生版

Sodium、Iris、Sodium Extra **有**官方 NeoForge 构建，直接用，不要走 Connector 的 Fabric 版。
VulkanMod、Nvidium、C2ME、Indium、Exordium 这类没有原生版，也不在支持范围内——它们改的是渲染/线程内核，不是 Connector 能桥的层。

## 四、这些是「有原生版、只是我们没用」的

Sampler 里被归到 `both` 的（Sodium、Iris、FerriteCore、Lithium、Cloth Config、YACL、Xaero's、Architectury…）
在 1.21.1 上大多同时发布 Fabric 和 NeoForge 构建。整包里的选择原则很简单：**有 NeoForge 原生版就用原生版**，
Fabric 版只在「没有原生版」时才依赖 Connector。

## 想自己验证某一条

```bash
# 只放最小集：Connector + FFAPI + 这个 mod（+ 它的依赖）
# 然后看 logs/superloader-report/summary.txt 的「可疑模组」段
python superloader.py launch
```

如果 summary 里标了 `[L2]`，基本可以按上表直接处置；标 `[L0]` 是缺前置，按提示补就行。
