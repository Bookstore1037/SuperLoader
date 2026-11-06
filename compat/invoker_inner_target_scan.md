# @Invoker/@Accessor 内部类 target 扫描（2026-11-05）

扫描方式：读 jar 内全部 `.class` 的常量池，挑出引用了 Mixin `Invoker`/`Accessor` 注解、
且常量池里出现 `net/minecraft...$...` 描述符的类；再把 target 的 intermediary 名经 Connector 的
`mappings/mappings.tiny` 翻成 mojmap，用 `javap` 读类级访问标志。**这是启发式扫描**（不解析注解结构），
可能有假阳性：一个 accessor 类里同时引用了别的内部类也会被列出来。

- 命中 jar：**22**，mixin 类：**53**，target 条目：**64**
- 其中 target 是 **package-private** 的条目：**20**

## 结论先行

1. 内部类 target 本身不是失败原因：22 个 jar / 53 个 mixin 类都这么做，只有 fallingleaves 崩。
2. 真正的区分点是 **target 类是否 package-private**，以及**该 mod 的 access widener 有没有被加载**。
3. fallingleaves 的 `.aw` 文件在 jar 里，但 `fabric.mod.json` 没有 `accessWidener` 键 → 两边都不加载；
   Connector 的 `@Invoker` target **已经正确重映射**（mapped jar 里是 `ParticleEngine$MutableSpriteSet`），
   所以这不是 remap 缺口，而是访问权限缺口。

## 明细

| 可见性 | jar | mixin 类 | target（intermediary） | target（mojang） | accessWidener |
|---|---|---|---|---|---|
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | AnimatedTextureAccessor | net.minecraft.class_7764$class_5790 | net.minecraft.client.renderer.texture.SpriteContents$AnimatedTexture | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | AnimatedTextureAccessor | net.minecraft.class_7764$class_5791 | net.minecraft.client.renderer.texture.SpriteContents$FrameInfo | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | SpriteContentsFrameInfoAccessor | net.minecraft.class_7764$class_5791 | net.minecraft.client.renderer.texture.SpriteContents$FrameInfo | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | SpriteContentsAnimatedTextureAccessor | net.minecraft.class_7764$class_5790 | net.minecraft.client.renderer.texture.SpriteContents$AnimatedTexture | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | SpriteContentsAnimatedTextureAccessor | net.minecraft.class_7764$class_5791 | net.minecraft.client.renderer.texture.SpriteContents$FrameInfo | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | SpriteContentsFrameInfoAccessor | net.minecraft.class_7764$class_5791 | net.minecraft.client.renderer.texture.SpriteContents$FrameInfo | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | SpriteContentsTickerAccessor | net.minecraft.class_7764$class_5790 | net.minecraft.client.renderer.texture.SpriteContents$AnimatedTexture | sodium-fabric.accesswidener |
| package-private | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | SpriteContentsTickerAccessor | net.minecraft.class_7764$class_7765 | net.minecraft.client.renderer.texture.SpriteContents$Ticker | sodium-fabric.accesswidener |
| package-private | fabric-carpet-1.21-1.4.147+v240613.jar | ThreadedLevelLightEngine_scarpetChunkCreationMixin | net.minecraft.class_3227$class_3901 | net.minecraft.server.level.ThreadedLevelLightEngine$TaskType | carpet.accesswidener |
| package-private | fallingleaves-1.17.1+1.21.1.jar | SimpleSpriteProviderInvoker | net.minecraft.class_702$class_4090 | net.minecraft.client.particle.ParticleEngine$MutableSpriteSet | dead:fallingleaves.accesswidener |
| package-private | language-reload-1.7.6+1.21.1.jar | ClientChunkManagerAccessor | net.minecraft.class_631$class_3681 | net.minecraft.client.multiplayer.ClientChunkCache$Storage | languagereload.accesswidener |
| package-private | language-reload-1.7.6+1.21.1.jar | ClientChunkMapAccessor | net.minecraft.class_631$class_3681 | net.minecraft.client.multiplayer.ClientChunkCache$Storage | languagereload.accesswidener |
| package-private | language-reload-1.7.6+1.21.1.jar | LanguageSelectionListWidgetAccessor | net.minecraft.class_426$class_4195 | net.minecraft.client.gui.screens.options.LanguageSelectScreen$LanguageSelectionList | languagereload.accesswidener |
| package-private | language-reload-1.7.6+1.21.1.jar | ClientChunkManagerAccessor | net.minecraft.class_631$class_3681 | net.minecraft.client.multiplayer.ClientChunkCache$Storage | languagereload.accesswidener |
| package-private | language-reload-1.7.6+1.21.1.jar | ClientChunkMapAccessor | net.minecraft.class_631$class_3681 | net.minecraft.client.multiplayer.ClientChunkCache$Storage | languagereload.accesswidener |
| package-private | language-reload-1.7.6+1.21.1.jar | LanguageSelectionListWidgetAccessor | net.minecraft.class_426$class_4195 | net.minecraft.client.gui.screens.options.LanguageSelectScreen$LanguageSelectionList | languagereload.accesswidener |
| package-private | repurposed_structures-7.5.22+1.21.1-fabric.jar | NamespaceResourceManagerAccessor | net.minecraft.class_3294$class_7082 | net.minecraft.server.packs.resources.FallbackResourceManager$PackEntry | repurposed_structures.accesswidener |
| package-private | the_bumblezone-7.17.3+1.21.1-fabric.jar | CooldownInstanceAccessor | net.minecraft.class_1796$class_1797 | net.minecraft.world.item.ItemCooldowns$CooldownInstance | the_bumblezone.accesswidener |
| package-private | the_bumblezone-7.17.3+1.21.1-fabric.jar | ItemCooldownsAccessor | net.minecraft.class_1796$class_1797 | net.minecraft.world.item.ItemCooldowns$CooldownInstance | the_bumblezone.accesswidener |
| package-private | trinkets-3.10.0.jar | CreativeSlotAccessor | net.minecraft.class_481$class_484 | net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen$SlotWrapper | trinkets.accesswidener |
| public | [钠] sodium-fabric-0.8.13+mc1.21.1.jar | MeshDataAccessor | net.minecraft.class_9799$class_9800 | com.mojang.blaze3d.vertex.ByteBufferBuilder$Result | sodium-fabric.accesswidener |
| public | bclib-21.0.13.jar | BiomeGenerationSettingsAccessor | net.minecraft.class_2893$class_2894 | net.minecraft.world.level.levelgen.GenerationStep$Carving | bclib.accesswidener |
| no-mapping | bclib-21.0.13.jar | MobSpawnSettingsAccessor | net.minecraft.class_6012<Lnet.minecraft.class_5483$class_1964 | ? | bclib.accesswidener |
| no-mapping | bclib-21.0.13.jar | RegistryDataLoaderMixin | net.minecraft.class_7655$class_7657<*> | ? | bclib.accesswidener |
| public | bclib-21.0.13.jar | SurfaceRulesContextAccessor | net.minecraft.class_6686$class_6694 | net.minecraft.world.level.levelgen.SurfaceRules$Context | bclib.accesswidener |
| public | better-end-21.0.11.jar | NoiseInterpolatorAccessor | net.minecraft.class_6568$class_5917 | net.minecraft.world.level.levelgen.NoiseChunk$NoiseInterpolator | betterend.accesswidener |
| public | better-nether-21.0.11.jar | RenderLayerMixin | net.minecraft.class_1921$class_4688 | net.minecraft.client.renderer.RenderType$CompositeState | betternether.accesswidener |
| public | better-nether-21.0.11.jar | RenderLayerMixin | net.minecraft.class_293$class_5596 | com.mojang.blaze3d.vertex.VertexFormat$Mode | betternether.accesswidener |
| public | better-nether-21.0.11.jar | BlockBehaviourAccessor | net.minecraft.class_4970$class_2251 | net.minecraft.world.level.block.state.BlockBehaviour$Properties | betternether.accesswidener |
| public | better-nether-21.0.11.jar | LootTableBuilderAccessor | net.minecraft.class_52$class_53 | net.minecraft.world.level.storage.loot.LootTable$Builder | betternether.accesswidener |
| public | cave_dust-3.0.1.jar | ClientWorldAccessor | net.minecraft.class_638$class_5271 | net.minecraft.client.multiplayer.ClientLevel$ClientLevelData | 无 |
| public | fabric-carpet-1.21-1.4.147+v240613.jar | ExplosionAccessor | net.minecraft.class_1927$class_4179 | net.minecraft.world.level.Explosion$BlockInteraction | carpet.accesswidener |
| public | fabric-carpet-1.21-1.4.147+v240613.jar | RedstoneWireBlock_fastMixin | net.minecraft.class_4970$class_2251 | net.minecraft.world.level.block.state.BlockBehaviour$Properties | carpet.accesswidener |
| public | fabric-carpet-1.21-1.4.147+v240613.jar | ThreadedLevelLightEngine_scarpetChunkCreationMixin | net.minecraft.class_2338$class_2339 | net.minecraft.core.BlockPos$MutableBlockPos | carpet.accesswidener |
| public | fastquit-3.0.0+1.20.6.jar | LevelStorageSessionAccessor | net.minecraft.class_32$class_5143 | net.minecraft.world.level.storage.LevelStorageSource$LevelStorageAccess | 无 |
| public | fastquit-3.0.0+1.20.6.jar | LevelStorageSessionAccessor | net.minecraft.class_32$class_7411 | net.minecraft.world.level.storage.LevelStorageSource$LevelDirectory | 无 |
| public | fastquit-3.0.0+1.20.6.jar | MinecraftServerAccessor | net.minecraft.class_32$class_5143 | net.minecraft.world.level.storage.LevelStorageSource$LevelStorageAccess | 无 |
| public | fastquit-3.0.0+1.20.6.jar | LevelStorageSessionAccessor | net.minecraft.class_32$class_5143 | net.minecraft.world.level.storage.LevelStorageSource$LevelStorageAccess | 无 |
| public | fastquit-3.0.0+1.20.6.jar | LevelStorageSessionAccessor | net.minecraft.class_32$class_7411 | net.minecraft.world.level.storage.LevelStorageSource$LevelDirectory | 无 |
| public | fastquit-3.0.0+1.20.6.jar | MinecraftServerAccessor | net.minecraft.class_32$class_5143 | net.minecraft.world.level.storage.LevelStorageSource$LevelStorageAccess | 无 |
| public | friendsandfoes-fabric-5.0.4+mc1.21.1.jar | ModelPartAccessor | net.minecraft.class_630$class_628 | net.minecraft.client.model.geom.ModelPart$Cube | friendsandfoes.accesswidener |
| public | held-item-info-1.7.0.jar | ItemEnchantmentsComponentAccessor | net.minecraft.class_7225$class_7874 | net.minecraft.core.HolderLookup$Provider | 无 |
| public | language-reload-1.7.6+1.21.1.jar | TextDisplayEntityAccessor | net.minecraft.class_8113$class_8123 | net.minecraft.world.entity.Display$TextDisplay | languagereload.accesswidener |
| public | language-reload-1.7.6+1.21.1.jar | TextDisplayEntityAccessor | net.minecraft.class_8113$class_8123$class_8125 | net.minecraft.world.entity.Display$TextDisplay$CachedInfo | languagereload.accesswidener |
| public | language-reload-1.7.6+1.21.1.jar | TextDisplayEntityAccessor | net.minecraft.class_8113$class_8123 | net.minecraft.world.entity.Display$TextDisplay | languagereload.accesswidener |
| public | language-reload-1.7.6+1.21.1.jar | TextDisplayEntityAccessor | net.minecraft.class_8113$class_8123$class_8125 | net.minecraft.world.entity.Display$TextDisplay$CachedInfo | languagereload.accesswidener |
| public | lazy-language-loader-0.3.7.jar | LanguageEntryAccessor | net.minecraft.class_426$class_4195$class_4194 | net.minecraft.client.gui.screens.options.LanguageSelectScreen$LanguageSelectionList$Entry | lazy-language-loader.accesswidener |
| public | lazy-language-loader-0.3.7.jar | LanguageEntryAccessor | net.minecraft.class_426$class_4195$class_4194 | net.minecraft.client.gui.screens.options.LanguageSelectScreen$LanguageSelectionList$Entry | lazy-language-loader.accesswidener |
| public | litematica-fabric-1.21-0.19.61.jar | IMixinKeyBinding | net.minecraft.class_3675$class_306 | com.mojang.blaze3d.platform.InputConstants$Key | litematica.accesswidener |
| public | malilib-fabric-1.21-0.21.10.jar | IMixinAnimalArmorItem | net.minecraft.class_4059$class_9076 | net.minecraft.world.item.AnimalArmorItem$BodyType | malilib.accesswidener |
| public | minihud-fabric-1.21-0.32.60.jar | IMixinBeaconBlockEntity | net.minecraft.class_2580$class_2581 | net.minecraft.world.level.block.entity.BeaconBlockEntity$BeaconBeamSection | dead:minihud.accesswidener |
| public | replaymod-1.21-2.6.28.jar | MinecraftAccessor | net.minecraft.class_9779$class_9781 | net.minecraft.client.DeltaTracker$Timer | 无 |
| public | replaymod-1.21-2.6.28.jar | TimerAccessor | net.minecraft.class_9779$class_9781 | net.minecraft.client.DeltaTracker$Timer | 无 |
| public | repurposed_structures-7.5.22+1.21.1-fabric.jar | TemplateAccessor | net.minecraft.class_3499$class_5162 | net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate$Palette | repurposed_structures.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | SoundEngineAccessor | net.minecraft.class_4235$class_4236 | net.minecraft.client.sounds.ChannelAccess$ChannelHandle | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | TextureStateShardAccessor | net.minecraft.class_4668$class_4683 | net.minecraft.client.renderer.RenderStateShard$TextureStateShard | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | KeyMappingAccessor | net.minecraft.class_3675$class_306 | com.mojang.blaze3d.platform.InputConstants$Key | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | ItemAccessor | net.minecraft.class_3959$class_242 | net.minecraft.world.level.ClipContext$Fluid | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | BiomeManagerAccessor | net.minecraft.class_4543$class_4544 | net.minecraft.world.level.biome.BiomeManager$NoiseBiomeSource | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | NoiseChunkAccessor | net.minecraft.class_6544$class_4762 | net.minecraft.world.level.biome.Climate$ParameterPoint | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | NoiseChunkAccessor | net.minecraft.class_6544$class_6552 | net.minecraft.world.level.biome.Climate$Sampler | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | StructureTemplateAccessor | net.minecraft.class_3499$class_3502 | net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate$StructureEntityInfo | the_bumblezone.accesswidener |
| public | the_bumblezone-7.17.3+1.21.1-fabric.jar | StructureTemplateAccessor | net.minecraft.class_3499$class_5162 | net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate$Palette | the_bumblezone.accesswidener |
| public | trinkets-3.10.0.jar | LivingEntityRendererMixin | net.minecraft.class_5617$class_5618 | net.minecraft.client.renderer.entity.EntityRendererProvider$Context | trinkets.accesswidener |

