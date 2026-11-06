import pathlib

p = pathlib.Path(r"D:\SuperLoader\core\suspects.py")
t = p.read_text(encoding="utf-8")

# 1) scan_console 接受 jars
t = t.replace(
    'def scan_console(log_path: Path, index: dict[str, dict]) -> dict[str, list[str]]:',
    'def scan_console(log_path: Path, index: dict[str, dict],\n                 jars: dict[str, dict] | None = None) -> dict[str, list[str]]:', 1)
t = t.replace(
    '        owner = _attribute(line, index)\n        if not owner:\n            continue',
    '        owner = _attribute(line, index, jars)\n        if not owner:\n            continue', 1)

# 2) 新增转换失败扫描，插在 scan_dep_lines 之前
anchor = 'def scan_dep_lines(log_path: Path, index: dict[str, dict]) -> dict[str, list[str]]:'
transform = '''TRANSFORM_FAIL = re.compile(
    r"Encountered error while transforming jar file|Failed to execute task "
    r"|Error transforming file ", re.IGNORECASE)


def scan_transform_errors(log_path: Path, jars: dict[str, dict]) -> dict[str, list[str]]:
    """抓 Connector 在启动前转换 jar 时的失败（L2）。

    形态：`Encountered error while transforming jar file ...\\\\mods\\\\<jar>` 后面跟
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
        for extra in lines[i:i + 10]:
            stripped = extra.strip()
            if not stripped:
                continue
            if stripped.startswith("at ") or stripped.startswith("..."):
                continue
            if not TRANSFORM_FAIL.search(stripped) and "Caused by:" not in stripped \\
                    and not stripped.startswith("java.") and "NPE" not in stripped:
                continue
            if stripped not in bucket and len(bucket) < MAX_LOG_EVIDENCE:
                bucket.append(stripped[:300])
        if not bucket:
            bucket.append(line.strip()[:300])
    return hits


'''
assert anchor in t
t = t.replace(anchor, transform + anchor, 1)

# 3) build_suspects 里建 jar 索引、接入
t = t.replace(
    '    index = package_index(paths)\n    reasons: dict[str, list[dict]] = {}',
    '    index = package_index(paths)\n    jars = jar_index(paths)\n    reasons: dict[str, list[dict]] = {}', 1)
t = t.replace(
    '    console_hits = scan_console(console_log, index)',
    '    console_hits = scan_console(console_log, index, jars)\n'
    '    transform_hits = scan_transform_errors(console_log, jars)', 1)
t = t.replace(
    '    # 7.5 崩溃栈里的模组帧',
    '    # 7.2 Connector 转换 jar 失败（L2，早于任何模组代码）\n'
    '    for mod_id, evidence in transform_hits.items():\n'
    '        add(mod_id, "mixin_transform_failed", evidence[0], "high", layer="L2")\n\n'
    '    # 7.5 崩溃栈里的模组帧', 1)
t = t.replace(
    '        evidence = list(console_hits.get(mod_id) or [])',
    '        evidence = list(transform_hits.get(mod_id) or [])\n'
    '        evidence += [e for e in (console_hits.get(mod_id) or []) if e not in evidence]', 1)
t = t.replace(
    '            "crash_frames": sum(len(v) for v in frame_hits.values()),',
    '            "crash_frames": sum(len(v) for v in frame_hits.values()),\n'
    '            "transform_errors": sum(len(v) for v in transform_hits.values()),', 1)

p.write_text(t, encoding="utf-8")
print("ok")
