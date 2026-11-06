import json
import pathlib
import shutil

ROOT = pathlib.Path(r"D:\SuperLoader")
LOGS = ROOT / "compat" / "issues" / "logs"
ISS = ROOT / "compat" / "issues"
INST = pathlib.Path(r"D:\SLData\instances\1.21.1")

cases = []
for d in sorted(LOGS.iterdir()):
    if not d.is_dir() or d.name == "_base":
        continue
    r = json.loads((d / "result.json").read_text("utf-8"))
    dbg = d / "debug.log"
    cr = d / "crash-report.txt"
    cases.append(dict(
        key=d.name, exit=r["exit_code"], elapsed=r["elapsed_s"], typed=r.get("typed"),
        report=r.get("crash_report"), jars=r["jars"],
        debug_kb=round(dbg.stat().st_size / 1024) if dbg.exists() else None,
        crash_kb=round(cr.stat().st_size / 1024) if cr.exists() else None,
        hints=r.get("hints") or [],
    ))

# 1) patch the Logs section of each draft
for c in cases:
    f = ISS / f"{c['key']}.md"
    t = f.read_text("utf-8")
    start = t.find("### Logs")
    end = t.find("### Additional context")
    if start < 0 or end < 0:
        print("skip", f.name)
        continue
    block = f"""### Logs

Collected with a minimal setup (see "Steps to reproduce") and stored locally in
`compat/issues/logs/{c['key']}/`:

- `debug.log` — NeoForge debug log of the crashing run ({c['debug_kb']} KB)
- `crash-report.txt` — copy of `crash-reports/{c['report']}` ({c['crash_kb']} KB)

_To be uploaded to a Gist / paste site before submitting (the tracker does not accept file uploads)._

"""
    t = t[:start] + block + t[end:]
    f.write_text(t, encoding="utf-8")

# 2) index for the logs folder
rows = "\n".join(
    f"| {c['key']} | {c['exit']} | {c['report']} | {c['debug_kb']} KB | {c['crash_kb']} KB | "
    f"{'是（自动按键触发）' if c['typed'] else '否'} |" for c in cases)
readme = f"""# Minimal-set run artifacts

每份 issue 草稿用最小集复跑一次，产物在各自的子目录里：

- `debug.log`：本次启动的 NeoForge debug 日志
- `crash-report.txt`：`D:\\SLData\\instances\\1.21.1\\crash-reports\\` 里对应那份的副本
- `latest.log`：普通日志（备用）
- `run.log`：启动器输出
- `result.json`：退出码 / 用时 / 装入的 jar 列表

| 案例 | 退出码 | crash report | debug.log | crash | 是否需按键 |
|------|--------|--------------|-----------|-------|------------|
{rows}

复跑脚本：`python tools/run_minimal_sets.py [--only <case>] [--restore]`（会清空实例 `mods/` 只放
Connector + FFAPI + 该案例的模组，玩家的整包在 `mods.bak` 里不受影响）。

提交前把 `debug.log` 和 `crash-report.txt` 传到 Gist / mclo.gs，把链接填进对应草稿的 `### Logs`。
"""
(LOGS / "README.md").write_text(readme, encoding="utf-8")

# 3) restore the player's pack
bak = INST / "mods.bak"
mods = INST / "mods"
if bak.exists():
    for p in mods.glob("*.jar"):
        p.unlink()
    moved = 0
    for p in sorted(bak.glob("*.jar")):
        shutil.move(str(p), str(mods / p.name))
        moved += 1
    try:
        bak.rmdir()
    except OSError:
        pass
    print("restored jars:", moved)
else:
    print("no mods.bak")

print("mods jars now:", len(list(mods.glob("*.jar"))))
