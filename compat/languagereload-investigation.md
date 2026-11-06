# language-reload 在 Connector 下的崩溃（L2）

## 现象

创建/打开创造模式物品栏、在 JEI 里输入搜索时崩溃：

```
Description: charTyped event handler
RemappedThrowable: Cannot invoke "java.util.Map.get(Object)" because "this.separateTranslations" is null
  at ClientLanguage.languagereload_get(ClientLanguage.java:554)
  at TranslatableContents.getOverriddenTranslations(TranslatableContents.java:1056)
  at TranslatableContents.wrapOperation$zno000$languagereload$onVisit(...)
  at SessionSearchTrees.wrapOperation$znn000$languagereload$addFallbackTranslationsToSearchTooltips(...)
  at SearchTree.plainText(...)
  at FullTextSearchTree.<init>(...)
  at SessionSearchTrees.lambda$updateCreativeTooltips$14(...)
  at KeyboardHandler.charTyped(KeyboardHandler.java:494)
```

崩溃报告：`D:\SLData\instances\1.21.1\crash-reports\crash-2026-11-05_20.24.47-client.txt`。

## mod 的工作方式（字节码）

`language-reload-1.7.6+1.21.1.jar` 的 `TranslationStorageMixin`（`@Mixin(Language.class)`）：

1. `onLoad`：注入 `ClientLanguage.loadFrom(...)` HEAD → `separateTranslationsOnLoad = new HashMap<>()`；
2. `onConstructed`：注入 `Language.<init>` TAIL →
   `separateTranslations = separateTranslationsOnLoad; separateTranslationsOnLoad = null;`
3. `onInternalLoad$saveSeparately`：注入 `Language.loadFromJson(InputStream, BiConsumer)` 内部的 `BiConsumer.accept` 调用，把每条翻译同时存进静态表；
4. `languagereload_get(String)`：直接用 `this.separateTranslations.get(...)`，**没有 null 兜底**。

也就是说它假设**一次加载只构造一个 Language 实例**：静态表在构造时被消费并清空。

## Connector 下的实际行为

- Connector 的 Language 补丁把 `loadFromJson` 的 2 参重载改成转发到 3 参重载；mapped jar 里
  `onInternalLoad$saveSeparately` 的调用点也从 2 参变成 3 参（证据：mapped class 常量池里出现
  `loadFromJson(InputStream, BiConsumer, BiConsumer)`）。
- 结果：构造顺序不再满足上面的假设——第二个 `ClientLanguage` 实例构造时静态表已经是 null，
  `separateTranslations` 为 null；等到 `getOverriddenTranslations` 走 `languagereload_get` 时直接 NPE。
- 归因器（`core/suspects.py`）能从崩溃报告的 `Mixins in Stacktrace:` 段读出：
  `net.minecraft.client.resources.language.ClientLanguage ← jerozgen.languagereload.mixin.TranslationStorageMixin (languagereload.mixins.json)`。

## 判定

- **不是 mod 自身 bug**（1.21.1 最新 Fabric 构建，Fabric 上正常）；
- **不是 refmap 缺口**（refmap 完整，注入点都能解析）；
- 是 **L2**：Connector 的 `Language` 补丁改变了 `loadFromJson` 的调用链，与 mod 的构造顺序假设冲突。
- companion 修不了：要给别人的 mixin 字段加 null 兜底 / 改消费逻辑，属于逐 mod 硬编码，违反护栏。

## 处置

- 用户已禁用 `language-reload`（实例 mods 里已无该 jar）；
- 记录进 `compat/corpus.json.excluded_upstream_defects` 与 `exceptions`，从 main 移出（manual 分母 33 → 32）；
- 可提给上游/Connector：`languagereload_get` 加 null 兜底（mod 侧一行修复），或 Connector 保持 2 参 `loadFromJson`
  的调用链不被改写（更根本）。
