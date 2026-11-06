"""Build compat/invoker_inner_target_scan.md: inner-class @Invoker/@Accessor targets + visibility."""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN = ROOT / "logs" / "inner_accessor_scan.json"
TINY = ROOT / "logs" / "tmp-tiny-mappings.tiny"
JAVAP = r"C:\Program Files\Java\jdk-21\bin\javap.exe"
MC_JAR = (r"D:\SLData\instances\1.21.1\libraries\net\minecraft\client"
          r"\1.21.1-20240808.144430\client-1.21.1-20240808.144430-srg.jar")
OUT = ROOT / "compat" / "invoker_inner_target_scan.md"


def inter2moj() -> dict[str, str]:
    if not TINY.exists():
        with zipfile.ZipFile(next(pathlib.Path(r"D:\SLData\instances\1.21.1\mods").glob("connector-*.jar"))) as zf:
            TINY.write_bytes(zf.read("mappings/mappings.tiny"))
    out = {}
    with TINY.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("CLASS\t"):
                p = line.rstrip("\n").split("\t")
                if len(p) >= 4:
                    out[p[2]] = p[3]
    return out


def class_flags(cls: str) -> str:
    try:
        r = subprocess.run([JAVAP, "-v", "-p", "-cp", MC_JAR, cls.replace("/", ".")],
                           capture_output=True, text=True, timeout=60)
    except Exception:
        return "?"
    for line in (r.stdout or "").splitlines():
        s = line.strip()
        if s.startswith("flags:"):
            if "ACC_PUBLIC" in s:
                return "public"
            if "ACC_INTERFACE" in s:
                return "interface"
            return "package-private"
    return "not-in-mc"


def jar_meta(path: pathlib.Path):
    try:
        with zipfile.ZipFile(path) as zf:
            fmj = json.loads(zf.read("fabric.mod.json").decode("utf-8", "replace"), strict=False)
            aw_files = [n for n in zf.namelist() if n.endswith(".accesswidener")]
    except Exception:
        return None, []
    return fmj.get("accessWidener"), aw_files


def main() -> int:
    mapping = inter2moj()
    scan = json.loads(SCAN.read_text("utf-8"))
    rows = []
    for entry in scan["jars"]:
        jar = pathlib.Path(entry["jar"])
        declared, aw_files = jar_meta(jar)
        for hit in entry["hits"]:
            for t in hit["targets"]:
                inter = t.replace(".", "/")
                moj = mapping.get(inter)
                vis = class_flags(moj) if moj else "no-mapping"
                rows.append({
                    "jar": jar.name, "mixin": hit["class"], "target": t,
                    "moj": moj, "vis": vis,
                    "aw": declared or ("dead:" + ",".join(aw_files) if aw_files else ""),
                })
    rows.sort(key=lambda r: (r["vis"] != "package-private", r["jar"].lower()))

    lines = [
        "# @Invoker/@Accessor 内部类 target 扫描（2026-11-05）",
        "",
        "扫描方式：读 jar 内全部 `.class` 的常量池，挑出引用了 Mixin `Invoker`/`Accessor` 注解、",
        "且常量池里出现 `net/minecraft...$...` 描述符的类；再把 target 的 intermediary 名经 Connector 的",
        "`mappings/mappings.tiny` 翻成 mojmap，用 `javap` 读类级访问标志。**这是启发式扫描**（不解析注解结构），",
        "可能有假阳性：一个 accessor 类里同时引用了别的内部类也会被列出来。",
        "",
        f"- 命中 jar：**{scan['jars'].__len__()}**，mixin 类：**{scan['mixin_classes']}**，target 条目：**{len(rows)}**",
        f"- 其中 target 是 **package-private** 的条目：**{sum(1 for r in rows if r['vis'] == 'package-private')}**",
        "",
        "## 结论先行",
        "",
        "1. 内部类 target 本身不是失败原因：22 个 jar / 53 个 mixin 类都这么做，只有 fallingleaves 崩。",
        "2. 真正的区分点是 **target 类是否 package-private**，以及**该 mod 的 access widener 有没有被加载**。",
        "3. fallingleaves 的 `.aw` 文件在 jar 里，但 `fabric.mod.json` 没有 `accessWidener` 键 → 两边都不加载；",
        "   Connector 的 `@Invoker` target **已经正确重映射**（mapped jar 里是 `ParticleEngine$MutableSpriteSet`），",
        "   所以这不是 remap 缺口，而是访问权限缺口。",
        "",
        "## 明细",
        "",
        "| 可见性 | jar | mixin 类 | target（intermediary） | target（mojang） | accessWidener |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["vis"], r["jar"], r["mixin"].split(".")[-1], r["target"],
            (r["moj"] or "?").replace("/", "."), r["aw"] or "无"))
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT, "rows", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
