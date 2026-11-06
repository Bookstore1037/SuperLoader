"""清理 logs/：只保留最近 N 次评测台运行，其余打包进 logs/archive/。

用法：
    python tools/clean_logs.py            # 保留最近 3 次，其余打包后删除
    python tools/clean_logs.py --keep 0   # 只打包，不保留
    python tools/clean_logs.py --dry-run  # 只看会动哪些

规则：
  - 只动 logs/compat/ 下名字是 8 位日期（20261104-124552）的运行目录；
  - 按名字倒序保留最近 --keep 个，其余压缩成一个 zip 放进 logs/archive/；
  - 压缩成功后原目录才删除；zip 已存在则追加不了，换一个带序号的名字；
  - 其它目录（baseline-*、removed-mods、tmp-mods-backup、dep-test）一律不碰。
"""

from __future__ import annotations

import argparse
import re
import shutil
import time
import zipfile
from pathlib import Path

RUN_DIR = re.compile(r"^\d{8}-\d{6}$")


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human(n: int) -> str:
    return f"{n / 1048576:.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="logs", help="logs 目录（默认 ./logs）")
    ap.add_argument("--keep", type=int, default=3, help="保留最近几个运行目录")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    logs = Path(args.logs)
    compat = logs / "compat"
    if not compat.is_dir():
        print(f"[clean] 没有 {compat}，跳过")
        return 0

    runs = sorted((d for d in compat.iterdir() if d.is_dir() and RUN_DIR.match(d.name)),
                  key=lambda d: d.name, reverse=True)
    if args.keep < 0:
        args.keep = 0
    doomed = runs[args.keep:]
    before = dir_size(logs)

    print(f"[clean] 运行目录 {len(runs)} 个，保留 {min(args.keep, len(runs))} 个，待归档 {len(doomed)} 个")
    for d in doomed:
        print(f"  - {d.name}  {human(dir_size(d))}")
    if not doomed:
        print(f"[clean] 无需清理，logs 共 {human(before)}")
        return 0
    if args.dry_run:
        print("[clean] dry-run，未改动")
        return 0

    archive = logs / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    zip_path = archive / f"compat-pruned-{stamp}.zip"
    n = 1
    while zip_path.exists():
        zip_path = archive / f"compat-pruned-{stamp}-{n}.zip"
        n += 1

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in doomed:
            for f in sorted(d.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(logs))
    print(f"[clean] 已打包 {zip_path}（{human(zip_path.stat().st_size)}）")

    for d in doomed:
        shutil.rmtree(d, ignore_errors=True)

    after = dir_size(logs)
    print(f"[clean] logs: {human(before)} -> {human(after)}，释放 {human(before - after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
