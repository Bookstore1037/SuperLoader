# core/modrinth.py
from dataclasses import dataclass
from urllib.parse import quote

from core.downloader import Downloader


@dataclass
class ModFile:
    slug: str
    version_number: str
    filename: str
    url: str
    sha1: str | None
    size: int


class ModrinthClient:
    BASE = "https://api.modrinth.com/v2"

    def __init__(self, downloader: Downloader):
        self.downloader = downloader

    def latest(self, slug: str, mc: str, loader: str) -> ModFile:
        gv = quote(f'["{mc}"]')
        ld = quote(f'["{loader}"]')
        url = f"{self.BASE}/project/{slug}/version?game_versions={gv}&loaders={ld}"
        versions = self.downloader.get_json(url)
        if not versions:
            raise RuntimeError(f"{slug}: 没有 {mc}+{loader} 的版本")
        v = versions[0]
        for f in v["files"]:
            if f.get("primary"):
                return ModFile(
                    slug=slug,
                    version_number=v["version_number"],
                    filename=f["filename"],
                    url=f["url"],
                    sha1=f.get("hashes", {}).get("sha1"),
                    size=f["size"],
                )
        raise RuntimeError(f"{slug}: 没有 primary 文件")