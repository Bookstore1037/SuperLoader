import pathlib

p = pathlib.Path(r'D:\SuperLoader\core\suspects.py')
t = p.read_text('utf-8')

old = """    def frames_from(seq: list[str]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for line in seq:
            if FATAL_MARK.search(line):
                continue
            stripped = line.strip()
            if not stripped.startswith("at "):
                continue
            m = FML_FRAME.match(stripped)
            mid = by_norm.get(m.group(1).replace("-", "_").lower()) if m else None
            if not mid:
                owner = _attribute(stripped, index)
                mid = owner[0] if owner else None
            if not mid:
                continue
            bucket = out.setdefault(mid, [])
            if len(bucket) < MAX_LOG_EVIDENCE and stripped not in bucket:
                bucket.append(stripped[:300])
        return out"""

new = """    def frames_from(seq: list[str]) -> dict[str, list[str]]:
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
            active = ("Exception" in stripped or "Error" in stripped or "Caused by" in stripped) \\
                and level in (None, "ERROR", "FATAL")
        return out"""

assert old in t, 'frames_from not found'
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('frames_from rewritten with active-stack rule')
