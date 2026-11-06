"""Record a baseline snapshot of the instance mods/ folder plus last launch verdict.

Usage:
  python tools/make_baseline.py --out compat/baseline-36jar-v2.json \
      --manual compat/manual-checks-36jar-v2.json [--note "..."]

The verdict block is copied from the last launch/report artifacts and flagged
`covers_current_mods=false` when any jar in mods/ is newer than the last launch,
so a stale verdict is never mistaken for a fresh one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import paths as P  # noqa: E402


def sha1_of(p: pathlib.Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(p: pathlib.Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--manual", required=True)
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    paths = P.Paths(pathlib.Path(r"D:\SLData"))
    mods = paths.mods
    jars = []
    newest = 0.0
    for f in sorted(mods.glob("*.jar")):
        jars.append({"jar": f.name, "sha1": sha1_of(f)})
        newest = max(newest, f.stat().st_mtime)

    out_dir = paths.instance / "logs" / "superloader-report"
    launch = load_json(out_dir / "launch.json") or {}
    env = load_json(out_dir / "environment.json") or {}
    apis = load_json(out_dir / "apis.json") or {}
    cls = load_json(out_dir / "classloading.json") or {}
    sus = load_json(out_dir / "suspects.json") or {}

    finished = launch.get("finished_at") or ""
    covers = True
    if finished and newest:
        try:
            fin = datetime.fromisoformat(finished).timestamp()
            covers = newest <= fin
        except Exception:
            covers = None

    verdict = {
        "launch_exit_code": launch.get("exit_code"),
        "launch_fatal_count": len(launch.get("fatal") or []),
        "stale": env.get("stale"),
        "suspects": sus.get("count"),
        "apis_issues": len(apis.get("issues") or []),
        "cls_classpath_conflicts": len((cls.get("classpath_conflicts") or [])),
        "launch_finished_at": finished,
        "covers_current_mods": covers,
    }

    manual = load_json(pathlib.Path(args.manual)) or []
    data = {
        "recorded_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "mods_count": len(jars),
        "versions": {
            "companion": (env.get("companion") or {}).get("version") or "",
            "connector": (env.get("connector") or {}).get("version") or "",
            "ffapi": (env.get("forgified_fabric_api") or {}).get("version") or "",
        },
        "jars": jars,
        "verdict": verdict,
        "manual_checks": manual,
        "note": args.note,
    }
    out = pathlib.Path(args.out)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("written %s jars=%d covers_current_mods=%s manual=%d" % (out, len(jars), covers, len(manual)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
