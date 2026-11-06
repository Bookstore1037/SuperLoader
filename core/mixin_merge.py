# core/mixin_merge.py
"""合并路 B1（jar 声明）和路 C（日志结果），产出最终 mixins.json。"""
import json
from pathlib import Path


def _norm(name: str) -> str:
    return (name or "").replace("/", ".").strip()


def merge(declared: list[dict], logged: list[dict]) -> list[dict]:
    """declared: mixins_declared.json 内容（路 B1）
       logged: mixins.json 内容（路 C）
       """
    # 路 B1 按 (config, mixin) 建索引
    by_key: dict[tuple[str, str], dict] = {}
    for d in declared:
        k = (d.get("config", ""), d.get("mixin", ""))
        if k not in by_key:
            by_key[k] = {
                "config": d.get("config", ""),
                "mixin": d.get("mixin", ""),
                "full_name": d.get("full_name", ""),
                "mod": d.get("mod", ""),
                "jar": d.get("jar", ""),
                "nested_jar": d.get("nested_jar", ""),
                "env": d.get("env", ""),
                "required": d.get("required", True),
                "targets": [],
                "status": "declared",
                "reason": None,
                "source": ["api"],
            }

    # 路 C 覆盖/补充
    for r in logged:
        if r.get("kind") != "mixin_apply":
            continue
        k = (r.get("config", ""), r.get("mixin", ""))
        status = r.get("status", "unknown")
        targets = r.get("targets") or []
        mod = r.get("mod", "")

        if k in by_key:
            cur = by_key[k]
            # target 合并
            for t in targets:
                if t and t not in cur["targets"]:
                    cur["targets"].append(t)
            # status 优先级：failed > skipped > applied > declared
            prio = {"failed": 4, "skipped": 3, "applied": 2, "declared": 1, "unknown": 0}
            if prio.get(status, 0) > prio.get(cur["status"], 0):
                cur["status"] = status
                if status == "failed":
                    cur["reason"] = r.get("reason")
            elif status == "failed" and not cur["reason"]:
                cur["reason"] = r.get("reason")
            if not cur["mod"] and mod:
                cur["mod"] = mod
            if "log" not in cur["source"]:
                cur["source"].append("log")
        else:
            # 路 C 有但路 B1 没有（比如框架层 mixin，或动态生成的）
            by_key[k] = {
                "config": r.get("config", ""),
                "mixin": r.get("mixin", ""),
                "full_name": "",
                "mod": mod,
                "jar": "",
                "nested_jar": "",
                "env": "",
                "required": True,
                "targets": list(targets),
                "status": status,
                "reason": r.get("reason"),
                "source": ["log"],
            }

    return list(by_key.values())


def merge_to_json(declared_path, logged_path, out_path) -> dict:
    dp = Path(declared_path)
    lp = Path(logged_path)
    declared = json.loads(dp.read_text(encoding="utf-8")) if dp.exists() else []
    logged = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else []

    merged = merge(declared, logged)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stats = {"total": len(merged)}
    for m in merged:
        stats[m["status"]] = stats.get(m["status"], 0) + 1
    return stats