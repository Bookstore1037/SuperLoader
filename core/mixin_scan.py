# core/mixin_scan.py
"""路 B1：扫描 mods/ 里的 jar（含 META-INF/jars/ 嵌套 jar），解析 *.mixins.json。"""
import io
import json
import re
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class MixinDecl:
    config: str = ""
    mixin: str = ""
    full_name: str = ""
    mod: str = ""
    jar: str = ""
    nested_jar: str = ""       # 嵌套 jar 名，顶层 jar 为空
    env: str = ""              # mixins / client / server
    required: bool = True
    compatibility: str = ""
    source: list[str] = field(default_factory=lambda: ["api"])


def _read_json(zf: zipfile.ZipFile, name: str):
    try:
        with zf.open(name) as f:
            return json.load(f)
    except Exception:
        return None


def _mod_id_from_jar(zf: zipfile.ZipFile, jar_name: str) -> str:
    fmj = _read_json(zf, "fabric.mod.json")
    if fmj and "id" in fmj:
        return fmj["id"]
    try:
        with zf.open("META-INF/neoforge.mods.toml") as f:
            text = f.read().decode("utf-8", errors="replace")
        m = re.search(r'modId\s*=\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return jar_name.replace(".jar", "").split("-")[0]


def _parse_mixin_configs(zf: zipfile.ZipFile, jar_label: str, nested_jar: str,
                         mod_id: str, out: list[MixinDecl]):
    for name in zf.namelist():
        if not (name.endswith(".mixins.json") or name.endswith(".mixins.json5")):
            continue
        data = _read_json(zf, name)
        if not data or not isinstance(data, dict):
            continue
        pkg = data.get("package", "") or ""
        required = bool(data.get("required", True))
        compat = data.get("compatibilityLevel", "") or ""
        for env_key in ("mixins", "client", "server"):
            arr = data.get(env_key) or []
            if not isinstance(arr, list):
                continue
            for rel in arr:
                if not isinstance(rel, str):
                    continue
                out.append(MixinDecl(
                    config=Path(name).name,
                    mixin=rel,
                    full_name=(pkg + "." + rel) if pkg else rel,
                    mod=mod_id,
                    jar=jar_label,
                    nested_jar=nested_jar,
                    env=env_key,
                    required=required,
                    compatibility=compat,
                ))


def _scan_nested(zf: zipfile.ZipFile, jar_label: str, out: list[MixinDecl]):
    """扫嵌套 jar 里的 mixins.json。

    NeoForge 的 jar-in-jar 放在 META-INF/jarjar/，Fabric 和旧格式在 META-INF/jars/，
    两个前缀都要认，否则 JiJ 里的 mixin 会整批漏掉（Connector 自己的 32 条就在 jarjar 里）。
    """
    for name in zf.namelist():
        if not name.endswith(".jar"):
            continue
        if not name.startswith(("META-INF/jars/", "META-INF/jarjar/")):
            continue
        try:
            data = zf.read(name)
        except Exception:
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as nz:
                nested_name = Path(name).name
                nested_mod = _mod_id_from_jar(nz, nested_name)
                _parse_mixin_configs(nz, jar_label, nested_name, nested_mod, out)
        except zipfile.BadZipFile:
            continue


def scan_mods(mods_dir) -> list[MixinDecl]:
    out: list[MixinDecl] = []
    d = Path(mods_dir)
    if not d.exists():
        return out

    for jar in sorted(d.glob("*.jar")):
        try:
            with zipfile.ZipFile(jar) as zf:
                mod_id = _mod_id_from_jar(zf, jar.name)
                _parse_mixin_configs(zf, jar.name, "", mod_id, out)
                _scan_nested(zf, jar.name, out)
        except zipfile.BadZipFile:
            continue
        except Exception as e:
            print(f"[mixin-scan] {jar.name}: {e}")
    return out


def scan_to_json(mods_dir, out_path) -> int:
    decls = scan_mods(mods_dir)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps([asdict(d) for d in decls], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(decls)