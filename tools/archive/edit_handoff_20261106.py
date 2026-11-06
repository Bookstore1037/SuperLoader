import json
import pathlib

root = pathlib.Path(r'D:\SuperLoader')

# 1) corpus.json: 指向 issue 合集
cp = root / 'compat/corpus.json'
c = json.loads(cp.read_text('utf-8'))
c['issue_collection'] = 'compat/connector-issues.md'
cp.write_text(json.dumps(c, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

# 2) HANDOFF
p = root / 'HANDOFF.md'
t = p.read_text('utf-8')

old_head = "- **2026-11-05 晚：内容组试装收工**（实例 65 jar，companion **0.6.3**）："
new_head = """- **2026-11-06：基线重建 + Connector issue 合集**：
  - `compat/baseline-66jar.json`（66 jar，launch 2026-11-06 12:03:20 → 12:04:59，`exit 0`、`fatal 0`、`stale false`、`suspects 0`、
    `apis_issues 0`、`covers_current_mods true`）；manual 32 条沿用 `compat/manual-checks-66jar.json`
  - `compat/connector-issues.md`：6 个 L2 案例（replaymod / minihud / bumblezone / farmers-delight-refabricated /
    friends-and-foes / language-reload）的统一环境、根因、字节码证据、建议修法与提交清单
  - 报告去噪：`fatal_lines()` 与 `suspects.scan_console/scan_crash_frames` 现在按日志级别过滤——
    WARN 里附带的异常栈（如 bclib 备份存档时 `java.io.IOException: 另一个程序已锁定文件的一部分`）不再被当成致命行/可疑模组；
    WARN 栈也不再被 `crash_frame` 误判为崩溃栈。三种情况复测：干净启动 `fatal=[] suspects=0`，
    合成 FATAL 栈仍能归因到 bclib，WARN 栈被忽略
- **2026-11-05 晚：内容组试装收工**（实例 65→66 jar，companion **0.6.3**）："""
assert old_head in t
t = t.replace(old_head, new_head, 1)

# 3) 下一步：标记 A / C 已完成
old_a = """- **A. 重建基线 + 一次回归**（约 10 分钟）：实例已从 57 涨到 65 jar，跑一次 launch 后用
  `python tools/make_baseline.py --out compat/baseline-65jar.json --manual compat/manual-checks-65jar.json`
  固化；顺便确认去皮桥在整包里没有副作用"""
new_a = """- **A. 重建基线 + 一次回归**：✅ 已完成（2026-11-06）——`compat/baseline-66jar.json`，
  启动 `exit 0 / fatal 0 / suspects 0 / stale false`，去皮桥在整包里无副作用"""
assert old_a in t
t = t.replace(old_a, new_a, 1)

old_c = """- **C. 整理 Connector issue 合集**：replaymod / minihud / bumblezone / 农夫乐事-refabricated / friends-and-foes / language-reload，
  每条已有 `compat/*-investigation.md` 与英文草稿，合成一份 issue 列表即可（不需要再跑游戏）"""
new_c = """- **C. 整理 Connector issue 合集**：✅ 已完成（2026-11-06）——`compat/connector-issues.md`（6 个 L2 案例，含环境表、
  根因、字节码证据、建议修法、提 issue 需要附的材料）"""
assert old_c in t
t = t.replace(old_c, new_c, 1)

# 4) 交接要点：基线列表补 66jar
old_b = "与 **`compat/baseline-57jar.json`（57 jar，2026-11-05 18:57 启动，当前基线）**"
new_b = ("与 `compat/baseline-57jar.json`（57 jar）和 **`compat/baseline-66jar.json`"
         "（66 jar，2026-11-06 12:03 启动，当前基线）**")
assert old_b in t
t = t.replace(old_b, new_b, 1)

p.write_text(t, encoding='utf-8')
print('HANDOFF + corpus updated')
