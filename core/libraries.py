# core/libraries.py
import json
from pathlib import Path

from core.downloader import Downloader
from core.paths import Paths


def os_matches(rules) -> bool:
    """按 Windows x64 判断 rules。features 条件一律不满足。"""
    if not rules:
        return True
    allowed = False
    for r in rules:
        action = r.get("action")
        if "features" in r:
            continue
        cond = r.get("os", {})
        os_name = cond.get("name")
        os_arch = cond.get("arch")
        if os_name is None or os_name == "windows":
            if os_arch is None or os_arch == "x86_64":
                allowed = action == "allow"
    return allowed


class Libraries:
    def __init__(self, paths: Paths, downloader: Downloader):
        self.paths = paths
        self.downloader = downloader

    def _load_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def collect(self) -> list[str]:
        """返回去重后的 library 相对路径列表。"""
        mc = self._load_json(self.paths.mc_json)
        nf = self._load_json(self.paths.nf_json)
        seen = set()
        out = []
        for lib in mc["libraries"] + nf["libraries"]:
            if not os_matches(lib.get("rules")):
                continue
            art = lib.get("downloads", {}).get("artifact")
            if not art or not art.get("path"):
                continue
            p = art["path"]
            if p in seen:
                continue
            seen.add(p)
            out.append(p)
        return out

    def classpath(self) -> str:
        return ";".join(str(self.paths.libraries / p) for p in self.collect())

    def fill_missing(self) -> None:
        """下载所有缺失的 library。"""
        mc = self._load_json(self.paths.mc_json)
        nf = self._load_json(self.paths.nf_json)
        missing = []
        for lib in mc["libraries"] + nf["libraries"]:
            if not os_matches(lib.get("rules")):
                continue
            art = lib.get("downloads", {}).get("artifact")
            if not art or not art.get("path"):
                continue
            dest = self.paths.libraries / art["path"]
            if not dest.is_file():
                missing.append((art["url"], dest, art.get("sha1")))

        print(f"[libraries] 缺失: {len(missing)} 个")
        for url, dest, sha1 in missing:
            print(f"[libraries] 下载 {dest.name}")
            self.downloader.download(url, dest, sha1=sha1, skip_if_exists=False)
        print(f"[libraries] 完成，补了 {len(missing)} 个")