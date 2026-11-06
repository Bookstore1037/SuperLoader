# core/assets.py
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from core.downloader import Downloader
from core.paths import Paths

OBJECTS_BASE = "https://resources.download.minecraft.net"


class Assets:
    def __init__(self, paths: Paths, downloader: Downloader, workers: int = 16):
        self.paths = paths
        self.downloader = downloader
        self.workers = workers

    def fill(self) -> None:
        mc = json.loads(self.paths.mc_json.read_text(encoding="utf-8"))
        ai = mc["assetIndex"]
        index_id = ai["id"]
        index_url = ai["url"]

        indexes_dir = self.paths.assets / "indexes"
        objects_dir = self.paths.assets / "objects"
        indexes_dir.mkdir(parents=True, exist_ok=True)
        objects_dir.mkdir(parents=True, exist_ok=True)

        index_file = indexes_dir / f"{index_id}.json"
        if not index_file.is_file():
            print(f"[assets] 下载 index: {index_url}")
            self.downloader.download(index_url, index_file)
        else:
            print(f"[assets] index 已存在: {index_file}")

        index = json.loads(index_file.read_text(encoding="utf-8"))
        objects = index["objects"]
        print(f"[assets] objects 总数: {len(objects)}")

        tasks = []
        for obj in objects.values():
            h = obj["hash"]
            sub = h[:2]
            dest = objects_dir / sub / h
            if dest.is_file() and dest.stat().st_size == obj["size"]:
                continue
            tasks.append((f"{OBJECTS_BASE}/{sub}/{h}", dest))

        print(f"[assets] 需要下载: {len(tasks)} 个")
        if not tasks:
            print("[assets] 完成")
            return

        done = 0
        failed = 0

        def worker(url, dest):
            dest.parent.mkdir(parents=True, exist_ok=True)
            self.downloader.download(url, dest, skip_if_exists=False)

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(worker, u, d): (u, d) for u, d in tasks}
            for f in as_completed(futures):
                u, d = futures[f]
                try:
                    f.result()
                    done += 1
                    if done % 200 == 0:
                        print(f"[assets] {done}/{len(tasks)}")
                except Exception as e:
                    failed += 1
                    print(f"[assets] 失败 {u}: {e}")

        # 兼容 assets/17.json
        legacy = self.paths.assets / f"{index_id}.json"
        if not legacy.is_file():
            legacy.write_bytes(index_file.read_bytes())

        print(f"[assets] 完成: 成功 {done}, 失败 {failed}")