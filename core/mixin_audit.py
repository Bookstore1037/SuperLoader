# core/mixin_audit.py
"""路 C：解析 superloader-launch.log，提取 mixin 应用结果。

数据源（按信息完整度排序）：
1. "Mixin apply for mod {mod} failed {config}:{mixin} from mod {mod} -> {target}: {异常}"
   —— FATAL，信息最全（mod/config/mixin/target/异常一行齐）
2. "MixinApplyError: Mixin [{config}:{mixin} from mod {mod}] from phase [{phase}] in config [{config}] FAILED during {stage}"
   —— FATAL，补 phase/config
3. "Mixing {mixin} from {config} into {target}"
   —— INFO，成功信号（verbose 才大量出现）
4. "Error loading class: {class} ({异常})"
   —— WARN，类加载失败，kind=class_load
"""
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path


# 1. Mixin apply for mod X failed ... -> T: 异常
_RE_APPLY_FAIL = re.compile(
    r"Mixin apply for mod (\S+) failed (\S+?) from mod \S+ -> (\S+): (.+)"
)

# 2. MixinApplyError: Mixin [config:mixin from mod modid] from phase [PHASE] in config [config] FAILED during STAGE
_RE_APPLY_ERROR = re.compile(
    r"MixinApplyError: Mixin \[([^\]]+?)(?: from mod ([^\]]+?))?\] "
    r"from phase \[(\w+)\] in config \[([^\]]+)\] FAILED during (\w+)"
)

# 3. Mixing X from Y into Z
_RE_MIXING = re.compile(r"Mixing (\S+) from (\S+) into (\S+)")

# 4. Error loading class: X (异常)
_RE_LOAD_ERROR = re.compile(r"Error loading class: (\S+) \((.+)\)")

# 异常类名 + 消息（用于 reason）
_RE_EXCEPTION = re.compile(r"([\w.$]+(?:Exception|Error)): (.+)")


# reason 时跳过的包装异常类
_WRAPPER_EXCEPTIONS = (
    "MixinApplyError",
    "MixinTransformerError",
    "MixinException",
)


@dataclass
class MixinRecord:
    kind: str = "mixin_apply"  # mixin_apply | class_load
    config: str = ""
    mixin: str = ""
    full_name: str = ""
    mod: str = ""
    targets: list[str] = field(default_factory=list)
    phase: str = ""
    status: str = "unknown"  # applied | failed | skipped | declared | unknown
    reason: str | None = None
    source: list[str] = field(default_factory=lambda: ["log"])


def _split_config_mixin(s: str) -> tuple[str, str]:
    """'sodium-common.mixins.json:xxx.VertexConsumerMixin' -> (config, mixin)"""
    if ":" in s:
        cfg, _, mix = s.partition(":")
        return cfg, mix
    return "", s


def _norm_class(name: str) -> str:
    """'com/mojang/...' -> 'com.mojang....'"""
    return name.replace("/", ".")


def _clean_reason(msg: str, limit: int = 200) -> str:
    msg = msg.strip()
    if len(msg) > limit:
        msg = msg[:limit] + "..."
    return msg


def _pick_reason_from_line(line: str) -> str | None:
    """从一行里提取最具体的异常类 + 消息，跳过包装异常。"""
    for m in _RE_EXCEPTION.finditer(line):
        exc_name = m.group(1)
        if any(w in exc_name for w in _WRAPPER_EXCEPTIONS):
            continue
        return f"{exc_name}: {_clean_reason(m.group(2))}"
    return None


def parse(log_text: str) -> list[MixinRecord]:
    lines = log_text.splitlines()
    records: list[MixinRecord] = []

    for line in lines:
        # 1. Mixin apply for mod X failed C:M from mod X -> T: 异常
        m = _RE_APPLY_FAIL.search(line)
        if m:
            mod, cfg_mix, target, msg = m.groups()
            cfg, mix = _split_config_mixin(cfg_mix)
            reason = _pick_reason_from_line(msg) or _clean_reason(msg)
            records.append(MixinRecord(
                kind="mixin_apply",
                config=cfg,
                mixin=mix,
                mod=mod,
                targets=[_norm_class(target)],
                status="failed",
                reason=reason,
            ))
            continue  # 这行信息最全，不再用下面的规则重复匹配

        # 2. MixinApplyError: ... FAILED during ...
        m = _RE_APPLY_ERROR.search(line)
        if m:
            mixin_ref, mod, phase, config, stage = m.groups()
            cfg, mix = _split_config_mixin(mixin_ref)
            records.append(MixinRecord(
                kind="mixin_apply",
                config=cfg or config,
                mixin=mix,
                mod=mod or "",
                phase=phase,
                status="failed",
                reason=f"MixinApplyError: FAILED during {stage}",
            ))
            continue

        # 3. Mixing X from Y into Z
        m = _RE_MIXING.search(line)
        if m:
            mixin_name, config, target = m.groups()
            records.append(MixinRecord(
                kind="mixin_apply",
                config=config,
                mixin=mixin_name,
                targets=[_norm_class(target)],
                status="applied",
            ))
            continue

        # 4. Error loading class
        m = _RE_LOAD_ERROR.search(line)
        if m:
            cls, exc = m.groups()
            reason = _pick_reason_from_line(exc) or _clean_reason(exc)
            records.append(MixinRecord(
                kind="class_load",
                targets=[_norm_class(cls)],
                status="unknown",
                reason=reason,
            ))
            continue

    return _merge(records)


_PRIORITY = {"failed": 4, "skipped": 3, "applied": 2, "declared": 1, "unknown": 0}


def _merge(records: list[MixinRecord]) -> list[MixinRecord]:
    """按 (kind, config, mixin) 聚合。

    - class_load 按 target 各自独立，不聚合。
    - mixin_apply 按 (config, mixin) 聚合，targets 合并去重。
    - status 取优先级最高的（failed > skipped > applied > declared > unknown）。
    - reason 优先保留 failed 的，其次 skipped。
    - mod/phase 取非空值补。
    """
    # class_load 独立，直接保留
    class_loads = [r for r in records if r.kind == "class_load"]
    mixin_applys = [r for r in records if r.kind == "mixin_apply"]

    by_key: dict[tuple[str, str], MixinRecord] = {}
    for r in mixin_applys:
        k = (r.config, r.mixin)
        if k not in by_key:
            by_key[k] = MixinRecord(
                kind="mixin_apply",
                config=r.config,
                mixin=r.mixin,
                full_name=r.full_name,
                mod=r.mod,
                targets=list(r.targets),
                phase=r.phase,
                status=r.status,
                reason=r.reason,
                source=list(r.source),
            )
            continue
        cur = by_key[k]
        # targets 合并去重
        for t in r.targets:
            if t and t not in cur.targets:
                cur.targets.append(t)
        # source 合并
        for s in r.source:
            if s not in cur.source:
                cur.source.append(s)
        # status 取优先级高
        if _PRIORITY.get(r.status, 0) > _PRIORITY.get(cur.status, 0):
            cur.status = r.status
        # reason：failed > skipped > 现有
        if r.status == "failed" and (cur.status != "failed" or not cur.reason):
            cur.reason = r.reason or cur.reason
        elif r.status == "skipped" and cur.status not in ("failed",) and not cur.reason:
            cur.reason = r.reason
        # 补空
        if not cur.mod and r.mod:
            cur.mod = r.mod
        if not cur.phase and r.phase:
            cur.phase = r.phase
        if not cur.full_name and r.full_name:
            cur.full_name = r.full_name

    return list(by_key.values()) + class_loads


def audit(log_path) -> list[dict]:
    """入口：读日志文件，返回 schema 列表。"""
    p = Path(log_path)
    if not p.exists():
        return []
    return [asdict(r) for r in parse(p.read_text(encoding="utf-8", errors="replace"))]