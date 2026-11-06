# core/apis.py
"""apis 板块 v1：只做可验证事实，不判断"调用是否成功"。

数据全部来自磁盘上的原始事实（jar 元数据 / runtime.json / Connector 审计文件），
所以可以离线重算，与 events / mods 板块同一套路。

三个检查项：
  1. FFAPI 模块完整性
     FFAPI jar 的 `META-INF/jars/*.jar` 里声明的模块（Forgified 版用
     `META-INF/neoforge.mods.toml`，mod id 是下划线形式）是否都出现在 ModList 里。
  2. Fabric mod depends
     `fabric.mod.json` 的 `depends` 逐条解析到：运行时 mod（归一化 `-`/`_`）、
     FFAPI/其它 jar 声明的 `provides` 别名、内置版本（minecraft / java /
     fabricloader）。版本范围做尽力而为的语义比较，无法比较时记 `satisfied=null`，
     不猜。
  3. Connector adapter 补丁数量
     Connector 自己写的 `.cache/connector/patch_audit.txt`（adapter 在 remap 时生成）。
     文件 mtime 早于本次 runtime.json 就标记 stale —— Connector 复用缓存时不会重写它，
     里面的 mixin 可能属于已经删掉的 mod（例如钠）。
"""
import json
import re
import tomllib
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

APIS_SCHEMA = 1

_NESTED_PREFIXES = ("META-INF/jars/", "META-INF/jarjar/")

_AUDIT_RE = {
    "successful": re.compile(r"^Successful:\s*(\d+)", re.M),
    "partial": re.compile(r"^Partial:\s*(\d+)", re.M),
    "failed": re.compile(r"^Failed:\s*(\d+)(?:\s*\((\d+)\s+ignored\))?", re.M),
    "success_rate": re.compile(r"Success rate:\s*([\d.]+)%"),
    "accuracy": re.compile(r"Accuracy:\s*([\d.]+)%"),
}
_METHOD_RE = re.compile(r"^Mixin method\s+(\S+)\s+(\S+)", re.M)
_IGNORED_RE = re.compile(r"^\(ignored\)\s+(\S+)\s+(\S+)", re.M)
_PROCESSOR_RE = re.compile(r">>\s*Using\s+([\w.$]+)")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _norm(mod_id: str) -> str:
    """Fabric 用连字符、FML 用下划线，统一成下划线小写比较。"""
    return (mod_id or "").replace("-", "_").lower()


# ---------------------------------------------------------------- jar 元数据

def _fabric_meta(zf: zipfile.ZipFile) -> dict | None:
    try:
        data = json.loads(zf.read("fabric.mod.json"))
    except (KeyError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("id"), str):
        return None
    provides = [p for p in (data.get("provides") or []) if isinstance(p, str)]
    depends = data.get("depends") if isinstance(data.get("depends"), dict) else {}
    return {
        "kind": "fabric",
        "id": data["id"],
        "version": data.get("version"),
        "provides": provides,
        "depends": depends,
    }


def _toml_meta(zf: zipfile.ZipFile) -> dict | None:
    text = None
    for name in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
        try:
            text = zf.read(name).decode("utf-8", errors="replace")
            break
        except KeyError:
            continue
    if text is None:
        return None
    try:
        data = tomllib.loads(text)
    except ValueError:
        return None
    mods = data.get("mods") or []
    if not isinstance(mods, list) or not mods or not isinstance(mods[0], dict):
        return None
    first = mods[0]
    provides: list[str] = []
    for entry in mods:
        for p in entry.get("provides") or []:
            if isinstance(p, str):
                provides.append(p)
    return {
        "kind": "neoforge",
        "id": first.get("modId"),
        "version": first.get("version"),
        "provides": provides,
        "depends": {},
    }


def _zip_meta(zf: zipfile.ZipFile) -> dict | None:
    return _fabric_meta(zf) or _toml_meta(zf)


def _manifest_value(zf: zipfile.ZipFile, key: str) -> str | None:
    try:
        text = zf.read("META-INF/MANIFEST.MF").decode("utf-8", errors="replace")
    except KeyError:
        return None
    for line in text.splitlines():
        if line.lower().startswith(key.lower() + ":"):
            return line.split(":", 1)[1].strip()
    return None


# ---------------------------------------------------------------- 版本范围

def _version_tuple(text) -> tuple[int, ...] | None:
    """'1.21.1' -> (1,21,1)；'0.116.15+2.3.6' -> (0,116,15)；'6.0.0-beta.2' -> (6,0,0)。"""
    if not isinstance(text, str):
        return None
    match = re.match(r"^\s*v?(\d+(?:\.\d+)*)", text)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def _compare(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    size = max(len(left), len(right))
    a = left + (0,) * (size - len(left))
    b = right + (0,) * (size - len(right))
    return (a > b) - (a < b)


def _single_constraint(version: tuple[int, ...], part: str) -> bool | None:
    match = re.match(r"^(>=|<=|>|<|=|~|\^)?\s*(.+)$", part.strip())
    if not match:
        return None
    op = match.group(1) or "="
    raw = match.group(2).strip()
    if raw in ("*", "x", "X"):
        return True
    if re.search(r"[xX*]", raw):
        # 通配符前缀：1.21.x
        prefix = _version_tuple(raw.split("x")[0].split("X")[0].rstrip("."))
        if prefix is None:
            return None
        return _compare(version[:len(prefix)], prefix) == 0
    target = _version_tuple(raw)
    if target is None:
        return None

    if op == ">=":
        return _compare(version, target) >= 0
    if op == "<=":
        return _compare(version, target) <= 0
    if op == ">":
        return _compare(version, target) > 0
    if op == "<":
        return _compare(version, target) < 0
    if op == "=":
        return _compare(version, target) == 0
    if op == "~":
        # ~1.21 -> [1.21, 1.22)；~1.21.3 -> [1.21.3, 1.22)
        upper = (target[0], target[1] + 1) if len(target) >= 2 else (target[0] + 1,)
        return _compare(version, target) >= 0 and _compare(version, upper) < 0
    if op == "^":
        upper = (target[0] + 1,) if target and target[0] > 0 else (0, target[1] + 1)
        return _compare(version, target) >= 0 and _compare(version, upper) < 0
    return None


def satisfies(version, spec) -> bool | None:
    """Fabric 风格的版本范围（空格分隔的 AND；数组表示"任一"）；无法判断返回 None。"""
    if spec is None:
        return True
    if isinstance(spec, (list, tuple)):
        # fabric.mod.json 允许 depends 值是版本字符串数组，语义为"任一满足"
        results = [satisfies(version, item) for item in spec]
        if not results:
            return True
        if any(item is True for item in results):
            return True
        return None if any(item is None for item in results) else False
    if not isinstance(spec, str):
        return None
    spec = spec.strip()
    if spec in ("", "*"):
        return True
    current = _version_tuple(version)
    if current is None:
        return None
    for part in spec.split():
        allowed = _single_constraint(current, part)
        if allowed is None:
            return None
        if not allowed:
            return False
    return True


def _fmt_range(spec) -> str:
    """depends 的 range 可能是字符串或字符串数组，打印成一行。"""
    if isinstance(spec, (list, tuple)):
        return " | ".join(str(item) for item in spec)
    return str(spec)


# ---------------------------------------------------------------- FFAPI
def _find_ffapi_jar(paths, mods_report: dict | None) -> Path | None:
    """优先用 runtime 里实际加载的 FFAPI；回退到 mods 目录前缀（离线重算）。"""
    for mod in ((mods_report or {}).get("mods") or []):
        if mod.get("mod_id") == "fabric_api":
            raw = (mod.get("file") or "").strip()
            if raw:
                path = Path(raw)
                if path.is_file():
                    return path
    jars = sorted(paths.mods.glob("forgified-fabric-api-*.jar"))
    return jars[0] if jars else None


def _ffapi_modules(jar: Path, runtime_index: dict[str, dict]) -> tuple[dict, dict[str, tuple[str, str]]]:
    """返回 (ffapi 报告段, 别名表 alias->(mod_id, version))。"""
    report = {
        "jar": jar.name,
        "version": None,
        "loader_version": None,
        "modules_total": 0,
        "modules_loaded": 0,
        "missing": [],
        "extra": [],
        "modules": [],
    }
    aliases: dict[str, tuple[str, str]] = {}
    if not jar.is_file():
        report["missing"] = [{"id": "fabric_api", "reason": "jar 不存在"}]
        return report, aliases

    try:
        with zipfile.ZipFile(jar) as zf:
            outer = _toml_meta(zf)
            if outer and outer.get("id"):
                report["version"] = (runtime_index.get(_norm(outer["id"])) or {}).get(
                    "version") or outer.get("version")
                for alias in outer.get("provides") or []:
                    aliases[_norm(alias)] = (outer["id"], report["version"] or "")
            declared_ids: list[str] = []
            for name in zf.namelist():
                if not name.endswith(".jar") or not name.startswith(_NESTED_PREFIXES):
                    continue
                try:
                    with zipfile.ZipFile(zf.open(name)) as nested:
                        meta = _toml_meta(nested) or _fabric_meta(nested)
                        if "fabric-loader" in Path(name).name and not report["loader_version"]:
                            report["loader_version"] = _manifest_value(
                                nested, "Implementation-Version")
                except (zipfile.BadZipFile, OSError, KeyError):
                    continue
                if not meta or not meta.get("id"):
                    continue
                mod_id = meta["id"]
                declared_ids.append(mod_id)
                loaded = runtime_index.get(_norm(mod_id))
                report["modules"].append({
                    "id": mod_id,
                    "jar": Path(name).name,
                    "version": (loaded or {}).get("version") or meta.get("version"),
                    "loaded": bool(loaded),
                })
                if loaded:
                    report["modules_loaded"] += 1
                else:
                    report["missing"].append({"id": mod_id, "jar": Path(name).name})
                for alias in meta.get("provides") or []:
                    aliases[_norm(alias)] = (mod_id, (loaded or {}).get("version") or "")
            report["modules_total"] = len(declared_ids)
            declared = {_norm(i) for i in declared_ids}
            report["extra"] = sorted(
                mod_id for mod_id in runtime_index
                if mod_id.startswith("fabric_") and mod_id not in declared
                and mod_id != "fabric_api")
    except (zipfile.BadZipFile, OSError):
        report["missing"] = [{"id": "fabric_api", "reason": "jar 无法读取"}]
    return report, aliases


# ---------------------------------------------------------------- Fabric depends

def _fabric_depend_mods(paths, runtime_index: dict[str, dict]) -> list[dict]:
    """扫 mods/*.jar 及其 META-INF/jars/ 嵌套 jar，取 Fabric 元数据。

    顶层 jar 即使没加载成功也纳入：dep 不满足导致加载失败时，runtime.json
    往往根本不会产出（启动在 pre-loading 阶段就崩了），只有从这里查 depends
    才能解释"为什么没加载"。嵌套 jar 仍只报实际加载的，避免 Connector 缓存/
    历史残留污染。
    """
    found: list[dict] = []

    def take(zf, jar_name: str, container: str | None):
        meta = _fabric_meta(zf)
        if not meta:
            return
        loaded = runtime_index.get(_norm(meta["id"]))
        if not loaded and container is not None:
            return  # 嵌套 jar 未加载：多半是缓存/残留，不报
        entry = {
            "mod_id": meta["id"],
            "jar": jar_name,
            "container": container,
            "version": (loaded or {}).get("version") or meta.get("version"),
            "loaded": bool(loaded),
            "depends": [],
            "unsatisfied": 0,
            "unknown": 0,
        }
        for dep_id, spec in (meta.get("depends") or {}).items():
            entry["depends"].append({"id": dep_id, "range": spec})
        found.append(entry)

    for jar in sorted(paths.mods.glob("*.jar")):
        try:
            with zipfile.ZipFile(jar) as zf:
                take(zf, jar.name, None)
                for name in zf.namelist():
                    if not name.endswith(".jar") or not name.startswith(_NESTED_PREFIXES):
                        continue
                    try:
                        with zipfile.ZipFile(zf.open(name)) as nested:
                            take(nested, Path(name).name, jar.name)
                    except (zipfile.BadZipFile, OSError, KeyError):
                        continue
        except (zipfile.BadZipFile, OSError):
            continue
    return found


def _builtins(runtime: dict | None, loader_version: str | None) -> dict[str, tuple[str, str]]:
    """内置依赖目标：id -> (version, 来源说明)。"""
    out: dict[str, tuple[str, str]] = {}

    def runtime_mod(mod_id: str):
        for mod in (runtime or {}).get("mods") or []:
            if _norm(mod.get("mod_id")) == _norm(mod_id):
                return mod
        return None

    minecraft = runtime_mod("minecraft")
    if minecraft:
        out["minecraft"] = (minecraft.get("version"), "runtime")

    system = ((runtime or {}).get("system") or {})
    if system.get("java_version"):
        out["java"] = (system["java_version"], "runtime")

    if loader_version:
        # FFAPI 内嵌 forgified-fabric-loader 的 Implementation-Version，
        # 形如 2.5.68+0.18.4+1.21.1（fork 2.5.68 + 上游 loader 0.18.4）
        out["fabricloader"] = (loader_version, "bundled")
    return out


def _resolve_dep(dep_id: str, aliases: dict[str, tuple[str, str]],
                 runtime_index: dict[str, dict],
                 builtins: dict[str, tuple[str, str]]) -> dict:
    key = _norm(dep_id)
    if key in builtins:
        version, source = builtins[key]
        return {"kind": "builtin", "id": dep_id, "version": version, "source": source}
    if key in aliases:
        target, version = aliases[key]
        return {"kind": "provided", "id": target, "version": version}
    mod = runtime_index.get(key)
    if mod:
        return {"kind": "mod", "id": mod.get("mod_id"), "version": mod.get("version")}
    return {"kind": "missing", "id": dep_id, "version": None}


def _depends_section(paths, runtime: dict | None, runtime_index: dict[str, dict],
                     aliases: dict[str, tuple[str, str]],
                     builtins: dict[str, tuple[str, str]]) -> list[dict]:
    mods = _fabric_depend_mods(paths, runtime_index)
    for mod in mods:
        for dep in mod["depends"]:
            resolved = _resolve_dep(dep["id"], aliases, runtime_index, builtins)
            dep.update({
                "resolved_kind": resolved["kind"],
                "resolved_id": resolved["id"],
                "resolved_version": resolved.get("version"),
                "satisfied": satisfies(resolved.get("version"), dep.get("range")),
            })
            if dep["satisfied"] is False:
                mod["unsatisfied"] += 1
            elif dep["satisfied"] is None:
                mod["unknown"] += 1
    mods.sort(key=lambda m: (-m["unsatisfied"], -m["unknown"], m["mod_id"]))
    return mods


# ---------------------------------------------------------------- adapter 审计

def _audit_path(paths) -> Path:
    return paths.instance / ".cache" / "connector" / "patch_audit.txt"


def _parse_audit(text: str) -> dict:
    out = {"successful": 0, "partial": 0, "failed": 0, "ignored": 0,
           "success_rate": None, "accuracy": None,
           "patched_methods": [], "ignored_methods": [], "processors": {}}

    for key in ("successful", "partial", "failed", "success_rate", "accuracy"):
        match = _AUDIT_RE[key].search(text)
        if not match:
            continue
        if key == "failed":
            out["failed"] = int(match.group(1))
            out["ignored"] = int(match.group(2) or 0)
        elif key in ("success_rate", "accuracy"):
            out[key] = round(float(match.group(1)) / 100.0, 4)
        else:
            out[key] = int(match.group(1))

    blocks = re.split(r"^Mixin method\s+", text, flags=re.M)[1:]
    for block in blocks:
        head = block.splitlines()[0] if block else ""
        parts = head.split()
        if len(parts) < 2:
            continue
        processors = _PROCESSOR_RE.findall(block)
        out["patched_methods"].append({
            "mixin_class": parts[0].replace("/", "."),
            "method": parts[1],
            "processors": [p.rsplit(".", 1)[-1] for p in processors],
        })
    for match in _IGNORED_RE.finditer(text):
        out["ignored_methods"].append({
            "mixin_class": match.group(1).replace("/", "."),
            "method": match.group(2),
        })
    out["processors"] = dict(Counter(
        p.rsplit(".", 1)[-1] for p in _PROCESSOR_RE.findall(text)).most_common())
    return out


def _adapter_section(paths, runtime: dict | None) -> dict:
    audit = _audit_path(paths)
    adapter_dir = paths.instance / ".cache" / "connector" / "adapter"
    section = {
        "audit_file": str(audit),
        "audit_generated_at": None,
        "stale": None,
        "stale_reason": None,
        "adapter_dir_files": len(list(adapter_dir.glob("*"))) if adapter_dir.is_dir() else 0,
        "successful": 0,
        "partial": 0,
        "failed": 0,
        "ignored": 0,
        "success_rate": None,
        "accuracy": None,
        "patched_methods": [],
        "ignored_methods": [],
        "processors": {},
    }
    if not audit.is_file():
        section["stale"] = True
        section["stale_reason"] = "patch_audit.txt 不存在（本次启动没有 adapter 补丁审计）"
        return section

    generated = datetime.fromtimestamp(audit.stat().st_mtime).astimezone()
    section["audit_generated_at"] = generated.isoformat(timespec="seconds")
    try:
        section.update(_parse_audit(audit.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        section["stale"] = True
        section["stale_reason"] = "patch_audit.txt 读取失败"
        return section

    runtime_at = None
    if runtime and runtime.get("generated_at"):
        try:
            runtime_at = datetime.fromisoformat(runtime["generated_at"])
        except ValueError:
            runtime_at = None
    if runtime_at is not None:
        # 留 5 分钟容差：audit 在 runtime.json 之前写，同一轮启动应为同时刻
        section["stale"] = (runtime_at - generated).total_seconds() > 300
        if section["stale"]:
            section["stale_reason"] = (
                "审计文件早于本次启动的 runtime.json；Connector 复用缓存时不会重写，"
                "里面可能包含已删除 mod 的补丁")
    return section


# ---------------------------------------------------------------- 入口

def build_apis(paths, runtime: dict | None, mods_report: dict | None) -> dict:
    report = {
        "schema": APIS_SCHEMA,
        "generated_at": _now(),
        "runtime_generated_at": (runtime or {}).get("generated_at"),
        "runtime_stage": (runtime or {}).get("stage"),
        "ffapi": {
            "jar": None, "version": None, "loader_version": None,
            "modules_total": 0, "modules_loaded": 0,
            "missing": [], "extra": [], "modules": [],
        },
        "fabric_depends": [],
        "connector_adapter": _adapter_section(paths, runtime),
        "totals": {"ffapi_missing": 0, "depends_total": 0, "depends_unsatisfied": 0,
                   "depends_unknown": 0, "adapter_patches": 0},
        "issues": [],
    }

    if not isinstance(runtime, dict) or not isinstance(runtime.get("mods"), list):
        report["issues"].append({
            "severity": "warn", "code": "runtime_missing",
            "message": "runtime.json 缺失：无法核对 FFAPI 模块与 Fabric depends"})
        report["totals"]["adapter_patches"] = len(
            report["connector_adapter"].get("patched_methods") or [])
        return report

    runtime_index: dict[str, dict] = {}
    for mod in (runtime or {}).get("mods") or []:
        if mod.get("mod_id") and mod.get("loaded") is not False:
            runtime_index[_norm(mod["mod_id"])] = mod

    ffapi_jar = _find_ffapi_jar(paths, mods_report)
    ffapi, aliases = _ffapi_modules(ffapi_jar, runtime_index) if ffapi_jar else (
        report["ffapi"], {})
    report["ffapi"] = ffapi

    builtins = _builtins(runtime, ffapi.get("loader_version"))
    depends = _depends_section(paths, runtime, runtime_index, aliases, builtins)
    report["fabric_depends"] = depends

    adapter = report["connector_adapter"]
    report["totals"] = {
        "ffapi_missing": len(ffapi.get("missing") or []),
        "depends_total": sum(len(m["depends"]) for m in depends),
        "depends_unsatisfied": sum(m["unsatisfied"] for m in depends),
        "depends_unknown": sum(m["unknown"] for m in depends),
        "adapter_patches": len(adapter.get("patched_methods") or []),
    }

    issues = report["issues"]
    for missing in ffapi.get("missing") or []:
        issues.append({"severity": "error", "code": "ffapi_module_missing",
                       "message": f"FFAPI 模块未加载: {missing.get('id')} ({missing.get('jar')})"})
    for mod in depends:
        for dep in mod["depends"]:
            if dep["satisfied"] is False:
                issues.append({
                    "severity": "error", "code": "fabric_dep_missing",
                    "message": f"{mod['mod_id']} 依赖 {dep['id']} {_fmt_range(dep.get('range'))} 未满足"
                               f"（解析到 {dep.get('resolved_id')} {dep.get('resolved_version')}）"})
            elif dep["satisfied"] is None:
                issues.append({
                    "severity": "warn", "code": "fabric_dep_unknown",
                    "message": f"{mod['mod_id']} 依赖 {dep['id']} {_fmt_range(dep.get('range'))} 无法判定"})
    if adapter.get("stale"):
        issues.append({"severity": "warn", "code": "adapter_audit_stale",
                       "message": adapter.get("stale_reason") or "adapter 审计文件过期"})
    return report


def compact(report: dict) -> dict:
    """environment.json 里只放摘要，逐模块/逐依赖数据留在 apis.json。"""
    ffapi = report.get("ffapi") or {}
    adapter = report.get("connector_adapter") or {}
    return {
        "totals": report.get("totals"),
        "ffapi": {
            "version": ffapi.get("version"),
            "loader_version": ffapi.get("loader_version"),
            "modules_total": ffapi.get("modules_total"),
            "modules_loaded": ffapi.get("modules_loaded"),
            "missing": len(ffapi.get("missing") or []),
        },
        "fabric_depends": [
            {"mod_id": m["mod_id"], "loaded": m.get("loaded"), "depends": len(m["depends"]),
             "unsatisfied": m["unsatisfied"], "unknown": m["unknown"]}
            for m in report.get("fabric_depends") or []
        ],
        "connector_adapter": {
            "successful": adapter.get("successful"),
            "partial": adapter.get("partial"),
            "failed": adapter.get("failed"),
            "ignored": adapter.get("ignored"),
            "stale": adapter.get("stale"),
            "audit_generated_at": adapter.get("audit_generated_at"),
        },
        "issues": len(report.get("issues") or []),
    }


def summary_lines(report: dict) -> list[str]:
    ffapi = report.get("ffapi") or {}
    adapter = report.get("connector_adapter") or {}
    totals = report.get("totals") or {}

    if not report.get("runtime_stage"):
        return ["  runtime.json 缺失（companion 未运行），apis 只能给出 jar 侧事实"]

    lines = [
        f"  FFAPI 模块 {ffapi.get('modules_loaded', 0)}/{ffapi.get('modules_total', 0)} 已加载"
        f"   缺失 {totals.get('ffapi_missing', 0)}"
        f"   （版本 {ffapi.get('version') or '?'}）",
        f"  Fabric depends: {len(report.get('fabric_depends') or [])} 个 mod，"
        f"{totals.get('depends_total', 0)} 条依赖，"
        f"未满足 {totals.get('depends_unsatisfied', 0)}，"
        f"无法判定 {totals.get('depends_unknown', 0)}",
        f"  Connector adapter: {adapter.get('successful', 0)} 成功 / "
        f"{adapter.get('partial', 0)} 部分 / {adapter.get('failed', 0)} 失败"
        f"（忽略 {adapter.get('ignored', 0)}）"
        + (f"   补丁方法 {totals.get('adapter_patches', 0)} 个" if totals.get("adapter_patches") else ""),
    ]
    if adapter.get("stale"):
        lines.append(f"  审计文件过期（{adapter.get('audit_generated_at') or '时间未知'}）: "
                     "数字仅供参考，详见 apis.json 的 stale_reason")
    for mod in report.get("fabric_depends") or []:
        if mod["unsatisfied"] or mod["unknown"]:
            detail = ", ".join(
                f"{d['id']} {_fmt_range(d.get('range'))}"
                + (f"（解析到 {d.get('resolved_version')}）"
                   if d.get("satisfied") is False and d.get("resolved_version") else "")
                for d in mod["depends"]
                if d.get("satisfied") is not True)
            tag = "" if mod.get("loaded", True) else "（未加载）"
            lines.append(f"  {mod['mod_id']}{tag}: {detail}")
    return lines
