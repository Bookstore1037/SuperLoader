import pathlib
import re

p = pathlib.Path(r"D:\SuperLoader\core\suspects.py")
t = p.read_text(encoding="utf-8")

# 1) 转换失败扫描：窗口放宽到 40 行，只收 Caused by / 失败行，最多 6 条
old_loop_start = t.index("    lines = _read_log_lines(log_path)\n    for i, line in enumerate(lines):\n        if not TRANSFORM_FAIL.search(line):")
old_end = t.index("    return hits\n\n\ndef scan_dep_lines")
new_body = '''    lines = _read_log_lines(log_path)
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
'''
t = t[:old_loop_start] + new_body + t[old_end:]

# 2) 证据挑更靠根因的行
t = t.replace('_EVIDENCE_PRIORITY = ("Caused by:", "Failed to execute task", "Encountered error",\n                      "Error transforming", "Exception", "Error")',
              '_EVIDENCE_PRIORITY = ("NullPointerException", "Failed to execute task", "Caused by:",\n                      "Encountered error", "Error transforming", "Exception", "Error")', 1)

# 3) 有转换失败时不再重复加 log_error
t = t.replace('    for mod_id, evidence in console_hits.items():',
              '    for mod_id, evidence in console_hits.items():\n'
              '        if mod_id in transform_hits:\n'
              '            continue  # 同一条错误已由 mixin_transform_failed 收录', 1)

p.write_text(t, encoding="utf-8")
print("ok")
