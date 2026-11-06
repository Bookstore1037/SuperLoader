# core/classloading.py
"""classloading 板块 v1：静态重复类扫描 + 运行期 ClassLoader 归属。

两块数据，来源完全分开：

  1. 运行期归属（companion 的 runtime.json）
     companion 用 `Class.forName` 探 7 个代表类，记录实际定义它的 ClassLoader
     （类名 + identityHashCode）。同一个 identity = 同一个 ClassLoader 实例，
     可以据此把 MC / companion / NeoForge / Connector / Fabric 分层。
     这是"运行期事实"，Python 只做归组和分层推断，不新增探测。

  2. 静态重复类（Python 扫 jar）
     扫 `mods/*.jar` 及 `META-INF/jars|jarjar/` 嵌套 jar 的 `.class` 条目，找同名类。
     判据**只看结构，不看包名**：同名类里只要顶层 jar 出现 >= 2 个才算冲突；
     顶层与嵌套、或嵌套与嵌套之间共存都是 jar-in-jar（Fabric 生态常态），记为 filtered。
     `reloc/` 与 fabric loader 前缀规则只用于给 jar-in-jar 再分一次子类，
     不再决定"是不是冲突"——前缀是开放集合，白名单补不完。
     另外做一次 mods 类 vs `libraries/` classpath 类的交叉，报真正会撞名的类。

v1 不做（需要运行期字节码/ClassLoader 枚举）：每个类"实际由哪个 jar 加载"、
mixin 生成类、ClassLoader 的 parent 链。
"""
import io
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CL_SCHEMA = 1

_NESTED_PREFIXES = ("META-INF/jars/", "META-INF/jarjar/")

# 前缀规则现在只用于 jar-in-jar 的子分类标注，不参与"是否冲突"的判断
_NOISE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("relocated", ("reloc/", "shaded/", "shadow/")),
    ("fabric_loader", ("net/fabricmc/loader/", "net/fabricmc/api/")),
    ("library", (
        "org/slf4j/", "com/google/", "org/apache/", "io/netty/", "it/unimi/",
        "org/lwjgl/", "com/mojang/", "org/joml/", "org/objectweb/", "org/jetbrains/",
        "kotlin/", "javax/", "org/spongepowered/", "net/minecraft/", "net/neoforged/",
    )),
]


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _categorize(class_name: str) -> str:
    for category, prefixes in _NOISE_RULES:
        if class_name.startswith(prefixes):
            return category
    return "mod"


def _layer_of(loader: str | None) -> str:
    loader = loader or ""
    if "TransformingClassLoader" in loader:
        return "transforming"
    if "ModuleClassLoader" in loader:
        return "module"
    if loader in ("bootstrap", "", None):
        return "bootstrap"
    return "unknown"


# ---------------------------------------------------------------- 静态扫描

def _jar_classes(zf: zipfile.ZipFile) -> tuple[list[str], int, list[tuple[str, list[str]]]]:
    """返回 (顶层类名, 嵌套 jar 数, [(嵌套 jar 名, 类名)])。"""
    top: list[str] = []
    nested: list[tuple[str, list[str]]] = []
    for name in zf.namelist():
        if name.endswith(".class"):
            top.append(name)
        elif name.startswith(_NESTED_PREFIXES) and name.endswith(".jar"):
            try:
                with zipfile.ZipFile(io.BytesIO(zf.read(name))) as nz:
                    classes = [n for n in nz.namelist() if n.endswith(".class")]
            except (zipfile.BadZipFile, KeyError, OSError):
                continue
            nested.append((Path(name).name, classes))
    return top, len(nested), nested


def _scan_mods(paths) -> dict:
    """扫 mods 目录，返回 jar 统计、类 -> 出现位置、重复类。"""
    jar_stats: list[dict] = []
    occurrences: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    if not paths.mods.is_dir():
        return {"jars": [], "classes_top_level": 0, "classes_nested": 0,
                "duplicates": {}, "occurrences": occurrences}

    for jar in sorted(paths.mods.glob("*.jar")):
        try:
            with zipfile.ZipFile(jar) as zf:
                top, nested_count, nested = _jar_classes(zf)
        except (zipfile.BadZipFile, OSError):
            jar_stats.append({"jar": jar.name, "classes_top_level": 0,
                              "nested_jars": 0, "classes_nested": 0, "error": "无法读取"})
            continue
        for name in top:
            occurrences[name].append((jar.name, None))
        for nested_jar, classes in nested:
            for name in classes:
                occurrences[name].append((jar.name, nested_jar))
        jar_stats.append({
            "jar": jar.name,
            "classes_top_level": len(top),
            "nested_jars": nested_count,
            "classes_nested": sum(len(c) for _, c in nested),
        })

    duplicates = {name: places for name, places in occurrences.items() if len(places) > 1}
    return {
        "jars": jar_stats,
        "classes_top_level": sum(j["classes_top_level"] for j in jar_stats),
        "classes_nested": sum(j["classes_nested"] for j in jar_stats),
        "duplicates": duplicates,
        "occurrences": occurrences,
    }


def _scan_library_classes(paths) -> tuple[int, int, set[str]]:
    """扫 libraries/ 下的 classpath jar，返回 (jar 数, 类数, 类名集合)。"""
    if not paths.libraries.is_dir():
        return 0, 0, set()
    jars = 0
    classes: set[str] = set()
    for jar in paths.libraries.rglob("*.jar"):
        jars += 1
        try:
            with zipfile.ZipFile(jar) as zf:
                for name in zf.namelist():
                    if name.endswith(".class"):
                        classes.add(name)
        except (zipfile.BadZipFile, OSError):
            continue
    return jars, len(classes), classes


def _display(member: str) -> str:
    """com/example/Foo.class -> com.example.Foo"""
    name = member[:-6] if member.endswith(".class") else member
    return name.replace("/", ".")


def _occurrence_label(place: tuple[str, str | None]) -> str:
    jar, nested = place
    return f"{jar}!{nested}" if nested else jar


def _duplicate_section(scan: dict, library_classes: set[str]) -> dict:
    """按结构判据归类同名类，前缀规则只做子分类标注。

    判据只看 occurrences 里的 `nested` 字段（与包名无关）：
      - 顶层 jar >= 2 个        → conflict（真冲突，进 reported）
      - 顶层 + 嵌套、或嵌套之间  → jar_in_jar（jar-in-jar 共存，Fabric 生态常态）
    """
    duplicates = scan["duplicates"]
    reported: list[dict] = []
    filtered: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    pairs: Counter = Counter()

    for name, places in sorted(duplicates.items()):
        pairs[tuple(sorted({_occurrence_label(p) for p in places}))] += 1
        top = [p for p in places if p[1] is None]
        if len(places) < 2:
            continue
        if len(top) >= 2:
            reported.append({
                "class": _display(name),
                "category": "conflict",
                "occurrences": [{"jar": p[0], "nested": p[1]} for p in places],
            })
            continue
        # 其余都是 jar-in-jar（顶层 vs 嵌套，或嵌套 vs 嵌套）
        prefix = _categorize(name)
        label = prefix if prefix in ("relocated", "fabric_loader") else "jar_in_jar"
        filtered[label] += 1
        if len(examples[label]) < 5:
            examples[label].append(name)

    conflicts = [
        {"class": _display(name),
         "occurrences": [{"jar": p[0], "nested": p[1]} for p in places]}
        for name, places in sorted(duplicates.items())
        if name in library_classes and any(p[1] is None for p in places)
    ]

    return {
        "total": len(duplicates),
        "reported": reported,
        "filtered": {
            "count": sum(filtered.values()),
            "by_category": dict(filtered.most_common()),
            "examples": {k: [_display(c) for c in v] for k, v in examples.items()},
        },
        "jar_pairs": [
            {"jars": list(jars), "count": count}
            for jars, count in pairs.most_common(10)
        ],
        "classpath_conflicts": conflicts,
    }


# ---------------------------------------------------------------- 运行期归属

def _runtime_section(runtime: dict | None) -> dict:
    probes = []
    for item in (runtime or {}).get("classloading") or []:
        if not isinstance(item, dict):
            continue
        probe = dict(item)
        probe["layer"] = _layer_of(item.get("loader"))
        probes.append(probe)

    groups: dict[tuple[str, int | None], list[dict]] = defaultdict(list)
    for probe in probes:
        key = (probe.get("loader") or "unknown", probe.get("loader_identity"))
        groups[key].append(probe)

    loaders = []
    for (loader, identity), items in sorted(groups.items(),
                                           key=lambda kv: (-len(kv[1]), str(kv[0]))):
        loaders.append({
            "loader": loader,
            "identity": identity,
            "layer": _layer_of(loader),
            "roles": [p.get("role") for p in items],
            "classes": [p.get("class") for p in items],
        })

    return {
        "probes": probes,
        "loaders": loaders,
        "layers": dict(Counter(p["layer"] for p in probes)),
        "note": "companion 只探了代表类；identity 相同 = 同一个 ClassLoader 实例",
    }


# ---------------------------------------------------------------- 入口

def build_classloading(paths, runtime: dict | None) -> dict:
    scan = _scan_mods(paths)
    library_jars, library_classes_count, library_classes = _scan_library_classes(paths)
    runtime_section = _runtime_section(runtime)
    static = {
        "scope": "mods/*.jar + META-INF/jars|jarjar 嵌套 jar",
        "jars": scan["jars"],
        "classes_top_level": scan["classes_top_level"],
        "classes_nested": scan["classes_nested"],
        "duplicates": _duplicate_section(scan, library_classes),
        "classpath": {
            "jars": library_jars,
            "classes": library_classes_count,
        },
    }

    report = {
        "schema": CL_SCHEMA,
        "generated_at": _now(),
        "runtime_stage": (runtime or {}).get("stage"),
        "runtime_generated_at": (runtime or {}).get("generated_at"),
        "runtime": runtime_section,
        "static": static,
        "totals": {
            "probes": len(runtime_section["probes"]),
            "loaders": len(runtime_section["loaders"]),
            "jars": len(static["jars"]),
            "classes_scanned": static["classes_top_level"] + static["classes_nested"],
            "duplicate_classes": static["duplicates"]["total"],
            "duplicate_reported": len(static["duplicates"]["reported"]),
            "duplicate_filtered": static["duplicates"]["filtered"]["count"],
            "classpath_conflicts": len(static["duplicates"]["classpath_conflicts"]),
        },
        "issues": [],
    }

    issues = report["issues"]
    if not runtime:
        issues.append({"severity": "warn", "code": "runtime_missing",
                       "message": "runtime.json 缺失：只有静态扫描，没有运行期 ClassLoader 归属"})
    for item in static["duplicates"]["reported"]:
        issues.append({
            "severity": "warn", "code": "duplicate_top_level_class",
            "message": f"顶层 jar 撞类: {item['class']} "
                       f"({', '.join(_occurrence_label((o['jar'], o['nested'])) for o in item['occurrences'])})"})
    for item in static["duplicates"]["classpath_conflicts"]:
        issues.append({
            "severity": "warn", "code": "classpath_conflict",
            "message": f"mod 类与 classpath 冲突: {item['class']}"})
    return report


def compact(report: dict) -> dict:
    runtime = report.get("runtime") or {}
    static = report.get("static") or {}
    duplicates = static.get("duplicates") or {}
    return {
        "probes": runtime.get("probes") or [],
        "loaders": runtime.get("loaders") or [],
        "layers": runtime.get("layers") or {},
        "static": {
            "jars": (report.get("totals") or {}).get("jars", 0),
            "classes_scanned": report.get("totals", {}).get("classes_scanned", 0),
            "duplicate_classes": duplicates.get("total", 0),
            "duplicate_reported": len(duplicates.get("reported") or []),
            "duplicate_filtered": (duplicates.get("filtered") or {}).get("count", 0),
            "classpath_conflicts": len(duplicates.get("classpath_conflicts") or []),
        },
        "totals": report.get("totals"),
        "issues": len(report.get("issues") or []),
    }


def summary_lines(report: dict) -> list[str]:
    runtime = report.get("runtime") or {}
    static = report.get("static") or {}
    duplicates = static.get("duplicates") or {}
    totals = report.get("totals") or {}
    lines: list[str] = []

    if not report.get("runtime_stage"):
        lines.append("  runtime.json 缺失（companion 未运行）：只有静态扫描，没有运行期归属")

    for probe in runtime.get("probes") or []:
        role = probe.get("role") or ""
        if probe.get("found") is False:
            lines.append(f"  {role:<18} {probe.get('class')}  (未找到: {probe.get('error')})")
            continue
        suffix = "  [与 companion 同层]" if probe.get("same_as_companion") else ""
        lines.append(f"  {role:<18} {probe.get('loader')}{suffix}")

    layers = runtime.get("layers") or {}
    if layers:
        lines.append(
            f"  {totals.get('loaders', 0)} 个 ClassLoader 实例（"
            + " / ".join(f"{k}={v}" for k, v in sorted(layers.items())) + "）")

    filtered = duplicates.get("filtered") or {}
    by_category = filtered.get("by_category") or {}
    filtered_text = ", ".join(f"{k}={v}" for k, v in by_category.items()) or "无"
    lines.append(
        f"  静态重复类: {totals.get('jars', 0)} 个 jar / "
        f"{totals.get('classes_scanned', 0)} 个类，重复 {duplicates.get('total', 0)}"
        f"（顶层冲突 {totals.get('duplicate_reported', 0)}，过滤 {filtered_text}）")
    lines.append(
        f"  classpath 冲突: {totals.get('classpath_conflicts', 0)}"
        f"（mods vs libraries {(static.get('classpath') or {}).get('jars', 0)} jar / "
        f"{(static.get('classpath') or {}).get('classes', 0)} 类）")

    for item in (duplicates.get("reported") or [])[:5]:
        lines.append(f"  重复: {item['class']}")
    return lines
