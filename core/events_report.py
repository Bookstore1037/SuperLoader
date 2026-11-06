# core/events_report.py
"""events 报告层：把 companion 写的原始 events.json 渲染成结构化视图。

沿用项目的单一写入者原则：
  companion（Java）只落原始事实（events.json，schema 1 = v1，schema 2 = v2）
  Python 只读原始事实，产出 events_report.json + summary.txt 的「事件」段

events.json 的三个阶段（load_complete / periodic / shutdown）互相覆盖、没有历史，
所以这里只描述"最后一次快照"，不伪造时间序列。

v2 契约（companion 0.4.1 起实现，读到就用、读不到就降级）：
  - events[] 每条可带 timing: {count, total_ns, max_ns}
  - spy 覆盖 GAME bus 全量事件类（load_complete + 每次 periodic 扫 listenerLists keys），
    "registered>0 但 declared_by 为空" 的程序化 addListener 条目会从 ~31 个降到 0
  - 耗时口径：每个事件类在 HIGHEST / LOWEST 各挂一个探针，两者间隔 ≈ 其他监听器的
    处理耗时（同优先级监听器与探针的相对顺序不退让，是近似值，不是 post 总墙钟时间）

状态分类（全部由数据推导，不写死数字）：
  observed         spied 且 posts > 0
  never_triggered  spied 但 posts == 0（observed_since 之后没触发）
  programmatic     未 spied、GAME bus 上有注册、但没有 @SubscribeEvent 声明
                   → v1 的唯一覆盖缺口，v2 的目标
  non_game_bus     未 spied、GAME bus 反射表里查不到注册、但有 @SubscribeEvent 声明
                   → 注册在 MOD bus / 被 classChecker 拒绝，属于设计边界
"""
import textwrap
from collections import Counter, defaultdict
from datetime import datetime

EVENT_REPORT_SCHEMA = 1


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _short(name: str) -> str:
    return name.rsplit(".", 1)[-1] if name else ""


def _wrap(text: str, width: int = 110, indent: str = "  ") -> str:
    return "\n".join(textwrap.wrap(
        text, width=width, initial_indent=indent, subsequent_indent=indent + "  ",
        break_long_words=False, break_on_hyphens=False))


def _status(item: dict) -> str:
    declared = item.get("declared_by") or []
    registered = item.get("registered")
    spied = bool(item.get("spied"))
    if spied:
        return "observed" if (item.get("posts") or 0) > 0 else "never_triggered"
    if isinstance(registered, int) and registered > 0:
        # GAME bus 上有监听器，但扫描不到 @SubscribeEvent 声明 → 程序化 addListener
        return "programmatic"
    if registered is None and declared:
        # @SubscribeEvent 声明存在，但 GAME bus 上没有注册 → MOD bus / classChecker
        return "non_game_bus"
    return "unspied"


def _timing(item: dict) -> dict | None:
    raw = item.get("timing")
    if not isinstance(raw, dict):
        return None
    try:
        count = int(raw.get("count") or 0)
        total_ns = int(raw.get("total_ns") or 0)
        max_ns = int(raw.get("max_ns") or 0)
    except (TypeError, ValueError):
        return None
    if count <= 0:
        return None
    return {
        "count": count,
        "total_ns": total_ns,
        "max_ns": max_ns,
        "total_ms": round(total_ns / 1e6, 2),
        "avg_us": round(total_ns / count / 1e3, 1),
        "max_us": round(max_ns / 1e3, 1),
    }


def _owner(declared: str) -> str:
    """declared_by 格式：modid:全限定类#方法。"""
    return declared.split(":", 1)[0] if ":" in declared else declared


def build_events(raw: dict | None) -> dict:
    """把 events.json 的原始内容渲染成报告结构。raw 缺失时返回空报告，不抛异常。"""
    out = {
        "schema": EVENT_REPORT_SCHEMA,
        "generated_at": _now(),
        "source": None,
        "raw": {},
        "timing": False,
        "totals": {
            "event_classes": 0, "spied": 0, "observed": 0, "never_triggered": 0,
            "programmatic": 0, "non_game_bus": 0, "unspied": 0,
            "reachable": 0, "coverage": None,
        },
        "by_mod": [],
        "top_posts": [],
        "top_cost": [],
        "gaps": {"programmatic": [], "non_game_bus": []},
        "events": [],
        "notes": [],
    }
    if not isinstance(raw, dict):
        out["notes"].append("events.json 缺失或不可解析")
        return out

    items = raw.get("events")
    if not isinstance(items, list):
        out["notes"].append("events.json 缺少 events 列表")
        out["source"] = "events.json"
        return out

    out["source"] = "events.json"
    out["raw"] = {
        key: raw.get(key)
        for key in ("schema", "stage", "generated_at", "observed_since",
                    "method", "registration_view")
    }

    counts: Counter = Counter()
    events: list[dict] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("event"):
            continue
        name = item["event"]
        status = _status(item)
        counts[status] += 1
        entry = dict(item)
        entry["simple"] = _short(name)
        entry["status"] = status
        entry["timing"] = _timing(item)
        events.append(entry)

    spied = counts["observed"] + counts["never_triggered"]
    reachable = spied + counts["programmatic"]
    out["totals"] = {
        "event_classes": len(events),
        "spied": spied,
        "observed": counts["observed"],
        "never_triggered": counts["never_triggered"],
        "programmatic": counts["programmatic"],
        "non_game_bus": counts["non_game_bus"],
        "unspied": counts["unspied"],
        "reachable": reachable,
        "coverage": round(spied / reachable, 3) if reachable else None,
    }

    declarations: Counter = Counter()
    owned_events: dict[str, set] = defaultdict(set)
    for entry in events:
        for declared in entry.get("declared_by") or []:
            owner = _owner(declared)
            declarations[owner] += 1
            owned_events[owner].add(entry["event"])
    out["by_mod"] = [
        {"mod_id": mod_id, "declarations": declarations[mod_id],
         "events": len(owned_events[mod_id])}
        for mod_id in sorted(declarations, key=lambda k: (-declarations[k], k))
    ]

    posted = sorted(
        (e for e in events if isinstance(e.get("posts"), int) and e["posts"] > 0),
        key=lambda e: -e["posts"])
    out["top_posts"] = [
        {"event": e["event"], "simple": e["simple"], "posts": e["posts"]}
        for e in posted[:5]
    ]

    timed = [e for e in events if e["timing"]]
    out["timing"] = bool(timed)
    out["top_cost"] = [
        {"event": e["event"], "simple": e["simple"], "count": e["timing"]["count"],
         "total_ms": e["timing"]["total_ms"], "avg_us": e["timing"]["avg_us"],
         "max_us": e["timing"]["max_us"]}
        for e in sorted(timed, key=lambda e: -e["timing"]["total_ns"])[:5]
    ]

    out["gaps"] = {
        "programmatic": [e["event"] for e in events if e["status"] == "programmatic"],
        "non_game_bus": [e["event"] for e in events if e["status"] == "non_game_bus"],
    }

    if not out["timing"]:
        schema = (out["raw"] or {}).get("schema")
        out["notes"].append(
            "本次快照没有 timing 样本（事件触发后才会出现）"
            if isinstance(schema, int) and schema >= 2
            else "events schema 1：未采集事件耗时（需 companion ≥ 0.4.1）")
    if counts["programmatic"]:
        out["notes"].append(
            f"{counts['programmatic']} 个事件类在 GAME bus 有注册但没有 @SubscribeEvent 声明"
            "（程序化 addListener），当前快照未挂 spy")
    out["events"] = events
    return out


def compact(ev: dict) -> dict:
    """environment.json 里只需要摘要，完整逐事件数据留在 events_report.json。"""
    raw = ev.get("raw") or {}
    return {
        "totals": ev.get("totals"),
        "stage": raw.get("stage"),
        "generated_at": raw.get("generated_at"),
        "observed_since": raw.get("observed_since"),
        "registration_view": raw.get("registration_view"),
        "timing": ev.get("timing"),
        "by_mod": ev.get("by_mod"),
        "top_posts": ev.get("top_posts"),
        "top_cost": ev.get("top_cost"),
        "gaps": {k: len(v or []) for k, v in (ev.get("gaps") or {}).items()},
    }


def summary_lines(ev: dict, limit: int = 6) -> list[str]:
    """summary.txt 的「事件」段正文（不含标题）。"""
    if not ev.get("source"):
        return ["  events.json 未生成（companion 未运行或版本过旧）"]

    totals = ev.get("totals") or {}
    raw = ev.get("raw") or {}
    coverage = totals.get("coverage")
    coverage_text = f"{coverage:.0%}" if isinstance(coverage, float) else "?"

    lines = [
        f"  事件类 {totals.get('event_classes', 0)}   已观测 {totals.get('observed', 0)}   "
        f"挂 spy 未触发 {totals.get('never_triggered', 0)}   "
        f"覆盖率 {totals.get('spied', 0)}/{totals.get('reachable', 0)} ({coverage_text})",
        f"  阶段 {raw.get('stage') or '?'} @ {raw.get('generated_at') or '?'}   "
        f"注册表视图 {raw.get('registration_view') or '?'}   "
        f"耗时采集 {'有' if ev.get('timing') else '无'}",
    ]

    gaps = ev.get("gaps") or {}
    programmatic = gaps.get("programmatic") or []
    if programmatic:
        lines.append(_wrap(
            f"待覆盖（程序化 addListener，{len(programmatic)}）: "
            + _join_short(programmatic, limit), indent="  "))
    non_game_bus = gaps.get("non_game_bus") or []
    if non_game_bus:
        lines.append(_wrap(
            f"非 GAME bus（{len(non_game_bus)}）: " + _join_short(non_game_bus, limit),
            indent="  "))

    top_posts = ev.get("top_posts") or []
    never = [e for e in ev.get("events") or [] if e.get("status") == "never_triggered"]
    if never:
        lines.append(_wrap(
            f"从未触发（{len(never)}）: " + _join_short([e["event"] for e in never], limit),
            indent="  "))
    if top_posts:
        lines.append(_wrap(
            "触发最多: " + ", ".join(f"{e['simple']}={e['posts']}" for e in top_posts),
            indent="  "))

    by_mod = ev.get("by_mod") or []
    if by_mod:
        lines.append(_wrap(
            "声明来源: " + ", ".join(
                f"{m['mod_id']}={m['declarations']}" for m in by_mod[:6]),
            indent="  "))

    top_cost = ev.get("top_cost") or []
    if top_cost:
        lines.append(_wrap(
            "耗时最高: " + ", ".join(
                f"{e['simple']} {e['total_ms']}ms/{e['count']}次" for e in top_cost[:3]),
            indent="  "))
    else:
        lines.append("  耗时: 本次快照无样本（事件触发后才有）")

    lines.append("  口径: 仅 GAME bus；覆盖率分母 = 总数 - 非 GAME bus；"
                 "observed_since 之前触发的事件计为 0")
    return lines


def _join_short(names: list[str], limit: int) -> str:
    short = [_short(n) for n in names]
    if len(short) > limit:
        return ", ".join(short[:limit]) + f" … 另 {len(short) - limit} 个"
    return ", ".join(short)
