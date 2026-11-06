import pathlib

p = pathlib.Path(r'D:\SuperLoader\core\report.py')
s = p.read_text(encoding='utf-8')

old = '''    repair = env.get("refmap_repair") or {}
    if repair:
        add(f"  refmap 修复: 缺失 {repair.get('missing_refmaps', 0)}   修补 jar {repair.get('patched', 0)}   "
            f"条目 {repair.get('entries', 0)}   未解析 {repair.get('unresolved', 0)}")
'''
new = '''    repair = env.get("refmap_repair") or {}
    if repair:
        origins = repair.get("origins") or {}
        add(f"  refmap 修复: 缺失 {repair.get('missing_refmaps', 0)}   修补 jar {repair.get('patched', 0)}   "
            f"条目 {repair.get('entries', 0)}   校验通过 {repair.get('verified', 0)}   "
            f"未解析 {repair.get('unresolved', 0)}   yarn={repair.get('yarn', '-')}")
        add(f"    来源: 玩家基线 {origins.get('player_baseline', 0)}   评测台样本 {origins.get('compat_sample', 0)}")
        if repair.get("unresolved"):
            add("    ⚠ 有未解析条目：可能是缺 Yarn 映射或映射表里查不到，详见 refmap_repair.json")
'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('report patched')
