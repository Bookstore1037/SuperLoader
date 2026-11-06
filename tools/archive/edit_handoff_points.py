import pathlib

p = pathlib.Path(r'D:\SuperLoader\HANDOFF.md')
text = p.read_text('utf-8')

old = "- 内容组 6 个（`content_phase2`）尚未开始，属阶段 2；infra 5 个纯库由依赖闭包带进来，不作为人工项"
new = """- 内容组（`content_phase2`）2026-11-05 晚状态：`betterend` / `betternether` 已进实例（斧头去皮由 companion 0.6.3 桥修好，
  实测 `lacugrove_log -> lacugrove_stripped_log`、`nether_sakura_log -> nether_sakura_stripped_log`）；`farmers-delight-refabricated`
  换成官方 NeoForge `1.21.1-1.3.4`；`the-bumblezone-fabric` 移出（决策 35）；只剩 `repurposed-structures-fabric`（+midnightlib）没试。
  infra 5 个纯库由依赖闭包带进来，不作为人工项"""
assert old in text
text = text.replace(old, new, 1)

old2 = "- companion 版本号：小改动只动第三位（0.4.0 → 0.4.1），别按功能跳 0.5.x；改版本后记得同步 `gradle.properties` 与 `SuperLoaderCompanion.VERSION`"
new2 = """- companion 版本号：小改动只动第三位，别按功能跳大版本；改版本后记得同步 `gradle.properties` 与 `SuperLoaderCompanion.VERSION`
  （当前 **0.6.3**：refmap 修复 + bclib 去皮桥；构建 `cd D:\\IDEA_mods\\nfprobe; .\\gradlew.bat build --offline`，
  产物 `build/libs/superloader_companion-0.6.3.jar` 复制进实例 `mods/` 并删旧版，实例 65 jar）"""
assert old2 in text
text = text.replace(old2, new2, 1)

p.write_text(text, encoding='utf-8')
print('handover points updated')
