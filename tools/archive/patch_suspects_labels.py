import pathlib
import re

p = pathlib.Path(r"D:\SuperLoader\core\suspects.py")
t = p.read_text(encoding="utf-8")

start = t.index("def compact(report: dict, limit: int = 8) -> dict:")
end = t.index("def summary_lines(compact_report: dict) -> list[str]:")
new_compact = '''REASON_LABEL = {
    "mixin_transform_failed": "Connector 转换 jar 失败",
    "mixin_failed": "mixin 应用失败",
    "mod_not_loaded": "没进 ModList",
    "fabric_dep_missing": "依赖不满足",
    "refmap_unverified": "refmap 校验未通过",
    "class_conflict": "类冲突",
    "crash_frame": "崩溃栈里出现",
    "log_error": "控制台异常",
}

_EVIDENCE_PRIORITY = ("Caused by:", "Failed to execute task", "Encountered error",
                      "Error transforming", "Exception", "Error")


def _pick_evidence(evidence: list[str], limit: int = 2) -> list[str]:
    """挑最像根因的行：`Caused by` / `Failed to execute task` / 异常消息优先。"""
    ranked = sorted(evidence, key=lambda e: next(
        (i for i, k in enumerate(_EVIDENCE_PRIORITY) if k in e), len(_EVIDENCE_PRIORITY)))
    out = []
    for e in ranked:
        text = " ".join(e.split())
        if text not in out:
            out.append(text[:240])
        if len(out) >= limit:
            break
    return out


def compact(report: dict, limit: int = 8) -> dict:
    items = (report or {}).get("suspects") or []
    packed = []
    for it in items[:limit]:
        findings = []
        seen = set()
        for r in it.get("reasons") or []:
            code = r.get("code") or ""
            if code in seen:
                continue
            seen.add(code)
            findings.append({"code": code,
                             "label": REASON_LABEL.get(code, code),
                             "layer": r.get("layer") or ""})
        packed.append({
            "mod_id": it.get("mod_id"),
            "jar": it.get("jar"),
            "severity": it.get("severity"),
            "findings": findings,
            "reasons": [r.get("detail") for r in it.get("reasons") or []],
            "layers": [r.get("layer") for r in it.get("reasons") or []],
            "evidence": _pick_evidence(list(it.get("evidence") or [])),
            "manual_check": it.get("manual_check"),
        })
    return {"count": (report or {}).get("count", len(items)), "items": packed}


'''
t = t[:start] + new_compact + t[end:]

start = t.index("def summary_lines(compact_report: dict) -> list[str]:")
new_summary = '''def summary_lines(compact_report: dict) -> list[str]:
    items = (compact_report or {}).get("items") or []
    if not items:
        return ["  无：本次启动没有模组级异常（静默功能失效仍需人工确认核心功能）"]
    out = [f"  {len(items)} 个（只核这几项，不用逐个点）"]
    for it in items:
        sev = {"high": "高", "medium": "中", "low": "低"}.get(it.get("severity"), "?")
        out.append(f"  - {it.get('mod_id')}（{it.get('jar') or '?'}）  {sev}")
        labels = []
        for f in it.get("findings") or []:
            layer = f"[{f['layer']}] " if f.get("layer") else ""
            labels.append(f"{layer}{f['label']}")
        if labels:
            out.append("      判定: " + "；".join(labels))
        for ev in (it.get("evidence") or [])[:2]:
            out.append(f"      证据: {ev}")
        if it.get("manual_check"):
            out.append(f"      人工抽查: {it['manual_check']}")
    return out
'''
t = t[:start] + new_summary
p.write_text(t, encoding="utf-8")
print("ok")
