"""人工验收覆盖检查：把实例 mods/ 的 jar 与 compat/corpus.json 的样本、manual_results 对齐。

用法：
    python tools/manual_coverage.py            # 打印表格
    python tools/manual_coverage.py --json     # 机器可读
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODS = pathlib.Path(r"D:\SLData\instances\1.21.1\mods")
RUNTIME = ("connector-", "forgified-fabric-api", "superloader_companion")
# corpus 的 slug 与 jar 里的 mod id 不一致时的别名（其余靠去掉 -/_ 后精确或包含匹配）
ALIAS = {
    "yacl": "yet_another_config_lib_v3",
    "stackdeobf": "stackdeobfuscator",
    "universal-graves": "graves",
    "hold-my-items": "hmi",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def scan_mods() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(MODS.glob("*.jar")):
        if p.name.startswith(RUNTIME):
            continue
        fid, ver, kind = p.stem, None, "?"
        try:
            with zipfile.ZipFile(p) as zf:
                names = zf.namelist()
                if "fabric.mod.json" in names:
                    fmj = json.loads(zf.read("fabric.mod.json").decode("utf-8", "replace"), strict=False)
                    fid, ver, kind = fmj.get("id") or fid, fmj.get("version"), "fabric"
                elif "META-INF/neoforge.mods.toml" in names or "META-INF/mods.toml" in names:
                    kind = "neoforge"
        except Exception:
            pass
        out[fid.lower()] = {"jar": p.name, "version": ver, "kind": kind, "norm": norm(fid)}
    return out


def main() -> int:
    corpus = json.loads((ROOT / "compat" / "corpus.json").read_text("utf-8"))
    results = {r["slug"]: r for r in corpus.get("manual_results", [])}
    mods = scan_mods()
    by_norm = {}
    for mid, info in mods.items():
        by_norm.setdefault(info["norm"], mid)

    def resolve(slug: str, eid: str) -> str | None:
        """精确 → 别名 → 去掉 -/_ 后的包含匹配（只接受唯一命中）。"""
        for cand in (slug, eid, ALIAS.get(slug, "")):
            n = norm(cand)
            if not n:
                continue
            if n in by_norm:
                return by_norm[n]
            hits = [mid for mid, info in mods.items()
                    if n in info["norm"] or info["norm"] in n]
            if len(hits) == 1:
                return hits[0]
        return None

    rows = []
    for group in ("main", "infra", "content_phase2"):
        for e in corpus.get(group, []):
            slug = e.get("slug") or ""
            mid = resolve(slug, e.get("id") or "")
            r = results.get(slug) or {}
            rows.append({
                "group": group, "slug": slug, "jar": mods[mid]["jar"] if mid else "",
                "id": mid or "", "version": mods[mid]["version"] if mid else "",
                "verdict": r.get("result") or "", "date": r.get("date") or "",
                "check": e.get("check") or "", "mode": e.get("verdict_mode") or "",
            })

    known = {r["jar"] for r in rows if r["jar"]}
    extra = [i for i in mods.values() if i["jar"] not in known]

    if "--json" in sys.argv:
        print(json.dumps({"rows": rows, "extra": extra}, ensure_ascii=False, indent=1))
        return 0

    main_rows = [r for r in rows if r["group"] == "main"]
    auto_rows = [r for r in main_rows if r["mode"] == "auto"]
    manual_rows = [r for r in main_rows if r["mode"] != "auto"]
    tested = [r for r in manual_rows if r["verdict"]]
    pending = [r for r in manual_rows if r["jar"] and not r["verdict"]]
    absent = [r for r in rows if not r["jar"]]

    print(f"manual 已测 {len(tested)}/{len(manual_rows)}  待核 {len(pending)}  |  "
          f"auto 样本 {len(auto_rows)}（回归用，不算人工）  |  未装 {len(absent)}")
    print("\n== 待人工核 ==")
    for r in pending:
        print(f"  {r['slug']:36s} {r['jar']}")
    print("\n== 已测 ==")
    for r in tested:
        print(f"  {r['verdict']:10s} {r['slug']:36s} {r['date']}")
    print("\n== 未装（main / 内容组） ==")
    for r in absent:
        if r["group"] == "infra":
            continue
        print(f"  {r['group']:14s} {r['slug']}")
    infra_absent = [r["slug"] for r in absent if r["group"] == "infra"]
    if infra_absent:
        print("  （infra 未单独装，按内嵌/依赖提供：" + "、".join(infra_absent) + "）")
    print("\n== 装了但不在 corpus ==")
    for i in extra:
        print(f"  {i['kind']:8s} {i['jar']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
