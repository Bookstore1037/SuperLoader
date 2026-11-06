import pathlib

p = pathlib.Path(r'D:\SuperLoader\HANDOFF.md')
text = p.read_text('utf-8')

anchor = "路线与判据见 `ROADMAP.md`（2026-11-03 修订）：主线是 Connector 跑 Fabric 原生 mod、目标 ≥90% 完美兼容；L0–L4 失败分层；补丁打桥接层、一个补丁覆盖一类调用；顺序 L1 → L4 → L2 个案 → L3 不做。\n"
assert anchor in text

block = anchor + """
### 2026-11-05 收工时的状态（已交付，别重做）

- companion **0.6.3**，两个补丁都在实例里：①refmap 缺失修复（0.5.2 起，每映射三态校验）②bclib 去皮桥（0.6.3 实测生效）
- 实例 **65 jar**；内容组已进 beatend / betternether / 农夫乐事（NeoForge 官方版）/ friends-and-foes（NeoForge 构建）/ repurposed-structures 未试
- 已移出并记录：`replaymod`(L2 Connector 目标迁移)、`minihud`(L2 NeoForge 改写)、`the-bumblezone-fabric`(L2 adapter NPE)、
  `language-reload`(L2 构造顺序，用户已禁用)、`fallingleaves`(上游丢 AW 键)；jar 在 `D:\\SuperLoader\\logs\\removed-mods\\`
- 六个 L2 案例的取证文档都在 `compat/*-investigation.md`，可直接整理成 Connector issue 合集

候选下一步（按性价比排序，任选或停测）：

1. **重建基线 + 一次回归**（约 10 分钟）：实例已从 57 涨到 65 jar，跑一次 launch 后用
   `python tools/make_baseline.py --out compat/baseline-65jar.json --manual compat/manual-checks-65jar.json`
   固化；顺便确认去皮桥在整包里没有副作用
2. **内容组收尾**：装 `repurposed-structures-fabric`（依赖 midnightlib）试一次；这是 content_phase2 里唯一没试的
3. **整理 Connector issue 合集**：replaymod / minihud / bumblezone / 农夫乐事-refabricated / friends-and-foes / language-reload，
   每条已有 `compat/*-investigation.md` 与英文草稿，合成一份 issue 列表即可（不需要再跑游戏）
4. **停测**：当前 65 jar 已经能进世界、能徒手验功能点；把 `compat/corpus_v2.md` 与报告当作交付物
"""

text = text.replace(anchor, block, 1)
p.write_text(text, encoding='utf-8')
print('inserted 收工状态 block')
