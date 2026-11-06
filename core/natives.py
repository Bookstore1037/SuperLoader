# core/natives.py
import json
import zipfile
from pathlib import Path

from core.downloader import Downloader
from core.libraries import os_matches
from core.paths import Paths


class Natives:
    def __init__(self, paths: Paths, downloader: Downloader):
        self.paths = paths
        self.downloader = downloader

    def _targets(self) -> list[dict]:
        mc = json.loads(self.paths.mc_json.read_text(encoding="utf-8"))
        out = []
        for lib in mc["libraries"]:
            name = lib.get("name", "")
            if "natives-windows" not in name:
                continue
            if "arm64" in name or "-x86" in name:
                continue
            if not os_matches(lib.get("rules")):
                continue
            art = lib.get("downloads", {}).get("artifact")
            if art:
                out.append(art)
        return out

    def fill(self) -> None:
        targets = self._targets()
        print(f"[natives] 目标: {len(targets)} 个")

        flat = self.paths.natives
        flat.mkdir(parents=True, exist_ok=True)

        for art in targets:
            dest = self.paths.libraries / art["path"]
            if not dest.is_file():
                print(f"[natives] 下载 {dest.name}")
                self.downloader.download(art["url"], dest, sha1=art.get("sha1"), skip_if_exists=False)
            with zipfile.ZipFile(dest) as z:
                for member in z.namelist():
                    if member.lower().endswith(".dll"):
                        data = z.read(member)
                        (flat / Path(member).name).write_bytes(data)

        print(f"[natives] 完成，dll 目录: {flat}")
        for p in sorted(flat.glob("*.dll")):
            print(f"  {p.name}")