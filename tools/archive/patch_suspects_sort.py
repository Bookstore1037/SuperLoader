import pathlib

p = pathlib.Path(r"D:\SuperLoader\core\suspects.py")
t = p.read_text(encoding="utf-8")

# 1) 致命行也用 jar 路径归因
t = t.replace("        owner = _attribute(body, index)",
              "        owner = _attribute(body, index, jars)", 1)

# 2) jar 名回填：先查 prefix index，再查 jar index
old = """        jar = ""
        for info in index.values():
            if info["mod_id"] == mod_id:
                jar = info["jar"]
                break"""
new = """        jar = ""
        for info in index.values():
            if info["mod_id"] == mod_id:
                jar = info["jar"]
                break
        if not jar:
            for info in jars.values():
                if info["mod_id"] == mod_id:
                    jar = info["jar"]
                    break"""
assert old in t
t = t.replace(old, new, 1)

# 3) 排序：转换/应用失败（根因）排在连带崩溃前面
old_sort = "    items.sort(key=lambda it: (SEVERITY_ORDER.get(it[\"severity\"], 3), len(it[\"reasons\"])))"
if old_sort not in t:
    # 找现有排序
    import re
    m = re.search(r"\n    items\.sort\([^\n]*\)", t)
    print("sort line:", m.group(0) if m else None)
    sort_line = m.group(0)
    new_sort = ("\n    _ROOT = {\"mixin_transform_failed\": 0, \"mixin_failed\": 1, \"fabric_dep_missing\": 1,\n"
                "             \"mod_not_loaded\": 1, \"crash_frame\": 4, \"log_error\": 5}\n"
                "    items.sort(key=lambda it: (min(_ROOT.get(r[\"code\"], 3) for r in it[\"reasons\"]),\n"
                "                                SEVERITY_ORDER.get(it[\"severity\"], 3)))")
    t = t.replace(sort_line, new_sort, 1)

p.write_text(t, encoding="utf-8")
print("ok")
