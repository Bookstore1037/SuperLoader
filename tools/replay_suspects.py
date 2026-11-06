"""Replay three known negative examples through core.suspects without launching the game.

Case A (L0): real log from 2026-11-04-6.log.gz - connectiblechains vs cloth-config 15.0.127.
Case B (L2): launch.json fatal line from the user's fallingleaves run (stale snapshot case,
             console log absent) - must be attributed via launch["fatal"].
Case C (L2): the replaymod run's console log (superloader-launch.log) - fatal line is only
             the crash-report header, attribution must come from the `at TRANSFORMER/...`
             stack frames, not from fatal[].
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import suspects as S  # noqa: E402
from core.paths import load_paths  # noqa: E402

LOGS = Path(r"D:\SLData\instances\1.21.1\logs")
FALLING = (
    "[05Nov2026 12:00:00.000] [Render thread/FATAL] [minecraft/]: Failed to access class "
    "net.minecraft.client.particle.ParticleEngine$MutableSpriteSet from class "
    "randommcsomethin.fallingleaves.mixin.SimpleSpriteProviderInvoker"
)


def run(name: str, console_log: Path | None, fatal: list[str]):
    paths = load_paths()
    report = S.build_suspects(
        paths,
        mods_report=None, mixins=None, mixins_logged=None, apis=None,
        classloading=None, refmap_repair=None,
        console_log=console_log, fatal=fatal,
    )
    print(f"\n== {name}")
    print("count:", report["count"], "scanned:", json.dumps(report["scanned"], ensure_ascii=False))
    for it in report["suspects"]:
        print(" -", it["mod_id"], it["severity"], it["reasons"])
    return report


def find_dep_log() -> Path | None:
    """找一份仍带依赖解析失败的真实日志（日志会轮转，不写死文件名）。"""
    for f in sorted(LOGS.glob("*.log*"), reverse=True):
        if not f.is_file():
            continue
        try:
            lines = S._read_log_lines(f)
        except Exception:
            continue
        if any(S.DEP_FAIL.search(l) for l in lines):
            return f
    return None


def main() -> int:
    dep_log = find_dep_log() or (LOGS / "2026-11-04-6.log.gz")
    a = run("connectiblechains (L0, real log)", dep_log, [])
    b = run("fallingleaves (L2, launch fatal only)", None, [FALLING])
    # replaymod：fatal[] 里只有 "---- Minecraft Crash Report ----"，必须靠栈帧归属
    c = run("replaymod (L2, crash frames in launch log)",
            LOGS / "superloader-launch.log", ["---- Minecraft Crash Report ----"])
    ok_a = any(s["mod_id"] == "connectiblechains" and any(r.get("layer") == "L0" for r in s["reasons"]) for s in a["suspects"])
    ok_b = any(s["mod_id"] == "fallingleaves" and any(r.get("layer") == "L2" for r in s["reasons"]) for s in b["suspects"])
    ok_c = any(s["mod_id"] == "replaymod" and any(r.get("layer") == "L2" for r in s["reasons"]) for s in c["suspects"])
    print("\nA(L0 connectiblechains):", "PASS" if ok_a else "FAIL")
    print("B(L2 fallingleaves):", "PASS" if ok_b else "FAIL")
    print("C(L2 replaymod):", "PASS" if ok_c else "FAIL")
    return 0 if (ok_a and ok_b and ok_c) else 1


if __name__ == "__main__":
    raise SystemExit(main())
