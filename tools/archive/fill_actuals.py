"""把评测台的实测结果回填到 corpus.json（actual_verdict / actual_reason / actual_layer / run_id）。"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "compat" / "corpus.json"


def layer_of(reason, fatal):
    text = " ".join(fatal or [])
    if reason == "ok":
        return "none"
    if "requires version" in text or "pre-loading phase" in text or "incompatible" in text:
        return "L0"
    if "Mixin apply for mod" in text or "MixinTransformerError" in text or "FAILED during APPLY" in text:
        return "L2"
    if "Could not execute entrypoint" in text:
        return "L1"
    if reason == "sample_not_loaded":
        return "L4?"
    return "?"


def main(run_json):
    run_dir = Path(run_json).parent
    results = json.loads(Path(run_json).read_text("utf-8"))
    by = {r["sample"]: r for r in results}
    data = json.loads(CORPUS.read_text("utf-8"))
    n = 0
    for r in data["main"]:
        s = by.get(r["slug"])
        if not s:
            continue
        r["actual_verdict"] = s["verdict"]
        r["actual_reason"] = s["reason"]
        r["actual_layer"] = layer_of(s["reason"], s.get("fatal"))
        r["actual_run"] = run_dir.name
        r["actual_sample_loaded"] = s.get("sample_loaded")
        n += 1
    for c in data.get("negative_controls") or []:
        s = by.get(c["slug"])
        if s:
            c["observed"] = {"verdict": s["verdict"], "reason": s["reason"],
                             "fatal": (s.get("fatal") or [None])[0], "run": run_dir.name}
    data.setdefault("last_run", {})["dir"] = str(run_dir)
    data["last_run"]["auto_pass"] = sum(1 for r in results if r["verdict"] == "pass")
    data["last_run"]["auto_n"] = len(results)
    CORPUS.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    print("filled %d samples from %s" % (n, run_dir.name))
    for r in results:
        print("  %-34s %-5s %-20s layer=%s" % (r["sample"], r["verdict"], r["reason"],
                                               layer_of(r["reason"], r.get("fatal"))))


if __name__ == "__main__":
    main(sys.argv[1])
