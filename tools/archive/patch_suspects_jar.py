import pathlib
import re

p = pathlib.Path(r"D:\SuperLoader\core\suspects.py")
t = p.read_text(encoding="utf-8")

old = '''def _attribute(line: str, index: dict[str, dict],
               jars: dict[str, dict] | None = None) -> tuple[str, str] | None:
    """把一行日志归因到模组：先看行里的 jar 路径，再取命中的最长包名前缀。"""
    if jars:
        hit = _attribute_jar(line, jars)
        if hit:
            return hit
    best: tuple[int, str, str] | None = None
'''
new = '''JAR_IN_LOG = re.compile(r"mods[\\\\/]+([A-Za-z0-9._+\\-\\[\\] \\u4e00-\\u9fff]+\\.jar)")


def jar_index(paths) -> dict[str, dict]:
    """jar 文件名（小写）→ {mod_id, jar}，用于日志里只写 jar 路径时的归因。

    典型形态：`Encountered error while transforming jar file ...\\mods\\the_bumblezone-7.17.3+1.21.1-fabric.jar`
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
    stem = re.sub(r"\\.jar$", "", name, flags=re.IGNORECASE)
    stem = re.sub(r"^\\[[^\\]]*\\]\\s*", "", stem)          # 去掉 `[钠] ` 这类中文前缀
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
'''
assert old in t
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("ok")
