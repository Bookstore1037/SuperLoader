"""v6：carpet 的 L2 假设在真实隔离下成立；mixintrace 的 L4 假设被推翻。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "compat" / "corpus.json"
data = json.loads(C.read_text("utf-8"))

for r in data.get("negative") or []:
    if r["slug"] == "carpet":
        r["expected"] = "fail"
        r["expected_layer"] = "L2"
        r["expected_reason"] = ("mixin 改 vanilla 活塞/方块更新行为（PistonStructureResolver_customStickyMixin、"
                                "Level_fillUpdatesMixin），经 Connector 重映射后 apply 失败")
        r["actual_verdict"] = "fail"
        r["actual_reason"] = "fatal_in_log"
        r["actual_layer"] = "L2"
        r["actual_run"] = "20261104-125206"
        r["hypothesis_falsified"] = False
        r.pop("note", None)
    if r["slug"] == "mixintrace":
        r["expected"] = "pass"
        r["expected_layer"] = "none"
        r["expected_reason"] = ("原假设 L4（钩 MixinService/agent 内部）被真实隔离下的实测推翻："
                                "12:52 单样本重跑 pass，loaded=true，进存档")
        r["actual_verdict"] = "pass"
        r["actual_reason"] = "ok"
        r["actual_layer"] = "none"
        r["actual_run"] = "20261104-125222"
        r["hypothesis_falsified"] = True

neg = data.get("negative") or []
falsified = data.setdefault("hypotheses_falsified", [])
falsified = [r for r in neg if r.get("hypothesis_falsified")]
data["negative"] = [r for r in neg if not r.get("hypothesis_falsified")]
data["hypotheses_falsified"] = falsified
data["rate_definition"]["negative_note"] = (
    "负例：carpet（expected=fail, L2）已实测 fail/L2；mixintrace 的 L4 假设被推翻，移入 hypotheses_falsified。"
    "另有两个 jar 级可复现负例控制见 negative_controls。")

C.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
print("negative:", [(r["slug"], r["expected"], r.get("expected_layer"), r.get("actual_verdict"), r.get("actual_layer")) for r in data["negative"]])
print("falsified:", [r["slug"] for r in data["hypotheses_falsified"]])
