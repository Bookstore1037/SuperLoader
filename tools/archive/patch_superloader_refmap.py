import pathlib

p = pathlib.Path(r'D:\SuperLoader\superloader.py')
s = p.read_text(encoding='utf-8')

old = '''    cmd = [
        "java", "-cp", str(companion[0]),
        "com.superloader.companion.repair.RefmapRepair",
        "--mods", str(paths.mods),
        "--connector", str(connector[0]),
        "--report", str(report_dir / "refmap_repair.json"),
    ]
'''
new = '''    cmd = [
        "java", "-cp", str(companion[0]),
        "com.superloader.companion.repair.RefmapRepair",
        "--mods", str(paths.mods),
        "--connector", str(connector[0]),
        "--report", str(report_dir / "refmap_repair.json"),
    ] + _refmap_locked_args(paths)
'''
assert old in s
s = s.replace(old, new, 1)

anchor = '''def _write_mixin_report(paths):'''
helper = '''def _refmap_locked_args(paths):
    """refmap 修复所需的额外参数：Yarn 映射（版本+sha1 由 lockfile 固定）、样本集、运行期 mojang 类。

    Yarn 映射只用来把注解里的 named 名翻成 intermediary；版本与 sha1 写死在
    ``compat/mappings.lock.json``，下载后校验不过就报错不加载（合成错的 refmap 比不修更糟）。
    """
    import json

    args = []
    lock = paths.root / "compat" / "mappings.lock.json"
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
        entry = (data.get("yarn") or {}).get(paths.MC_VERSION) or {}
        if entry.get("version") and entry.get("sha1"):
            args += [
                "--yarn-version", entry["version"],
                "--yarn-sha1", entry["sha1"],
                "--cache", str(paths.root / ".cache" / "compat" / "mappings"),
            ]
        else:
            print("[refmap] lockfile 里没有本版本的 yarn，跳过 named 名解析")
    except (OSError, ValueError) as exc:
        print(f"[refmap] 读 lockfile 失败，跳过 named 名解析: {exc}")

    corpus = paths.root / "compat" / "corpus.json"
    if corpus.is_file():
        args += ["--corpus", str(corpus)]

    mc_jar = _find_mc_jar(paths)
    if mc_jar is not None:
        args += ["--mc-jar", str(mc_jar)]
    return args


def _find_mc_jar(paths):
    """找运行期 mojang 类所在的 client jar（校验合成出来的 refmap 是否真的存在于运行时类里）。"""
    root = paths.instance / "libraries" / "net" / "minecraft" / "client"
    if not root.is_dir():
        return None
    candidates = []
    for jar in root.glob("*/client-*.jar"):
        name = jar.name
        if "-extra" in name or "-slim" in name or "-sources" in name:
            continue
        candidates.append(jar)
    if not candidates:
        return None
    for jar in candidates:
        if paths.MC_VERSION in jar.parent.name:
            return jar
    return sorted(candidates)[-1]


'''
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)
p.write_text(s, encoding='utf-8')
print('superloader patched')
