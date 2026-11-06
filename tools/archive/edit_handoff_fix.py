import pathlib

p = pathlib.Path(r'D:\SuperLoader\HANDOFF.md')
t = p.read_text('utf-8')

t = t.replace('内容组已进 beatend / betternether', '内容组已进 betterend / betternether')

old = """候选下一步（按性价比排序，任选或停测）：

1. **重建基线 + 一次回归**（约 10 分钟）：实例已从 57 涨到 65 jar，跑一次 launch 后用
   `python tools/make_baseline.py --out compat/baseline-65jar.json --manual compat/manual-checks-65jar.json`
   固化；顺便确认去皮桥在整包里没有副作用
2. **内容组收尾**：装 `repurposed-structures-fabric`（依赖 midnightlib）试一次；这是 content_phase2 里唯一没试的
3. **整理 Connector issue 合集**：replaymod / minihud / bumblezone / 农夫乐事-refabricated / friends-and-foes / language-reload，
   每条已有 `compat/*-investigation.md` 与英文草稿，合成一份 issue 列表即可（不需要再跑游戏）
4. **停测**：当前 65 jar 已经能进世界、能徒手验功能点；把 `compat/corpus_v2.md` 与报告当作交付物
"""

new = """候选下一步（按性价比排序，任选或停测）：

- **A. 重建基线 + 一次回归**（约 10 分钟）：实例已从 57 涨到 65 jar，跑一次 launch 后用
  `python tools/make_baseline.py --out compat/baseline-65jar.json --manual compat/manual-checks-65jar.json`
  固化；顺便确认去皮桥在整包里没有副作用
- **B. 内容组收尾**：装 `repurposed-structures-fabric`（依赖 midnightlib）试一次；这是 content_phase2 里唯一没试的
- **C. 整理 Connector issue 合集**：replaymod / minihud / bumblezone / 农夫乐事-refabricated / friends-and-foes / language-reload，
  每条已有 `compat/*-investigation.md` 与英文草稿，合成一份 issue 列表即可（不需要再跑游戏）
- **D. 停测**：当前 65 jar 已经能进世界、能徒手验功能点；把 `compat/corpus_v2.md` 与报告当作交付物
"""
assert old in t
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('next-step list fixed')
