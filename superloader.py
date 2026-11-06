# superloader.py
import argparse
import sys
from datetime import datetime

from core.paths import load_paths
from core.downloader import Downloader
from core.libraries import Libraries
from core.installer import Installer
from core.natives import Natives
from core.assets import Assets
from core.modrinth import ModrinthClient
from core.launcher import Launcher
from core.paths import MC_VERSION
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent

MOD_SLUGS = ["connector", "forgified-fabric-api"]


def _find_runtime_jars(mods_dir, slug):
    """按文件名前缀找 slug 对应的 jar。connector -> connector-*.jar"""
    if not mods_dir.exists():
        return []
    prefix = f"{slug}-"
    return sorted(
        p for p in mods_dir.iterdir()
        if p.is_file() and p.name.startswith(prefix) and p.suffix == ".jar"
    )


def ensure_runtime_mods(paths, dl, mr, dry_run=False):
    for slug in MOD_SLUGS:
        local = _find_runtime_jars(paths.mods, slug)
        if len(local) > 1:
            print(f"[mods] 冲突: {slug} 有 {len(local)} 个 jar，请手动保留一个：")
            for p in local:
                print(f"  - {p.name}")
            return 1
        if len(local) == 1:
            print(f"[mods] {slug} 存在 ({local[0].name})")
            continue
        if dry_run:
            print(f"[mods] {slug} 缺失 (dry-run，不下载)")
            continue
        try:
            f = mr.latest(slug, MC_VERSION, "neoforge")
            dest = paths.mods / f.filename
            print(f"[mods] {slug} 缺失，补下 {f.version_number} -> {f.filename}")
            paths.mods.mkdir(parents=True, exist_ok=True)   # 只在这里 mkdir
            dl.download(f.url, dest, sha1=f.sha1)
        except Exception as e:
            print(f"[mods] {slug} 补下失败: {e}")
            return 1
    return 0


def cmd_install(args):
    paths = load_paths()
    dl = Downloader()

    print("=== 1/5 安装 NeoForge ===")
    Installer(paths, dl).install()

    print("\n=== 2/5 补 libraries ===")
    Libraries(paths, dl).fill_missing()

    print("\n=== 3/5 补 natives ===")
    Natives(paths, dl).fill()

    print("\n=== 4/5 补 assets ===")
    Assets(paths, dl).fill()

    print("\n=== 5/5 下载 Connector + FFAPI ===")
    if ensure_runtime_mods(paths, dl, ModrinthClient(dl)) != 0:
        return 1

    print("\n=== 安装完成 ===")


def cmd_launch(args):
    paths = load_paths()
    dl = Downloader()

    mr = ModrinthClient(dl)
    if ensure_runtime_mods(paths, dl, mr, dry_run=args.dry_run) != 0:
        return 1

    lib = Libraries(paths, dl)
    launcher = Launcher(paths, lib.classpath(), memory_mb=args.mem)

    if args.dry_run:
        for c in launcher.build():
            print(c if len(c) < 200 else c[:200] + " ...")
        return 0

    _refmap_repair(paths)

    started_at = datetime.now().astimezone().isoformat(timespec="seconds")

    rc = launcher.launch()
    finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[launch] 退出码 {rc}")
    _write_mixin_report(paths)
    _write_reports(paths, launch={
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": rc,
        "dry_run": False,
    })
    return rc


def _refmap_repair(paths):
    """启动前修补"mixin config 声明了 refmap、但 jar 内没有该文件"的模组。

    Connector 对缺失的 refmap 只打 WARN（`Refmap remapper could not find refmap file`），
    这些 mixin 随后按 dev 名找不到目标（日志 `No refMap loaded`）。修复必须在 Mixin
    初始化之前完成，所以放在启动前，由 companion 自带的小工具直接改写 jar。

    设置 ``SL_NO_REFMAP_REPAIR=1`` 可关闭。
    """
    import os
    import subprocess

    if os.environ.get("SL_NO_REFMAP_REPAIR"):
        print("[refmap] SL_NO_REFMAP_REPAIR 已设置，跳过修复")
        return

    companion = _find_runtime_jars(paths.mods, "superloader_companion")
    connector = _find_runtime_jars(paths.mods, "connector")
    if len(companion) != 1 or len(connector) != 1:
        print("[refmap] 找不到唯一的 companion / connector jar，跳过修复")
        return

    report_dir = paths.instance / "logs" / "superloader-report"
    report_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "java", "-cp", str(companion[0]),
        "com.superloader.companion.repair.RefmapRepair",
        "--mods", str(paths.mods),
        "--connector", str(connector[0]),
        "--report", str(report_dir / "refmap_repair.json"),
    ] + _refmap_locked_args(paths)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        print("[refmap] 找不到 java，跳过修复")
        return
    except subprocess.TimeoutExpired:
        print("[refmap] 修复超时（180s），跳过")
        return
    for line in (proc.stdout or "").splitlines():
        if line.startswith("[refmap-repair]"):
            print("[refmap]" + line[len("[refmap-repair]"):])
    if proc.returncode != 0:
        print(f"[refmap] 修复工具退出码 {proc.returncode}: {(proc.stderr or '').strip()[:400]}")


def _refmap_locked_args(paths):
    """refmap 修复所需的额外参数：Yarn 映射（版本+sha1 由 lockfile 固定）、样本集、运行期 mojang 类。

    Yarn 映射只用来把注解里的 named 名翻成 intermediary；版本与 sha1 写死在
    ``compat/mappings.lock.json``，下载后校验不过就报错不加载（合成错的 refmap 比不修更糟）。
    """
    import json

    args = []
    lock = CODE_ROOT / "compat" / "mappings.lock.json"
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
        entry = (data.get("yarn") or {}).get(MC_VERSION) or {}
        if entry.get("version") and entry.get("sha1"):
            args += [
                "--yarn-version", entry["version"],
                "--yarn-sha1", entry["sha1"],
                "--cache", str(CODE_ROOT / ".cache" / "compat" / "mappings"),
            ]
        else:
            print("[refmap] lockfile 里没有本版本的 yarn，跳过 named 名解析")
    except (OSError, ValueError) as exc:
        print(f"[refmap] 读 lockfile 失败，跳过 named 名解析: {exc}")

    corpus = CODE_ROOT / "compat" / "corpus.json"
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
        if MC_VERSION in jar.parent.name:
            return jar
    return sorted(candidates)[-1]


def _write_mixin_report(paths):
    """launch 后生成透明化报告：
       mixins_declared.json — 路 B1 jar 声明
       mixins_logged.json   — 路 C 日志结果
       mixins.json          — 合并（最终）
    """
    import json
    from core.mixin_scan import scan_to_json
    from core.mixin_audit import audit
    from core.mixin_merge import merge_to_json

    report_dir = paths.instance / "logs" / "superloader-report"
    report_dir.mkdir(parents=True, exist_ok=True)

    # 路 B1
    declared_path = report_dir / "mixins_declared.json"
    try:
        n = scan_to_json(paths.instance / "mods", declared_path)
        print(f"[report] mixins_declared.json: {n} 条声明")
    except Exception as e:
        print(f"[report] mixin 声明扫描失败: {e}")

    # 路 C
    logged_path = report_dir / "mixins_logged.json"
    log_path = paths.instance / "logs" / "superloader-launch.log"
    if log_path.exists():
        records = audit(log_path)
        logged_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[report] mixins_logged.json: {len(records)} 条日志结果")
    else:
        logged_path.write_text("[]", encoding="utf-8")
        print("[report] 未找到 launch 日志，日志结果为空")

    # 合并
    stats = merge_to_json(declared_path, logged_path, report_dir / "mixins.json")
    print(f"[report] mixins.json: total={stats['total']} " +
          " ".join(f"{k}={v}" for k, v in stats.items() if k != "total"))
    print(f"[report] 输出: {report_dir}")

def _write_reports(paths, launch=None):
    """environment.json / mods.json / events_report.json / apis.json /
    classloading.json / summary.txt（数据来自 companion 的 runtime.json + jar 元数据）。"""
    from core.report import write_reports
    try:
        stats = write_reports(paths, launch=launch)
        print(f"[report] environment / mods / events_report / apis / classloading / summary: "
              f"mods={stats['mods']} issues={stats['issues']} "
              f"mixins={stats['mixins']} events={stats.get('events', 0)} "
              f"apis_issues={stats.get('apis', 0)} "
              f"cls_issues={stats.get('classloading', 0)} "
              f"suspects={stats.get('suspects', 0)} "
              f"stale={stats.get('stale')}")
    except Exception:
        import traceback
        traceback.print_exc()
        print("[report] transparency report generation failed")


def cmd_report(args):
    paths = load_paths()
    _write_mixin_report(paths)
    _write_reports(paths)
    return 0


def main():
    parser = argparse.ArgumentParser(prog="superloader")
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="安装 NeoForge + Connector + FFAPI")
    p_install.set_defaults(func=cmd_install)

    p_launch = sub.add_parser("launch", help="启动游戏")
    p_launch.add_argument("--mem", type=int, default=4096)
    p_launch.add_argument("--dry-run", action="store_true")
    p_launch.set_defaults(func=cmd_launch)

    p_report = sub.add_parser("report", help="只重新生成透明化报告（不启动游戏）")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()