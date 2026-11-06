# core/downloader.py
import hashlib
import time
import urllib.request
from pathlib import Path


class Downloader:
    def __init__(self, user_agent: str = "SuperLoader/0.1", retries: int = 3, timeout: int = 60):
        self.user_agent = user_agent
        self.retries = retries
        self.timeout = timeout

    def download(self, url: str, dest: Path, sha1: str | None = None, skip_if_exists: bool = True) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)

        if skip_if_exists and dest.is_file():
            if sha1 is None or self._sha1(dest) == sha1.lower():
                return dest

        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = r.read()
                if sha1 and hashlib.sha1(data).hexdigest() != sha1.lower():
                    raise ValueError(f"SHA1 不匹配: {url}")
                dest.write_bytes(data)
                return dest
            except Exception as e:
                last_err = e
                if attempt < self.retries:
                    time.sleep(attempt)

        raise RuntimeError(f"下载失败: {url}") from last_err

    def get_json(self, url: str) -> dict:
        import json
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    @staticmethod
    def _sha1(path: Path) -> str:
        return hashlib.sha1(path.read_bytes()).hexdigest()