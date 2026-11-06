# core/report.py
"""透明化报告：environment.json / mods.json / summary.txt。

数据来源分两类，互不重叠：
  1. companion mod 在 NeoForge 侧采集的 runtime.json
     （ModList / LoadingModList 公开 API：mod 清单、版本、文件、加载状态、加载问题、类加载器）
  2. Python 侧 jar 元数据扫描
     （fabric.mod.json / META-INF/neoforge.mods.toml，判断 mod 面向哪个 loader）

Python 是最终报告的唯一写入者：companion 只落原始事实，报告可以随时用
`python superloader.py report` 重新渲染，不需要重开游戏。
"""
import io
import json
import re
import textwrap
import tomllib
import zipfile
from datetime import datetime
from pathlib import Path

from core.apis import build_apis, compact as compact_apis, summary_lines as apis_summary_lines
from core.classloading import (build_classloading, compact as compact_classloading,
                               summary_lines as classloading_summary_lines)
from core.events_report import build_events, compact as compact_events, summary_lines
from core.paths import MC_VERSION, NF_VERSION, Paths
from core.suspects import (
    build_suspects,
    compact as compact_suspects,
    summary_lines as suspects_summary_lines,
)

REPORT_SCHEMA = 1


# Fabric 的 mod id 习惯用连字符，FML 的 namespace 用下划线，两边都要能查到
def _id_variants(mod_id: str) -> list[str]:
    return list({mod_id, mod_id.replace("_", "-"), mod_id.replace("-", "_")})


# ---------------------------------------------------------------- 读取运行时数据

def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def report_dir(paths: Paths) -> Path:
    return paths.instance / "logs" / "superloader-report"


# ---------------------------------------------------------------- 启动结果与新鲜度

def _parse_ts(value):
    """解析 ISO 时间戳；Python 3.13 的 fromisoformat 能吃 9 位小数秒。"""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# 只认已知的致命模式；普通 mod 的 WARN/ERROR 不该进报告
_FATAL_PATTERNS = (
    "Mixin apply for mod",
    "MixinTransformerError",
    "FAILED during APPLY",
    'Exception in thread "main"',
    "---- Minecraft Crash Report ----",
    "A fatal error has been detected",
    "Could not execute entrypoint",
    "Error during pre-loading phase",
    "Some of your mods are incompatible",
    "requires version ",
)

# 运行时抛出的异常行（crash report 里的真因），形如
#   dev.booky.stackdeobf.mappings.RemappedThrowable: Cannot invoke "..." because "stack" is null
# 不带上面的固定关键词，但比 `---- Minecraft Crash Report ----` 有用得多。
_FATAL_EXCEPTION = re.compile(
    r"^(?!\s*at\s)[A-Za-z_$][\w.$]*(?:Exception|Error|Throwable):\s", re.MULTILINE)

# 日志级别，形如 `[Thread-8/WARN]`、`[Render thread/INFO]`
_LOG_LEVEL = re.compile(r"\[(?:[^\]]*/)?(ERROR|FATAL|WARN|INFO|DEBUG|TRACE)\]")


def fatal_lines(log_path: Path, limit: int = 5) -> list[str]:
    """从 launch 控制台日志里挑出致命行（崩溃 / 致命 mixin 失败）。

    `_FATAL_EXCEPTION` 只在 ERROR/FATAL 日志块（或 crash report 块内）才算数：
    WARN 里附带的异常栈只是警告，例如 bclib 备份存档时被自己锁住文件的
    `java.io.IOException`，把它当致命行会让 summary 误报。
    """
    if not log_path.is_file():
        return []
    out: list[str] = []
    level = None
    in_crash = False
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = _LOG_LEVEL.search(line)
                if m:
                    level = m.group(1)
                if "---- Minecraft Crash Report ----" in line:
                    in_crash = True
                text = line.strip()
                if any(p in line for p in _FATAL_PATTERNS):
                    pass
                elif _FATAL_EXCEPTION.match(text) and (in_crash or level in (None, "ERROR", "FATAL")):
                    pass
                else:
                    continue
                if len(text) > 400:
                    text = text[:400] + "..."
                if text not in out:
                    out.append(text)
                if len(out) >= limit:
                    break
    except OSError:
        return []
    return out


def runtime_stale(launch: dict, runtime: dict | None):
    """本次启动有没有产出新的 runtime.json。

    None  = 没有 launch 记录，无法判断（只跑过 report）
    True  = 启动失败 / 在 common_setup 前中断，runtime.json 是上一次运行的
    False = runtime 快照产生于本次启动之后
    """
    started = _parse_ts(launch.get("started_at"))
    if started is None:
        return None
    rt = _parse_ts((runtime or {}).get("generated_at"))
    if rt is None:
        return True
    return rt < started


# ---------------------------------------------------------------- jar 元数据扫描

def _json_in_zip(zf: zipfile.ZipFile, name: str):
    try:
        with zf.open(name) as f:
            return json.load(f)
    except Exception:
        return None


def _toml_mod_ids(text: str) -> set[str]:
    try:
        data = tomllib.loads(text)
    except Exception:
        return set(re.findall(r'modId\s*=\s*"([^"]+)"', text))
    ids = set()
    mods = data.get("mods")
    if isinstance(mods, list):
        for entry in mods:
            if isinstance(entry, dict) and isinstance(entry.get("modId"), str):
                ids.add(entry["modId"])
    return ids


def _jar_meta(zf: zipfile.ZipFile) -> dict[str, dict]:
    """返回 jar 里声明的 mod id -> {types, version}。version 为 ${...} 占位符时记 None。"""
    out: dict[str, dict] = {}

    def _clean_ver(v):
        if isinstance(v, str) and v and not (v.startswith("${") and v.endswith("}")):
            return v
        return None

    fabric = _json_in_zip(zf, "fabric.mod.json")
    if isinstance(fabric, dict):
        mid = fabric.get("id")
        if isinstance(mid, str) and mid:
            rec = out.setdefault(mid, {"types": set(), "version": None})
            rec["types"].add("fabric")
            ver = _clean_ver(fabric.get("version"))
            if ver:
                rec["version"] = ver

    for candidate in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
        try:
            text = zf.read(candidate).decode("utf-8", errors="replace")
        except KeyError:
            continue
        try:
            data = tomllib.loads(text)
        except Exception:
            data = None
        mods = data.get("mods") if isinstance(data, dict) else None
        if isinstance(mods, list):
            for entry in mods:
                if not isinstance(entry, dict):
                    continue
                mid = entry.get("modId")
                if not isinstance(mid, str) or not mid:
                    continue
                rec = out.setdefault(mid, {"types": set(), "version": None})
                rec["types"].add("neoforge")
                ver = _clean_ver(entry.get("version"))
                if ver:
                    rec["version"] = ver
        else:
            for mid in re.findall(r'modId\s*=\s*"([^"]+)"', text):
                out.setdefault(mid, {"types": set(), "version": None})["types"].add("neoforge")
        break
    return out


# NeoForge 的 jar-in-jar 在 META-INF/jarjar/，旧格式和 Fabric 在 META-INF/jars/
_NESTED_PREFIXES = ("META-INF/jars/", "META-INF/jarjar/")


def _version_from_jar_name(jar_name: str) -> str | None:
    m = re.search(r'-(\d+\.\d+\.\d+[^/]*?)\.jar$', jar_name)
    return m.group(1) if m else None


def build_target_index(paths: Paths, runtime: dict | None = None) -> dict[tuple, dict]:
    """扫描实际加载的 jar 及其嵌套 jar，按 (mod_id, version) 建索引。

    jar-in-jar 生态下同名模块多版本共存是常态，单键 mod_id 必然覆盖。
    """
    index: dict[tuple, dict] = {}
    seen: set[Path] = set()

    def merge(meta: dict[str, dict], jar_name: str, container: str | None):
        for mid, info in meta.items():
            ver = info.get("version")
            if not ver:
                ver = _version_from_jar_name(jar_name)
            key = (mid, ver)
            rec = index.get(key)
            if rec is None:
                index[key] = {
                    "types": set(info["types"]),
                    "jar": jar_name,
                    "container": container,
                    "version": ver,
                }
            else:
                rec["types"] |= info["types"]

    def scan(jar: Path):
        try:
            resolved = jar.resolve()
        except OSError:
            return
        if resolved in seen:
            return
        seen.add(resolved)
        try:
            with zipfile.ZipFile(jar) as zf:
                merge(_jar_meta(zf), jar.name, None)
                for name in zf.namelist():
                    if not name.endswith(".jar"):
                        continue
                    if not name.startswith(_NESTED_PREFIXES):
                        continue
                    try:
                        with zipfile.ZipFile(io.BytesIO(zf.read(name))) as nz:
                            merge(_jar_meta(nz), Path(name).name, jar.name)
                    except zipfile.BadZipFile:
                        continue
        except (zipfile.BadZipFile, OSError):
            return

    for jar in sorted(paths.mods.glob("*.jar")):
        scan(jar)

    for mod in (runtime or {}).get("mods") or []:
        raw = (mod.get("file") or "").strip()
        if not raw:
            continue
        path = Path(raw)
        if path.is_file() and path.suffix == ".jar":
            scan(path)
    return index


def _lookup(mod_id: str, index: dict[tuple, dict]) -> tuple[list[dict], set[str]]:
    """按 id 变体合并查询，返回该 mod_id 的全部版本记录与 types 并集。"""
    variants = set(_id_variants(mod_id))
    recs: list[dict] = []
    types: set[str] = set()
    for (mid, _ver), rec in index.items():
        if mid in variants:
            recs.append(rec)
            types |= rec["types"]
    return recs, types


def _source_of(mod: dict, paths: Paths, index: dict[tuple, dict]) -> str:
    mod_id = mod.get("mod_id")
    if mod_id == "minecraft":
        return "game"
    if mod_id == "neoforge":
        return "loader"

    raw = (mod.get("file") or "").strip()
    if raw:
        try:
            rel = Path(raw).relative_to(paths.instance)
        except ValueError:
            return "external"
        top = rel.parts[0] if rel.parts else ""
        return {
            "mods": "mods_dir",
            ".cache": "connector_cache",
            "libraries": "library",
        }.get(top, "instance")

    if mod_id == "connector":
        return "mods_dir"
    recs, _ = _lookup(mod_id, index)
    if any(r.get("container") for r in recs):
        return "jar_in_jar"
    if recs:
        return "mods_dir"
    parent = (mod.get("parent_file") or "").strip()
    if parent and parent not in ("/", "\\"):
        return "jar_in_jar"
    return "unknown"


def _classify(mod_id: str, source: str, recs: list[dict], types: set[str],
              ffapi_jar: str | None) -> str:
    if mod_id == "minecraft":
        return "game"
    if mod_id == "neoforge":
        return "loader"
    if mod_id == "connector":
        return "connector"
    if types == {"fabric"}:
        return "fabric"
    if types == {"neoforge"}:
        return "neoforge"
    if len(types) == 2:
        return "both"
    if source == "connector_cache":
        return "fabric"
    if ffapi_jar and any(r.get("container") == ffapi_jar for r in recs):
        return "neoforge"
    if mod_id in ("fabric_api", "forgified_fabric_api"):
        return "neoforge"
    return "unknown"


def _connector_jar(paths: Paths) -> Path | None:
    jars = sorted(paths.mods.glob("connector-*.jar"))
    return jars[0] if jars else None


# ---------------------------------------------------------------- 组装 mods.json

def build_mods(paths: Paths, runtime: dict | None, index: dict[tuple, dict],
               stale: bool | None = None) -> dict:
    if not runtime:
        return {
            "schema": REPORT_SCHEMA,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "runtime_generated_at": None,
            "source": None,
            "count": 0,
            "by_mod_id": 0,
            "by_target": {},
            "by_source": {},
            "multi_version_mods": [],
            "mods": [],
            "issues": [],
        }

    ffapi_mod = next((m for m in runtime.get("mods") or []
                      if m.get("mod_id") == "fabric_api"), None)
    ffapi_jar = (ffapi_mod or {}).get("file_name")
    connector_jar = _connector_jar(paths)

    runtime_by_key: dict[tuple, dict] = {}
    runtime_by_id: dict[str, dict] = {}
    for mod in runtime.get("mods") or []:
        mid = mod.get("mod_id") or ""
        ver = mod.get("version")
        runtime_by_key[(mid, ver)] = mod
        runtime_by_id.setdefault(mid, mod)

    # 归一化：连字符和下划线视为同一 mod 的两个命名形式
    def _norm(mid: str) -> str:
        return mid.replace("_", "-")

    # 把 index 条目按归一化 mod_id 分组：norm_id -> [(mid, ver, rec), ...]
    grouped: dict[str, list[tuple[str, str | None, dict]]] = {}
    for (mid, ver), rec in index.items():
        grouped.setdefault(_norm(mid), []).append((mid, ver, rec))

    mods_out = []
    used_runtime: set[tuple] = set()

    for norm_id, entries in sorted(grouped.items()):
        # 同组内按版本排序，优先用 FML 侧（types 含 neoforge）的 jar/container
        entries.sort(key=lambda e: (e[1] or "", 0 if "neoforge" in e[2]["types"] else 1))

        # 收集所有版本
        versions: list[str] = []
        primary = None  # 用于取 jar/container 的主记录
        all_types: set[str] = set()
        for mid, ver, rec in entries:
            all_types |= rec["types"]
            v = ver if ver is not None else rec.get("version")
            if v is not None and v not in versions:
                versions.append(v)
            if primary is None or "neoforge" in rec["types"]:
                primary = (mid, ver, rec)

        if not primary:
            continue
        pmid, pver, prec = primary

        # runtime 匹配：优先 (mid, ver)，fallback 归一化后的 mod_id
        rt = runtime_by_key.get((pmid, pver))
        if rt is None:
            rt = runtime_by_id.get(pmid)
        if rt is None:
            # 按归一化 id 在 runtime 里找
            for rmid, rmod in runtime_by_id.items():
                if _norm(rmid) == norm_id:
                    rt = rmod
                    break
        if rt is not None:
            used_runtime.add((rt.get("mod_id") or "", rt.get("version")))

        rt_file_name = (rt or {}).get("file_name")
        rt_parent = (rt or {}).get("parent_file")
        jar = rt_file_name or prec.get("jar")
        container = rt_parent or prec.get("container")

        source = _source_of(rt or {"mod_id": pmid, "file": ""}, paths, index)
        target = _classify(pmid, source, [prec], all_types, ffapi_jar)

        mods_out.append({
            "load_order": (rt or {}).get("load_order"),
            "mod_id": pmid,
            "name": (rt or {}).get("name"),
            "version": pver if pver is not None else (
                versions[0] if versions else (rt or {}).get("version")),
            "versions": versions if len(versions) > 1 else None,
            "target": target,
            "source": source,
            "loaded": (rt or {}).get("loaded"),
            "jar": jar,
            "container": container,
            "file": ((rt or {}).get("file") or "").strip() or None,
            "file_type": (rt or {}).get("file_type"),
            "license": (rt or {}).get("license"),
            "locator": (rt or {}).get("locator"),
            "namespace": (rt or {}).get("namespace"),
        })

    # index 里没覆盖的 runtime 条目（如 minecraft / neoforge / connector）补上
    for mod in runtime.get("mods") or []:
        mid = mod.get("mod_id") or ""
        key = (mid, mod.get("version"))
        if key in used_runtime:
            continue
        # 归一化后已被覆盖的不再重复输出
        if any(_norm(m["mod_id"]) == _norm(mid) for m in mods_out):
            continue
        recs, types = _lookup(mid, index)
        source = _source_of(mod, paths, index)
        jar = (recs[0].get("jar") if recs else None) or mod.get("file_name")
        container = (recs[0].get("container") if recs else None)
        if mid == "connector":
            container = None
            if connector_jar is not None:
                jar = connector_jar.name
        mods_out.append({
            "load_order": mod.get("load_order"),
            "mod_id": mid,
            "name": mod.get("name"),
            "version": mod.get("version"),
            "versions": None,
            "target": _classify(mid, source, recs, types, ffapi_jar),
            "source": source,
            "loaded": mod.get("loaded"),
            "jar": jar,
            "container": container,
            "file": (mod.get("file") or "").strip() or None,
            "file_type": mod.get("file_type"),
            "license": mod.get("license"),
            "locator": mod.get("locator"),
            "namespace": mod.get("namespace"),
        })

    # 多版本标记：按归一化 mod_id 分组
    by_norm: dict[str, list[dict]] = {}
    for m in mods_out:
        by_norm.setdefault(_norm(m["mod_id"]), []).append(m)
    multi: list[dict] = []
    for norm_id, items in by_norm.items():
        vs: list[str] = []
        for x in items:
            vs.extend(x.get("versions") or ([x.get("version")] if x.get("version") else []))
        vs = sorted({str(v) for v in vs if v})
        if len(vs) > 1:
            for x in items:
                x["multi_version"] = True
            multi.append({"mod_id": items[0]["mod_id"], "versions": vs})

    by_target: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for m in mods_out:
        by_target[m["target"]] = by_target.get(m["target"], 0) + 1
        by_source[m["source"]] = by_source.get(m["source"], 0) + 1

    issues = list(runtime.get("issues") or [])
    if stale is False:
        # 本次启动确实产出了运行时数据：mods/ 里有 jar 却没进 ModList = 被跳过
        for m in mods_out:
            if m.get("source") == "mods_dir" and m.get("loaded") is None:
                issues.append({
                    "severity": "warn",
                    "code": "mod_not_loaded",
                    "message": f"{m['mod_id']}（{m.get('jar')}）在 mods/ 里，但不在本次 ModList 中",
                })

    return {
        "schema": REPORT_SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_generated_at": runtime.get("generated_at"),
        "stage": runtime.get("stage"),
        "count": len(mods_out),
        "by_mod_id": len(by_norm),
        "by_target": dict(sorted(by_target.items())),
        "by_source": dict(sorted(by_source.items())),
        "multi_version_mods": multi,
        "mods": mods_out,
        "issues": issues,
    }

# ---------------------------------------------------------------- 组装 environment.json

def _mod_by_id(runtime: dict | None, mod_id: str) -> dict | None:
    if not runtime:
        return None
    for mod in runtime.get("mods") or []:
        if mod.get("mod_id") == mod_id:
            return mod
    return None


def _mixin_stats(mixins: list) -> dict:
    stats = {"total": 0, "declared": 0, "applied": 0, "failed": 0, "skipped": 0, "unknown": 0}
    for m in mixins:
        stats["total"] += 1
        status = m.get("status") or "unknown"
        if status in stats:
            stats[status] += 1
        else:
            stats["unknown"] += 1
    return stats


def build_environment(paths: Paths, runtime: dict | None,
                      mods_report: dict, mixins: list) -> dict:
    connector = _mod_by_id(runtime, "connector")
    ffapi = _mod_by_id(runtime, "fabric_api")
    companion = _mod_by_id(runtime, "superloader_companion")
    system = (runtime or {}).get("system") or {}

    return {
        "schema": REPORT_SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_generated_at": (runtime or {}).get("generated_at"),
        "runtime_stage": (runtime or {}).get("stage"),
        "minecraft": MC_VERSION,
        "neoforge": NF_VERSION,
        "connector": {
            "version": connector.get("version") if connector else None,
            "jar": (_connector_jar(paths).name if _connector_jar(paths) else None),
        },
        "forgified_fabric_api": {
            "version": ffapi.get("version") if ffapi else None,
            "jar": (ffapi or {}).get("file_name"),
        },
        "companion": {
            "version": (companion or {}).get("version"),
            "jar": (companion or {}).get("file_name"),
        },
        "java": {
            "version": system.get("java_version"),
            "vendor": system.get("java_vendor"),
            "vm": system.get("java_vm"),
        },
        "os": {
            "name": system.get("os_name"),
            "arch": system.get("os_arch"),
            "version": system.get("os_version"),
        },
        "launcher": {
            "name": "SuperLoader",
            "root": str(paths.root),
            "instance": str(paths.instance),
        },
        "mods": {
            "total": mods_report.get("count", 0),
            "by_target": mods_report.get("by_target", {}),
            "by_source": mods_report.get("by_source", {}),
        },
        "mixins": _mixin_stats(mixins),
        "issues": mods_report.get("issues", []),
    }


# ---------------------------------------------------------------- summary.txt

def _wrap(items: list[str], width: int = 96, indent: str = "  ") -> str:
    if not items:
        return ""
    text = ", ".join(items)
    return "\n".join(textwrap.wrap(
        text, width=width, initial_indent=indent, subsequent_indent=indent,
        break_long_words=False, break_on_hyphens=False))


def _is_ffapi(mod: dict, ffapi_jar: str | None) -> bool:
    if mod["mod_id"] in ("fabric_api", "forgified_fabric_api"):
        return True
    return bool(ffapi_jar) and mod.get("container") == ffapi_jar


def render_summary(env: dict, mods_report: dict, mixins: list, events: dict | None = None,
                   apis: dict | None = None, classloading: dict | None = None) -> str:
    out: list[str] = []
    add = out.append

    mods = mods_report.get("mods", [])
    ffapi_mod = next((m for m in mods if m["mod_id"] == "fabric_api"), None)
    ffapi_jar = (ffapi_mod or {}).get("jar")

    add("SuperLoader 透明化报告")
    add("=" * 56)
    add(f"生成时间: {env['generated_at']}")
    add(f"实例目录: {env['launcher']['instance']}")
    launch = env.get("launch") or {}
    stale = env.get("stale")
    if env.get("runtime_stage"):
        tag = ""
        if stale is True:
            tag = "  ⚠ 上次运行（早于本次启动）"
        elif stale is False:
            tag = "  ✓ 本次启动"
        add(f"运行时数据: stage={env['runtime_stage']} @ {env.get('runtime_generated_at')}{tag}")
    else:
        add("运行时数据: 缺失（companion mod 未运行或未落盘）")
    add("")

    add("启动")
    add("-" * 56)
    if launch.get("started_at"):
        rc = launch.get("exit_code")
        rc_text = "?" if rc is None else str(rc)
        fatal = launch.get("fatal") or []
        if rc not in (0, None):
            if stale is False and not fatal:
                rc_text += "（非 0；本次数据完整、无致命行，可能是关窗/强杀路径）"
            else:
                rc_text += "（异常退出）"
        add(f"  开始 {launch['started_at']}   结束 {launch.get('finished_at') or '?'}   "
            f"退出码 {rc_text}")
        if stale is True:
            add("  ⚠ 本次启动没有产出新的运行时数据：下面的 模组/事件/APIs/类加载器")
            add("    是上一次运行的快照，不代表本次启动结果")
        elif stale is False:
            add("  运行时数据为本次启动产出")
        if fatal:
            add(f"  致命行 {len(fatal)} 条:")
            for line in fatal:
                add(textwrap.fill(line, width=110, initial_indent="    ",
                                  subsequent_indent="      "))
    else:
        add("  无 launch 记录（只跑过 report；无法判断数据新鲜度）")
    add("")

    add("环境")
    add("-" * 56)
    add(f"  Minecraft        {env['minecraft']}")
    add(f"  NeoForge         {env['neoforge']}")
    c = env.get("connector") or {}
    f = env.get("forgified_fabric_api") or {}
    add(f"  Connector        {c.get('version') or '?'}")
    add(f"  Forgified Fabric {f.get('version') or '?'}")
    cp = env.get("companion") or {}
    add(f"  Companion        {cp.get('version') or '?'}")
    java = env.get("java") or {}
    os_ = env.get("os") or {}
    add(f"  Java             {java.get('version') or '?'} ({java.get('vendor') or '?'})")
    add(f"  系统             {os_.get('name') or '?'} {os_.get('arch') or ''} "
        f"{os_.get('version') or ''}".rstrip())
    add("")

    add("模组")
    add("-" * 56)
    total = mods_report.get("count", 0)
    add(f"  总数 {total}（含 Minecraft 本体与 NeoForge 自身）")
    add("  " + "  ".join(
        f"{k}={v}" for k, v in (mods_report.get("by_target") or {}).items()))
    multi = mods_report.get("multi_version_mods") or []
    if multi:
        add(f"  多版本共存 {len(multi)} 个 mod_id: "
            + ", ".join(f"{m['mod_id']}({'/'.join(m['versions'])})" for m in multi))

    fabric = [m for m in mods if m["target"] == "fabric"]
    neoforge = [m for m in mods if m["target"] == "neoforge" and not _is_ffapi(m, ffapi_jar)]
    ffapi = [m for m in mods if _is_ffapi(m, ffapi_jar)]
    connector = [m for m in mods if m["target"] == "connector"]
    unresolved = [m for m in mods if m["target"] == "unknown"]

    if fabric:
        add(f"\n  Fabric 目标 ({len(fabric)}):")
        add(_wrap([f"{m['name']} ({m['mod_id']})" for m in fabric], indent="    "))
    if neoforge:
        add(f"\n  NeoForge 目标 ({len(neoforge)}):")
        add(_wrap([f"{m['name']} ({m['mod_id']})" for m in neoforge], indent="    "))
    if ffapi:
        add(f"\n  Forgified Fabric API ({len(ffapi)}): fabric_api 及其模块"
            f"（FML 以 jar-in-jar 加载）")
    if connector:
        add(f"\n  Connector 框架 ({len(connector)}): "
            + ", ".join(f"{m['name']} ({m['mod_id']})" for m in connector))
    if unresolved:
        add(f"\n  未能归类 ({len(unresolved)}): "
            + ", ".join(f"{m['mod_id']}" for m in unresolved))

    issues = mods_report.get("issues") or []
    stale = env.get("stale")
    note = "（上一次运行）" if stale else ""
    add(f"\n  加载问题: {len(issues)}{note}")
    for issue in issues[:10]:
        code = issue.get("code")
        if code == "mod_not_loaded":
            add(f"    [{issue.get('severity')}] {issue.get('message')}")
            continue
        add(f"    [{issue.get('severity')}] {issue.get('mod_id') or '-'}: "
            f"{issue.get('translation_key') or issue.get('cause') or ''}")
    add("")

    stats = env.get("mixins") or {}
    add("Mixins")
    add("-" * 56)
    add(f"  声明 {stats.get('total', 0)}    applied={stats.get('applied', 0)}   "
        f"failed={stats.get('failed', 0)}   skipped={stats.get('skipped', 0)}   "
        f"declared-only={stats.get('declared', 0)}")
    failed = [m for m in mixins if m.get("status") == "failed"]
    if failed:
        add(f"  失败 {len(failed)} 条:")
        for m in failed[:10]:
            add(f"    {m.get('jar')} :: {m.get('mixin')} -> {m.get('reason') or ''}")
    else:
        add("  失败: 无")
    repair = env.get("refmap_repair") or {}
    if repair:
        origins = repair.get("origins") or {}
        add(f"  refmap 修复: 缺失 {repair.get('missing_refmaps', 0)}   修补 jar {repair.get('patched', 0)}   "
            f"条目 {repair.get('entries', 0)}   校验通过 {repair.get('verified', 0)}   "
            f"校验失败 {repair.get('unverified', 0)}   无法校验 {repair.get('unverifiable', 0)}   "
            f"未解析 {repair.get('unresolved', 0)}   yarn={repair.get('yarn', '-')}")
        add(f"    来源: 玩家基线 {origins.get('player_baseline', 0)}   评测台样本 {origins.get('compat_sample', 0)}")
        if repair.get("unverified"):
            add("    ⚠ 有校验失败条目：映射表说这个成员不存在，可能是 Connector/Yarn 没收录，详见 refmap_repair.json")
        if repair.get("unresolved"):
            add("    ⚠ 有未解析条目：可能是缺 Yarn 映射或映射表里查不到，详见 refmap_repair.json")
    add("")

    add("可疑模组")
    add("-" * 56)
    for line in suspects_summary_lines(env.get("suspects") or {}):
        add(line)
    add("")

    add("事件")
    add("-" * 56)
    for line in summary_lines(events or build_events(None)):
        add(line)
    add("")

    add("APIs")
    add("-" * 56)
    for line in apis_summary_lines(apis or {}):
        add(line)
    add("")

    add("类加载器")
    add("-" * 56)
    for line in classloading_summary_lines(classloading or {}):
        add(line)
    add("")
    add(f"报告目录: {Path(env['launcher']['instance']) / 'logs' / 'superloader-report'}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- 入口

def write_reports(paths: Paths, launch: dict | None = None) -> dict:
    out_dir = report_dir(paths)
    out_dir.mkdir(parents=True, exist_ok=True)

    # launch 记录：launch 命令传入本次启动结果；report 命令复用上一次的
    if launch:
        launch = dict(launch)
    else:
        launch = _load_json(out_dir / "launch.json") or {}
    if launch:
        launch.setdefault("console_log",
                          str(paths.instance / "logs" / "superloader-launch.log"))
        launch["fatal"] = fatal_lines(Path(launch["console_log"]))
        (out_dir / "launch.json").write_text(
            json.dumps(launch, ensure_ascii=False, indent=2), encoding="utf-8")

    runtime = _load_json(out_dir / "runtime.json")
    stale = runtime_stale(launch, runtime)
    mixins = _load_json(out_dir / "mixins.json") or []
    events_report = build_events(_load_json(out_dir / "events.json"))
    index = build_target_index(paths, runtime)

    mods_report = build_mods(paths, runtime, index, stale=stale)
    apis_report = build_apis(paths, runtime, mods_report)
    classloading_report = build_classloading(paths, runtime)
    env = build_environment(paths, runtime, mods_report, mixins)
    env["events"] = compact_events(events_report)
    env["apis"] = compact_apis(apis_report)
    env["classloading"] = compact_classloading(classloading_report)
    env["launch"] = launch
    env["stale"] = stale
    env["refmap_repair"] = (_load_json(out_dir / "refmap_repair.json") or {}).get("totals") or {}
    suspects = build_suspects(
        paths,
        mods_report=mods_report,
        mixins=mixins,
        mixins_logged=_load_json(out_dir / "mixins_logged.json") or [],
        apis=apis_report,
        classloading=classloading_report,
        refmap_repair=_load_json(out_dir / "refmap_repair.json"),
        console_log=Path(launch["console_log"]) if launch.get("console_log") else None,
        fatal=launch.get("fatal") or [],
    )
    env["suspects"] = compact_suspects(suspects)
    for rep in (mods_report, events_report, apis_report, classloading_report):
        rep["stale"] = stale

    (out_dir / "mods.json").write_text(
        json.dumps(mods_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "events_report.json").write_text(
        json.dumps(events_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "apis.json").write_text(
        json.dumps(apis_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "classloading.json").write_text(
        json.dumps(classloading_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "suspects.json").write_text(
        json.dumps(suspects, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "summary.txt").write_text(
        render_summary(env, mods_report, mixins, events_report, apis_report,
                       classloading_report), encoding="utf-8")

    return {
        "mods": mods_report.get("count", 0),
        "issues": len(mods_report.get("issues") or []),
        "mixins": env["mixins"]["total"],
        "events": events_report["totals"]["event_classes"],
        "apis": len(apis_report.get("issues") or []),
        "classloading": len(classloading_report.get("issues") or []),
        "suspects": (suspects or {}).get("count", 0),
        "stale": stale,
    }