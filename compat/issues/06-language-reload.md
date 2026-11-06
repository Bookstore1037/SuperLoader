<!-- Suggested title:
[1.21.1] Language Reload crashes on charTyped in the creative inventory: ClientLanguage.separateTranslations is null after Connector's Language patch changes the construction order
-->

### Mod Name

Language Reload

### Mod Homepage

https://modrinth.com/mod/language-reload

### Minecraft version

1.21.1 (LTS)

### Describe the bug

With Connector, typing into the creative inventory search crashes the game:

```
net.minecraft.ReportedException: charTyped event handler
Caused by: java.lang.NullPointerException: Cannot invoke "java.util.Map.get(Object)" because "this.separateTranslations" is null
    at net.minecraft.client.resources.language.ClientLanguage.languagereload_get(ClientLanguage.java:554)
    at net.minecraft.network.chat.contents.TranslatableContents.getOverriddenTranslations(TranslatableContents.java:1056)
    at net.minecraft.network.chat.contents.TranslatableContents.wrapOperation$zno000$languagereload$onVisit(TranslatableContents.java:1030)
    at net.minecraft.client.gui.screens.inventory.SessionSearchTrees.wrapOperation$znn000$languagereload$addFallbackTranslationsToSearchTooltips(SessionSearchTrees.java:545)
    at net.minecraft.client.searchtree.SearchTree.plainText(...)
    at net.minecraft.client.searchtree.FullTextSearchTree.<init>(...)
    at net.minecraft.client.gui.screens.inventory.SessionSearchTrees.lambda$updateCreativeTooltips$14(...)
    at net.minecraft.client.KeyboardHandler.charTyped(KeyboardHandler.java:494)
```

The `Mixins in Stacktrace` section of the crash report shows both Language Reload mixins involved:

```
net.minecraft.client.resources.language.ClientLanguage
    - jerozgen.languagereload.mixin.TranslationStorageMixin (languagereload.mixins.json)
net.minecraft.network.chat.contents.TranslatableContents
    - jerozgen.languagereload.mixin.TranslatableTextContentMixin (languagereload.mixins.json)
    - xyz.nucleoid.server.translations.mixin.codec.TranslatableTextContentMixin (server_translations_api.mixin.json)
```

`TranslationStorageMixin` assumes exactly one `Language` instance is constructed per resource load:

- `onLoad` (injected at `ClientLanguage.loadFrom` HEAD) stores the per-language maps in the **static** `separateTranslationsOnLoad`;
- `onConstructed` (injected at `Language.<init>` TAIL) copies it into the **instance** field `separateTranslations` and then sets the
  static field to `null`;
- `onInternalLoad$saveSeparately` is injected at an `INVOKE` of `Language.loadFromJson(InputStream, BiConsumer)`.

Under Connector the `loadFromJson` call site is rewritten to the **3-argument** overload (NeoForge's patched `Language` delegates the
two-argument method to `loadFromJson(InputStream, BiConsumer, BiConsumer<Component>)`, and the transformed mixin's constant pool
references the 3-arg method). With the altered call/constructor ordering, the second `Language` instance is constructed after the
static field has been consumed, so its `separateTranslations` stays `null`, and `ClientLanguage.languagereload_get` dereferences it
without a null check.

We are not 100% certain whether the decisive factor is the rewritten `loadFromJson` call site or the extra `Language` construction
NeoForge performs; both point at the same assumption ("one Language per load"), which does not hold under Connector + NeoForge.

### Steps to reproduce

1. NeoForge 21.1.265, Connector 2.0.0-beta.17+1.21.1, Forgified Fabric API 0.116.15+2.3.6+1.21.1 (Java 25).
2. Put `language-reload-1.7.6+1.21.1.jar` in `mods/`.
3. Launch the game, enter a world, open the creative inventory, type two or more characters into the search box.
4. Crash in `charTyped` with the NPE above.

Minimal set believed to reproduce: Connector + Forgified Fabric API + Language Reload.

### Logs

- `debug.log` (NeoForge debug log, crashing run): <link>
- `crash-report.txt`: <link>

### Additional context

- Connector: 2.0.0-beta.17+1.21.1 · NeoForge: 21.1.265 · Java: 25.0.4 · OS: Windows 11
- 1.7.6+1.21.1 is the latest 1.21.1 build; the mod is Fabric-native.
- The same NPE comes from Language Reload's own injected getter (`ClientLanguage.languagereload_get`); the Server Translations API mixin
  listed in the stacktrace only participates in the same `TranslatableContents` visit and is not the source of the null field.
- Suggestion: either keep `loadFromJson` call sites on the two-argument method (so the mod's `@At` injection still lands where it
  expects), or expose the same "per-load" hook NeoForge uses so Fabric mods that assume a single `Language` instance survive the extra
  construction.
