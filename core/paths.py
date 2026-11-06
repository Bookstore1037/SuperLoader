# core/paths.py
import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "settings.json"

MC_VERSION = "1.21.1"
NF_VERSION = "21.1.265"
NF_ID = f"neoforge-{NF_VERSION}"


class Paths:
    def __init__(self, root: Path):
        self.root = root

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def instance(self) -> Path:
        return self.root / "instances" / MC_VERSION

    @property
    def libraries(self) -> Path:
        return self.instance / "libraries"

    @property
    def mods(self) -> Path:
        # 评测台用：每样本独立 mods 目录（instances/1.21.1/mods.compat/<slug>/），
        # 其他数据（libraries/versions/assets）仍只读共享，不复制。
        override = os.environ.get("SL_MODS_DIR")
        if override:
            p = Path(override)
            return p if p.is_absolute() else self.instance / p
        return self.instance / "mods"

    @property
    def natives(self) -> Path:
        return self.instance / "natives" / "windows" / "x64"

    @property
    def assets(self) -> Path:
        return self.instance / "assets"

    @property
    def versions(self) -> Path:
        return self.instance / "versions"

    @property
    def mc_json(self) -> Path:
        return self.versions / MC_VERSION / f"{MC_VERSION}.json"

    @property
    def nf_json(self) -> Path:
        return self.versions / NF_ID / f"{NF_ID}.json"

    @property
    def installer_original(self) -> Path:
        return self.cache / f"neoforge-{NF_VERSION}-installer.jar"

    @property
    def installer_patched(self) -> Path:
        return self.cache / f"neoforge-{NF_VERSION}-installer-patched.jar"


def load_paths() -> Paths:
    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return Paths(Path(data["root"]))