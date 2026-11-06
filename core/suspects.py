"""可疑模组清单。

整包验收的用法：一次启动后，先看这一节——没有任何条目就说明"这次启动没有模组级异常"，
有的话只核这几项，不用把几十个模组逐个点一遍。

判定只用已经落盘的证据，不重启游戏：
  - mixin 应用失败（mixins_logged.json / mixins.json 里 status=failed）
  - mods/ 里有、本次 ModList 里没有（mod_not_loaded）
  - 依赖不满足（apis.json 的 issue）
  - refmap 合成/校验失败（refmap_repair.json 的 unverified/unresolved）
  - 类加载冲突（classloading.json 的 issue）
  - 控制台日志里的 ERROR/FATAL/异常，按包名归因到模组
  - 本次启动的致命行（launch.json 的 fatal[]；stale 时快照里看不到，只能靠它）
  - Fabric Loader 的依赖解析失败（HARD_DEP*/Resolution failed，归 L0）
"""

from __future__ import annotations

import gzip
import json
import re
import zipfile
from pathlib import Path

MAX_ENTRIES_PER_JAR = 600
MAX_LOG_EVIDENCE = 3
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# 原因码 → 失败层（ROADMAP §2 的 L0–L4），报告里用来告诉用户"这该由谁修"
LAYERS = {
    "mixin_failed": "L2",
    "mod_not_loaded": "L0",
    "fabric_dep_missing": "L0",
    "refmap_unverified": "L2",
    "class_conflict": "L4",
}

# 这些不是"某个模组的锅"，扫日志时跳过
INFRA_PREFIXES = (
    "net/minecraft", "com/mojang", "net/neoforged", "cpw/mods",
    "org/spongepowered", "org/sinytra", "net/fabricmc", "io/netty",
    "java/", "jdk/", "sun/", "org/lwjgl", "net/caffeinemc",
)

# 日志行里的错误级别可能是 [ERROR]、[main/ERROR]、[Render thread/FATAL] 三种写法
LOG_SUSPECT = re.compile(r"\[(?:\w[^\]/]*/)?(?:ERROR|FATAL)\]|Exception|Caused by:")
# 日志级别，形如 [Thread-8/WARN]；WARN 里附带的异常栈只是警告，不算可疑模组
LEVEL = re.compile(r"\[(?:[^\]]*/)?(ERROR|FATAL|WARN|INFO|DEBUG|TRACE)\]")
HARD_LEVEL = re.compile(r"\[(?:[^\]]*/)?(?:ERROR|FATAL)\]")
STACK_CLASS = re.compile(r"\bat\s+([A-Za-z_$][\w.$]*(?:\.[\w$]+)+)")
# FML 的崩溃栈帧形如：at TRANSFORMER/replaymod@1.21-2.6.28/com.replaymod...onGuiRender(VanillaGuiScreen.java:232)
# 这里直接带 mod id，是最可靠的归属来源；没有 TRANSFORMER 前缀时才退回包名匹配。
FML_FRAME = re.compile(r"\bat\s+TRANSFORMER/([A-Za-z0-9_.\-]+)@[^\s/]*/([A-Za-z_$][\w.$]*)\.")
# `dev.booky.stackdeobf.mappings.RemappedThrowable: Cannot invoke ...` —— 异常头前缀，
# 归属时应剥掉（否则会怪罪打印异常的那个库，比如 StackDeobf）。
_EXC_HEADER = re.compile(r"^[A-Za-z_$][\w.$]*(?:Exception|Error|Throwable):\s*")
FATAL_MARK = re.compile(r"\[(?:[^\]]*/)?FATAL\]|---- Minecraft Crash Report ----|Exception in thread ") 
# 崩溃报告 `Mixins in Stacktrace:` 段里的行：`\t\tjerozgen.languagereload.mixin.X (languagereload.mixins.json)`
# 用于"mixin 把方法注入进 MC 自己的类、栈帧里一个 mod id 都没有"的情况（languagereload 的 ClientLanguage）。
MIXIN_IN_SECTION = re.compile(r"^([A-Za-z_$][\w.$]*) \(([\w.\-]+\.json)\)$")

# Fabric/NeoForge 的依赖解析失败：HARD_DEP_NO_CANDIDATE / HARD_DEP / Resolution failed，
# 以及 NeoForge+Fabric 混合环境里更常见的 FML pre-loading 报错。这类行通常不提包名，
# 只写 mod 名/id，所以单独认，统一归 L0。
DEP_FAIL = re.compile(
    r"HARD_DEP_NO_CANDIDATE|HARD_DEP\b|Resolution failed"
    r"|Error during pre-loading phase|Some of your mods are incompatible"
    r"|requires version .* of mod ",
    re.IGNORECASE,
)
DEP_MOD_NAME = re.compile(r"\bmod ([A-Za-z0-9_.\-]+)(?: \(([A-Za-z0-9_.\-]+)\))?")
DEP_MOD_PAREN = re.compile(r"\bmod ([^()]+?) \(([^)]+)\)")


def _first_mod_key(line: str) -> str | None:
    """取一行里第一个 mod 的 id。

    优先用括号里的 id：`mod Connectible Chains (connectiblechains) 2.5.7 ...`
    括号外是显示名（带空格），直接当 id 会匹配不上。
    """
    m = DEP_MOD_PAREN.search(line)
    if m:
        return m.group(2).strip().replace("-", "_")
    m = DEP_MOD_NAME.search(line)
    if m:
        return m.group(1).replace("-", "_")
    return None


L2_TEXT = re.compile(
    r"Mixin apply for mod|InvalidInjectionException|InjectionError|failed to access class"
    r"|No refMap|Could not find any targets|MixinTransformerError|InvalidAccessorException",
    re.IGNORECASE,
)
L0_TEXT = re.compile(
    r"requires version .* of mod |HARD_DEP|Resolution failed|which is missing", re.IGNORECASE)


def _layer_for_text(text: str) -> str | None:
    """从一条致命行里猜失败层：只做"该找谁"的粗判，不做精确归因。"""
    if L2_TEXT.search(text):
        return "L2"
    if L0_TEXT.search(text):
        return "L0"
    return None


def _read_log_lines(path: Path) -> list[str]:
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                return f.read().splitlines()
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _jar_prefixes(jar: Path) -> set[str]:
    """从 jar 条目里取类所在的包目录（最多三级），作为日志归因用的前缀。

    取到目录而不是完整类名：日志里出现的往往是 `carpet.mixins.json`、`dev.isxander.yacl3` 这种
    包级名字，或者是另一个同类下的类名（`carpet.mixins.Level_fillUpdatesMixin`），
    用完整类名当前缀会匹配不到。
    """
    out: set[str] = set()
    try:
        with zipfile.ZipFile(jar) as zf:
            for i, name in enumerate(zf.namelist()):
                if i > MAX_ENTRIES_PER_JAR:
                    break
                if not name.endswith(".class") or name.startswith("META-INF/"):
                    continue
                parts = name[:-6].split("/")[:-1]
                if len(parts) < 2 or parts[-1] == "package-info":
                    continue
                out.add("/".join(parts[:3]))
    except (OSError, zipfile.BadZipFile):
        pass
    return out


def _mod_id_from_jar(jar: Path) -> str | None:
    try:
        with zipfile.ZipFile(jar) as zf:
            raw = zf.read("fabric.mod.json")
    except (OSError, KeyError, zipfile.BadZipFile):
        return None
    try:
        data = json.loads(raw.decode("utf-8", "replace"), strict=False)
    except ValueError:
        return None
    mid = data.get("id")
    return mid if isinstance(mid, str) else None


def package_index(paths) -> dict[str, dict]:
    """包名前缀 → {mod_id, jar}。优先用 connector 缓存里的已重映射 jar（与运行期一致）。"""
    index: dict[str, dict] = {}
    candidates: list[Path] = []
    cache = getattr(paths, "instance", None)
    if cache is not None:
        mapped = cache / ".cache" / "connector"
        if mapped.is_dir():
            candidates.extend(sorted(mapped.glob("*.jar")))
    mods_dir = getattr(paths, "mods", None)
    if mods_dir is not None and mods_dir.is_dir():
        candidates.extend(sorted(mods_dir.glob("*.jar")))

    seen_jars: set[str] = set()
    for jar in candidates:
        name = jar.name
        if name in seen_jars:
            continue
        seen_jars.add(name)
        mid = _mod_id_from_jar(jar)
        if not mid:
            continue
        for prefix in _jar_prefixes(jar):
            # 先到先得：重映射 jar 排在前面
            index.setdefault(prefix, {"mod_id": mid, "jar": name})
    return index


JAR_IN_LOG = re.compile(r"mods[\\/]+([A-Za-z0-9._+\-\[\] \u4e00-\u9fff]+\.jar)")


def jar_index(paths) -> dict[str, dict]:
    """jar 文件名（小写）→ {mod_id, jar}，用于日志里只写 jar 路径时的归因。

    典型形态：`Encountered error while transforming jar file .../mods/the_bumblezone-7.17.3+1.21.1-fabric.jar`
    —— 行里没有包名，只有文件名，包前缀匹配一定失败。
    """
    out: dict[str, dict] = {}
    cache = getattr(paths, "instance", None)
    dirs: list[Path] = []
    if cache is not None and (cache / ".cache" / "connector").is_dir():
        dirs.append(cache / ".cache" / "connector")
    mods_dir = getattr(paths, "mods", None)
    if mods_dir is not None and mods_dir.is_dir():
        dirs.append(mods_dir)
    for d in dirs:
        for jar in sorted(d.glob("*.jar")):
            mid = _mod_id_from_jar(jar) or _id_from_filename(jar.name)
            out.setdefault(jar.name.lower(), {"mod_id": mid, "jar": jar.name})
    return out


def _id_from_filename(name: str) -> str:
    """`the_bumblezone-7.17.3+1.21.1-fabric.jar` → `the_bumblezone`（读不到 mod id 时兜底）。"""
    stem = re.sub(r"\.jar$", "", name, flags=re.IGNORECASE)
    stem = re.sub(r"^\[[^\]]*\]\s*", "", stem)          # 去掉 `[钠] ` 这类中文前缀
    for sep in ("-", "+"):
        head = stem.split(sep, 1)[0]
        if head:
            stem = head
    return stem.strip().replace("-", "_").lower()


def _attribute_jar(line: str, jars: dict[str, dict]) -> tuple[str, str] | None:
    m = JAR_IN_LOG.search(line)
    if not m:
        return None
    name = m.group(1).strip().lower()
    info = jars.get(name)
    if info:
        return info["mod_id"], info["jar"]
    # 文件名不完全一致时（版本号/前缀差异）按去掉版本号的名字比
    key = _id_from_filename(name)
    for fname, info in jars.items():
        if _id_from_filename(fname) == key:
            return info["mod_id"], info["jar"]
    return None


def _attribute(line: str, index: dict[str, dict],
               jars: dict[str, dict] | None = None) -> tuple[str, str] | None:
    """把一行日志归因到模组：先看行里的 jar 路径，再取命中的最长包名前缀。"""
    if jars:
        hit = _attribute_jar(line, jars)
        if hit:
            return hit
    dotted = line.replace("/", ".")
    best: tuple[int, str, str] | None = None
    for prefix, info in index.items():
        p = prefix.replace("/", ".")
        if p and p in dotted:
            if best is None or len(p) > best[0]:
                best = (len(p), info["mod_id"], info["jar"])
    if best is None:
        # 栈帧里的类名再试一次
        for m in STACK_CLASS.finditer(line):
            cls = m.group(1)
            for prefix, info in index.items():
                p = prefix.replace("/", ".")
                if cls.startswith(p + "."):
                    if best is None or len(p) > best[0]:
                        best = (len(p), info["mod_id"], info["jar"])
    if best is None:
        return None
    return best[1], best[2]


def scan_console(log_path: Path, index: dict[str, dict],
                 jars: dict[str, dict] | None = None) -> dict[str, list[str]]:
    """扫控制台日志，返回 mod_id → 证据行（最多若干条）。"""
    hits: dict[str, list[str]] = {}
    if not log_path or not log_path.is_file():
        return hits
    level = None
    for line in _read_log_lines(log_path):
        m = LEVEL.search(line)
        if m:
            level = m.group(1)
        if not LOG_SUSPECT.search(line):
            continue
        # WARN/INFO 块里附带的 Exception 只是警告（如 bclib 备份存档时文件被锁），不算可疑模组
        if level not in (None, "ERROR", "FATAL") and not HARD_LEVEL.search(line):
            continue
        owner = _attribute(line, index, jars)
        if not owner:
            continue
        mod_id, _jar = owner
        bucket = hits.setdefault(mod_id, [])
        stripped = line.strip()
        if stripped not in bucket and len(bucket) < MAX_LOG_EVIDENCE:
            bucket.append(stripped[:300])
    return hits


def scan_crash_frames(log_path: Path, index: dict[str, dict],
                      mixins: list | None = None) -> dict[str, list[str]]:
    """从崩溃栈里按"最近的模组帧"归属（L2）。

    为什么需要：Render thread 崩在模组回调里时，日志里既没有 `Mixin apply for mod` 也没有
    `requires version`，fatal 行往往只有 `---- Minecraft Crash Report ----`，于是 stale=false
    时也看不到是谁崩的（connectiblechains/fallingleaves/replaymod 三次实测）。
    这里抓 FML 的 `at TRANSFORMER/<modid>@...` 帧（带 mod id，最可靠），
    没有前缀时退回包名匹配；每个 mod 只留最早出现的 3 条。

    还有一种情况：mixin 把方法注入进 MC 自己的类，栈帧写成 `TRANSFORMER/minecraft@1.21.1`，
    一个 mod id 都没有（languagereload 的 `ClientLanguage.languagereload_get` 就是）。
    这时读崩溃报告里的 `Mixins in Stacktrace:` 段，取**第一个目标类**下列出的 mixin config，
    通过 config→mod 反查归属。
    """
    hits: dict[str, list[str]] = {}
    if not log_path or not log_path.is_file():
        return hits
    known = {v["mod_id"] for v in index.values()}
    by_norm = {mid.replace("-", "_").lower(): mid for mid in known}
    config_mod = {e.get("config"): e.get("mod") for e in (mixins or []) if e.get("config")}
    lines = _read_log_lines(log_path)

    def frames_from(seq: list[str]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        active = False       # 是否正处于异常栈里（WARN 块里的栈不算）
        level = None
        for line in seq:
            if FATAL_MARK.search(line):
                continue
            m = LEVEL.search(line)
            if m:
                level = m.group(1)
            stripped = line.strip()
            if stripped.startswith("at "):
                if not active:
                    continue
                fm = FML_FRAME.match(stripped)
                mid = by_norm.get(fm.group(1).replace("-", "_").lower()) if fm else None
                if not mid:
                    owner = _attribute(stripped, index)
                    mid = owner[0] if owner else None
                if not mid:
                    continue
                bucket = out.setdefault(mid, [])
                if len(bucket) < MAX_LOG_EVIDENCE and stripped not in bucket:
                    bucket.append(stripped[:300])
                continue
            if not stripped:
                active = False
                continue
            # 异常头（`XxxException: ...` / `Caused by: ...`）开启一段栈；其余行关闭
            active = ("Exception" in stripped or "Error" in stripped or "Caused by" in stripped) \
                and level in (None, "ERROR", "FATAL")
        return out

    # 优先只认最后一份 crash report 之后的栈；日志里如果没写 crash report（或 header 之后没有栈），
    # 退回整份日志——superloader-launch.log 每次启动都会被重写，整份扫不会串轮次。
    anchor = 0
    for i, line in enumerate(lines):
        if "---- Minecraft Crash Report ----" in line:
            anchor = i
    hits = frames_from(lines[anchor:]) if anchor else {}
    if not hits:
        hits = frames_from(lines)

    # `Mixins in Stacktrace:` 的「第一个目标类」= 崩溃现场那个类，列出注入它的 mixin config。
    if config_mod:
        section_start = None
        for i in range(anchor, len(lines)):
            if "Mixins in Stacktrace:" in lines[i]:
                section_start = i
                break
        if section_start is not None:
            header = None
            for line in lines[section_start + 1:]:
                s = line.strip()
                if not s:
                    continue
                if line.startswith("\t\t") or line.startswith("        "):
                    m = MIXIN_IN_SECTION.match(s)
                    if not m or header is None:
                        continue
                    mid = config_mod.get(m.group(2))
                    if not mid:
                        continue
                    bucket = hits.setdefault(mid, [])
                    ev = f"{header} ← {m.group(1)} ({m.group(2)})"
                    if len(bucket) < MAX_LOG_EVIDENCE and ev not in bucket:
                        bucket.append(ev[:300])
                elif not line.startswith("\t"):
                    break  # 段落结束
                else:
                    if header is not None and not s.endswith(":"):
                        break
                    header = s.rstrip(":")
    return hits


TRANSFORM_FAIL = re.compile(
    r"Encountered error while transforming jar file|Failed to execute task "
    r"|Error transforming file ", re.IGNORECASE)


def scan_transform_errors(log_path: Path, jars: dict[str, dict]) -> dict[str, list[str]]:
    """抓 Connector 在启动前转换 jar 时的失败（L2）。

    形态：`Encountered error while transforming jar file ...\\mods\\<jar>` 后面跟
    `Failed to execute task <mixin class>.class` + `Caused by: ...`。这类失败发生在任何模组代码
    运行之前，控制台里既没有包名也没有 FML 帧，必须靠 jar 文件名归属。
    """
    hits: dict[str, list[str]] = {}
    if not log_path or not log_path.is_file():
        return hits
    lines = _read_log_lines(log_path)
    for i, line in enumerate(lines):
        if not TRANSFORM_FAIL.search(line):
            continue
        owner = _attribute_jar(line, jars)
        if not owner:
            continue
        mod_id, _jar = owner
        bucket = hits.setdefault(mod_id, [])
        if line.strip()[:300] not in bucket:
            bucket.append(line.strip()[:300])
        for extra in lines[i + 1:i + 40]:
            stripped = extra.strip()
            if not stripped:
                continue
            if stripped.startswith("Caused by:") or TRANSFORM_FAIL.search(stripped):
                if stripped[:300] not in bucket:
                    bucket.append(stripped[:300])
        del bucket[6:]
    return hits


def scan_dep_lines(log_path: Path, index: dict[str, dict]) -> dict[str, list[str]]:
    """抓依赖解析失败（L0），归属到日志里点名的 mod。

    NeoForge + Connector 下的典型形态：
        [Render thread/FATAL] [ne.ne.fm.ModLoader/CORE]: Error during pre-loading phase:
        Some of your mods are incompatible with the game or each other!
        - mod Connectible Chains (connectiblechains) 2.5.7+1.21.1 requires version 15.0.140
          or later of mod Cloth Config v15 (cloth_config), but only the wrong version is present: 15.0.127!
    Fabric Loader 下是 HARD_DEP_NO_CANDIDATE / HARD_DEP / Resolution failed。
    归属到"提出要求、因此加载失败"的那个 mod（行的第一个 mod 名）。
    """
    hits: dict[str, list[str]] = {}
    if not log_path or not log_path.is_file():
        return hits
    known = {v["mod_id"] for v in index.values()}
    by_key = {mid.replace("-", "_"): mid for mid in known}
    pending = 0
    for line in _read_log_lines(log_path):
        if DEP_FAIL.search(line):
            pending = 12  # 后面的 "- mod X requires ..." 明细行也收
        elif pending > 0 and line.lstrip().startswith("- mod "):
            pending -= 1
        else:
            pending = 0
            continue
        # 只认每行第一个 mod（提出要求的一方），后面的 "of mod Y" 是被依赖的那一方
        key = _first_mod_key(line)
        mid = by_key.get(key) if key else None
        if not mid:
            continue
        bucket = hits.setdefault(mid, [])
        stripped = line.strip()
        if len(bucket) < MAX_LOG_EVIDENCE and stripped not in bucket:
            bucket.append(stripped[:300])
    return hits


def build_suspects(paths, mods_report: dict | None, mixins: list | None,
                   mixins_logged: list | None, apis: dict | None,
                   classloading: dict | None, refmap_repair: dict | None,
                   console_log: Path | None, fatal: list[str] | None = None) -> dict:
    index = package_index(paths)
    jars = jar_index(paths)
    reasons: dict[str, list[dict]] = {}
    severity: dict[str, str] = {}
    console_hits = scan_console(console_log, index, jars)
    transform_hits = scan_transform_errors(console_log, jars)
    dep_hits = scan_dep_lines(console_log, index)
    frame_hits = scan_crash_frames(console_log, index, mixins)
    fatal_hits: dict[str, list[str]] = {}
    fatal_unattributed: list[str] = []
    for line in fatal or []:
        stripped = str(line).strip()
        if not stripped:
            continue
        # 异常头（`pkg.Class: message`）本身归属的是“打印这条异常的工具”，不是肇事者；
        # 真正的肇事者由崩溃栈帧（crash_frame）判定，这里只按 message 内容找线索。
        body = _EXC_HEADER.sub("", stripped) if _EXC_HEADER.match(stripped) else stripped
        owner = _attribute(body, index, jars)
        if owner:
            fatal_hits.setdefault(owner[0], []).append(stripped[:300])
        else:
            fatal_unattributed.append(stripped[:300])

    def add(mod_id: str, code: str, detail: str, sev: str = "medium",
            layer: str | None = None) -> None:
        if not mod_id:
            return
        bucket = reasons.setdefault(mod_id, [])
        if any(r["code"] == code and r["detail"] == detail for r in bucket):
            return
        bucket.append({"code": code, "detail": detail,
                       "layer": layer or LAYERS.get(code)})
        if SEVERITY_ORDER[sev] < SEVERITY_ORDER.get(severity.get(mod_id, "low"), 2):
            severity[mod_id] = sev

    # 1. mixin 应用失败
    for entry in (mixins_logged or []) + (mixins or []):
        if (entry or {}).get("status") != "failed":
            continue
        mod_id = entry.get("mod") or ""
        detail = f"{entry.get('config') or '?'} :: {entry.get('mixin') or '?'}"
        reason = (entry.get("reason") or "").strip()
        if reason:
            detail += f" -> {reason[:160]}"
        add(mod_id, "mixin_failed", detail, "high")

    # 2. mods/ 里有但没进 ModList
    for issue in (mods_report or {}).get("issues") or []:
        if (issue or {}).get("code") != "mod_not_loaded":
            continue
        mod_id = issue.get("mod_id") or ""
        add(mod_id, "mod_not_loaded", issue.get("message") or "不在本次 ModList 中", "high")

    # 3. 依赖不满足（API 表面缺口，L1）
    for issue in (apis or {}).get("issues") or []:
        mod_id = issue.get("mod") or issue.get("mod_id") or ""
        detail = issue.get("message") or issue.get("code") or "依赖问题"
        add(mod_id, str(issue.get("code") or "dep_issue"), detail, "high", layer="L1")

    # 4. refmap 合成/校验
    for entry in (refmap_repair or {}).get("mods") or []:
        bad = int(entry.get("unverified") or 0)
        unresolved = int(entry.get("unresolved") or 0)
        if not bad and not unresolved:
            continue
        mod_id = entry.get("id") or ""
        detail = f"refmap 校验失败 {bad} 条，未解析 {unresolved} 条"
        add(mod_id, "refmap_unverified", detail, "high" if bad else "medium")

    # 5. 类加载冲突
    for issue in (classloading or {}).get("issues") or []:
        detail = issue.get("message") or issue.get("code") or "类加载冲突"
        for mod_id, info in index.items():
            if mod_id in str(detail):
                add(info["mod_id"], "class_conflict", str(detail)[:200], "high")
                break

    # 6. 控制台日志
    for mod_id, evidence in console_hits.items():
        if mod_id in transform_hits:
            continue  # 同一条错误已由 mixin_transform_failed 收录
        add(mod_id, "log_error", f"控制台 {len(evidence)} 条异常", "medium",
            layer=_layer_for_text(evidence[0]))

    # 7. Fabric Loader 依赖解析失败（L0）
    for mod_id, evidence in dep_hits.items():
        add(mod_id, "fabric_dep_missing", evidence[0], "high", layer="L0")

    # 7.2 Connector 转换 jar 失败（L2，早于任何模组代码）
    for mod_id, evidence in transform_hits.items():
        add(mod_id, "mixin_transform_failed", evidence[0], "high", layer="L2")

    # 7.5 崩溃栈里的模组帧：stale=false 时 Render thread 崩在模组回调里也只有这里能归因
    for mod_id, evidence in frame_hits.items():
        add(mod_id, "crash_frame", evidence[0], "high", layer="L2")

    # 8. 本次启动的致命行：stale=true 时 runtime 快照是上一次的，只有这里能看到本次崩在哪
    for mod_id, lines in fatal_hits.items():
        add(mod_id, "fatal_in_log", lines[0], "high", layer=_layer_for_text(lines[0]))

    # 组装
    manual = _manual_checks(paths)
    items = []
    for mod_id, rs in reasons.items():
        jar = ""
        for info in index.values():
            if info["mod_id"] == mod_id:
                jar = info["jar"]
                break
        if not jar:
            for info in jars.values():
                if info["mod_id"] == mod_id:
                    jar = info["jar"]
                    break
        evidence = list(transform_hits.get(mod_id) or [])
        evidence += [e for e in (console_hits.get(mod_id) or []) if e not in evidence]
        evidence += [e for e in (dep_hits.get(mod_id) or []) if e not in evidence]
        evidence += [e for e in (fatal_hits.get(mod_id) or []) if e not in evidence]
        evidence += [e for e in (frame_hits.get(mod_id) or []) if e not in evidence]
        items.append({
            "mod_id": mod_id,
            "jar": jar,
            "severity": severity.get(mod_id, "low"),
            "reasons": rs,
            "manual_check": manual.get(mod_id),
            "evidence": evidence[:MAX_LOG_EVIDENCE],
        })
    _ROOT = {"mixin_transform_failed": 0, "mixin_failed": 1, "fabric_dep_missing": 1,
             "mod_not_loaded": 1, "crash_frame": 4, "log_error": 5}
    items.sort(key=lambda it: (min(_ROOT.get(r["code"], 3) for r in it["reasons"]),
                                SEVERITY_ORDER.get(it["severity"], 3)))
    return {
        "schema": 1,
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "count": len(items),
        "suspects": items,
        "scanned": {
            "mods_indexed": len({v["mod_id"] for v in index.values()}),
            "console_log": str(console_log) if console_log else None,
            "fatal_lines": len(fatal or []),
            "fatal_unattributed": fatal_unattributed[:5],
            "loader_dep_lines": sum(len(v) for v in dep_hits.values()),
            "crash_frames": sum(len(v) for v in frame_hits.values()),
            "transform_errors": sum(len(v) for v in transform_hits.values()),
        },
    }


def _manual_checks(paths) -> dict[str, str]:
    """从 corpus 里取人工抽查项（没有就返回空）。"""
    root = getattr(paths, "root", None)
    if root is None:
        return {}
    data = _load_json(Path(root) / "compat" / "corpus.json")
    if not isinstance(data, dict):
        return {}
    out: dict[str, str] = {}
    for group in ("main", "infra", "content_phase2"):
        for entry in data.get(group) or []:
            if not isinstance(entry, dict):
                continue
            check = entry.get("manual_check") or entry.get("check")
            if not check:
                continue
            for key in ("id", "slug", "mod_id"):
                val = entry.get(key)
                if val:
                    out.setdefault(str(val).replace("-", "_"), str(check))
    return out


REASON_LABEL = {
    "mixin_transform_failed": "Connector 转换 jar 失败",
    "mixin_failed": "mixin 应用失败",
    "mod_not_loaded": "没进 ModList",
    "fabric_dep_missing": "依赖不满足",
    "refmap_unverified": "refmap 校验未通过",
    "class_conflict": "类冲突",
    "crash_frame": "崩溃栈里出现",
    "log_error": "控制台异常",
}

_EVIDENCE_PRIORITY = ("NullPointerException", "Failed to execute task", "Caused by:",
                      "Encountered error", "Error transforming", "Exception", "Error")


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


def summary_lines(compact_report: dict) -> list[str]:
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
