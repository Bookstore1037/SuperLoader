"""兼容评测台：单样本隔离跑，判定 pass/fail 并落 compat.json + compat.md。

用法：
  python tools/compat_sweep.py --plan --group auto      # 只打印拼装计划（不复制、不启动）
  python tools/compat_sweep.py --prepare --group auto   # 只拼 mods 目录 + 校验 sha1（不启动）
  python tools/compat_sweep.py --group auto             # 拼装 + 启动 + 判定
  python tools/compat_sweep.py --sample krypton         # 只跑一个

判定（与 compat/corpus_v2.md §0 一致）：
  pass = 样本 jar 真的进了 ModList（loaded）+ 进存档 + 无 FATAL + 新 runtime.json + 无 crash report
  样本 jar 在 mods/ 里但没进 ModList → fail(sample_not_loaded)
  超时无新 runtime.json → fail(timeout_no_runtime)
  进程存活但出现新 crash report → fail(crash_screen)
  sha1 不符 / jar 缺失 → fail(infra_not_ready)，不算样本失败

隔离（写死）：每样本独立 mods 目录 instances/1.21.1/mods.compat/<slug>/；
运行时把实例 mods/ 暂存为 mods.__baseline、复制样本目录过去（FML 只认 gameDir/mods，
SL_MODS_DIR 只影响 Python 侧报告扫描），跑完立即换回。异常中断用 --restore-mods 收尾。
libraries/versions/assets 只读共享。
存档：运行前从 logs/compat/save-backup/新的世界 恢复，避免样本间污染。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTANCE = ROOT.parent / "SLData" / "instances" / "1.21.1"
JAR_CACHE = ROOT / ".cache" / "compat" / "jars"
CORPUS = ROOT / "compat" / "corpus.json"
CLOSURE = ROOT / "compat" / "deps_closure.json"
OUT_ROOT = ROOT / "logs" / "compat"
SAVE_SRC = INSTANCE / "saves" / "新的世界"
SAVE_BACKUP = OUT_ROOT / "save-backup" / "新的世界"

# “进存档”证据：companion 的 world_joined 事件还没加（P1 待办），现在用客户端日志。
# 强证据（足以判定进入世界）：
#   A. LoggerChunkProgressListener 的 "Time elapsed: <n> ms" —— 出生点区块加载完成，一次性打印；
#   B. "Saving chunks for level" —— 世界真的被保存过（退出/自动保存），只可能在进入后出现；
#   C. "Started serving on" —— 开 LAN 时才有，弱。
# 弱证据（单独不成立，只作辅助记录）：AdvancementTree "Loaded <n> advancements"、
#   "Preparing spawn area"（服务端准备出生点，也可能在失败前打印）。
STRONG_JOIN = [
    re.compile(r"Time elapsed: \d+ ms"),
    re.compile(r"Saving chunks for level"),
]
WEAK_JOIN = [
    re.compile(r"Preparing spawn area"),
    re.compile(r"Loaded \d+ advancements"),
]
CRASH_SCREEN_PATTERNS = [re.compile(r"Cowardly refusing"), re.compile(r"crash screen", re.I)]


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text("utf-8"))


def sample_group(corpus, name):
    groups = {
        "main": corpus["main"],
        "auto": [r for r in corpus["main"] if r.get("verdict_mode") == "auto"],
        "manual": [r for r in corpus["main"] if r.get("verdict_mode") == "manual"],
        "negative": corpus.get("negative") or [],
        "infra": corpus["infra"],
        "content": corpus["content_phase2"],
    }
    if name not in groups:
        raise SystemExit("未知 group: %s（可选 %s）" % (name, ", ".join(groups)))
    return groups[name]


def runtime_mods(mods_dir: Path):
    """运行时模组：connector / FFAPI / companion，取现实例 mods/ 里的三个 jar。"""
    live = INSTANCE / "mods"
    picks = []
    for pat in ("connector-*-full.jar", "forgified-fabric-api-*.jar", "superloader_companion-*.jar"):
        found = sorted(live.glob(pat))
        if not found:
            raise SystemExit("实例 mods/ 里缺运行时模组 %s" % pat)
        picks.append(found[-1])
    return picks


def plan(sample, closure, mods_dir: Path):
    rec = closure[sample]
    jars = []
    for it in rec.get("install") or []:
        p = JAR_CACHE / it["file"]
        ok = p.exists() and sha1_of(p) == it.get("sha1")
        jars.append({"file": it["file"], "ok": ok, "entry": it})
    rt = runtime_mods(mods_dir)
    return {"sample": sample, "mods_dir": str(mods_dir), "jars": jars, "runtime": [p.name for p in rt]}


def prepare(sample, closure, mods_dir: Path):
    info = plan(sample, closure, mods_dir)
    bad = [j["file"] for j in info["jars"] if not j["ok"]]
    if bad:
        return info, "infra_not_ready: sha1 不符或 jar 缺失 -> %s" % ", ".join(bad)
    if mods_dir.exists():
        shutil.rmtree(mods_dir)
    mods_dir.mkdir(parents=True, exist_ok=True)
    for j in info["jars"]:
        shutil.copy2(JAR_CACHE / j["file"], mods_dir / j["file"])
    for p in runtime_mods(mods_dir):
        shutil.copy2(p, mods_dir / p.name)
    info["installed"] = sorted(p.name for p in mods_dir.glob("*.jar"))
    return info, None


def restore_save():
    if not SAVE_BACKUP.exists():
        if not SAVE_SRC.exists():
            raise SystemExit("既没有存档备份也没有现存档：%s" % SAVE_SRC)
        SAVE_BACKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SAVE_SRC, SAVE_BACKUP)
        print("[save] 已备份 %s" % SAVE_BACKUP)
        return
    if SAVE_SRC.exists():
        shutil.rmtree(SAVE_SRC)
    shutil.copytree(SAVE_BACKUP, SAVE_SRC)


MODS_LIVE = INSTANCE / "mods"
MODS_STASH = INSTANCE / "mods.__baseline"


def stage_mods(staged: Path):
    """把实例 mods/ 换成样本目录 —— FML 只扫 gameDir/mods，SL_MODS_DIR 只影响 Python 侧。"""
    if MODS_STASH.exists():
        raise SystemExit("发现残留 %s，先运行 --restore-mods" % MODS_STASH)
    if not staged.is_dir():
        raise SystemExit("样本 mods 目录不存在：%s" % staged)
    if MODS_LIVE.exists():
        MODS_LIVE.rename(MODS_STASH)
    shutil.copytree(staged, MODS_LIVE)


def restore_mods():
    if MODS_LIVE.exists():
        shutil.rmtree(MODS_LIVE)
    if MODS_STASH.exists():
        MODS_STASH.rename(MODS_LIVE)


def own_jar(closure, sample):
    rec = closure.get(sample) or {}
    if rec.get("file"):
        return rec["file"]
    for it in rec.get("install") or []:
        if it.get("slug") == sample or it.get("id") == rec.get("mod_id"):
            return it.get("file")
    return None


def sample_loaded_from_report(closure, sample):
    """样本自己的 jar 是否真的进了本次 ModList（loaded 非空）。

    Connector 会把 jar 重命名成 <原名>_mapped_moj_1.21.1.jar，且 mod_id 常与 slug 不同
    （stackdeobf → stackdeobfuscator），所以按「原名 / 去掉 _mapped 前缀 / jar 内 mod id」三路匹配。
    """
    own = own_jar(closure, sample)
    if not own:
        return None, own
    stem = Path(own).stem
    ids = {sample}
    try:
        import zipfile
        with zipfile.ZipFile(JAR_CACHE / own) as z:
            fmj = json.loads(z.read("fabric.mod.json").decode("utf-8", "replace"), strict=False)
        ids.add(fmj.get("id"))
        for p in fmj.get("provides") or []:
            ids.add(str(p).split(":")[0])
    except Exception:
        pass
    ids = {i for i in ids if i}
    try:
        mods = json.loads((REPORT_SRC / "mods.json").read_text("utf-8"))
    except Exception:
        return None, own
    for m in mods.get("mods") or []:
        jar = (m.get("jar") or "")
        if (jar == own or jar.startswith(stem)
                or m.get("mod_id") in ids):
            return bool(m.get("loaded")), own
    return False, own


FML_CFG = INSTANCE / "config" / "fml.toml"
FML_GOOD = OUT_ROOT / "fml.toml.good"


def guard_fml_config():
    """被杀在启动早期会留下写了一半的 fml.toml → SetupMinecraftWindow NPE。跑前还原已知good。"""
    if FML_GOOD.exists():
        FML_CFG.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FML_GOOD, FML_CFG)
    elif FML_CFG.exists():
        FML_GOOD.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FML_CFG, FML_GOOD)


def scan_log(text: str):
    fatal = [ln.strip()[:400] for ln in text.splitlines()
             if any(k in ln for k in ("Mixin apply for mod", "MixinTransformerError", "FAILED during APPLY",
                                     "Exception in thread \"main\"", "---- Minecraft Crash Report ----",
                                     "A fatal error has been detected", "Could not execute entrypoint",
                                     "Error during pre-loading phase", "Some of your mods are incompatible"))]
    strong, weak = [], []
    for ln in text.splitlines():
        s = ln.strip()[:300]
        if any(p.search(ln) for p in STRONG_JOIN):
            strong.append(s)
        elif any(p.search(ln) for p in WEAK_JOIN):
            weak.append(s)
    crash_screen = any(p.search(ln) for ln in text.splitlines() for p in CRASH_SCREEN_PATTERNS)
    return fatal[:10], strong[:5], weak[:5], crash_screen


def java_pids_since(started_epoch: float):
    """启动后新出现的 java/javaw 进程（游戏本体），避免误杀别的 Java。"""
    since = datetime.fromtimestamp(started_epoch - 5).strftime("%Y-%m-%dT%H:%M:%S")
    cmd = ("Get-Process java,javaw -ErrorAction SilentlyContinue | "
           "Where-Object { $_.StartTime -ge [datetime]'%s' } | "
           "Select-Object -ExpandProperty Id" % since)
    p = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return [ln.strip() for ln in p.stdout.splitlines() if ln.strip().isdigit()]


def stop_game(started_epoch: float):
    """优雅关游戏（taskkill 不带 /F），留给 superloader 渲染报告的时间。"""
    pids = java_pids_since(started_epoch)
    for pid in pids:
        subprocess.run(["taskkill", "/PID", pid], capture_output=True)
    return pids


REPORT_SRC = INSTANCE / "logs" / "superloader-report"


def snapshot_report(sample: str, out_dir: Path):
    """把本次渲染的报告目录按样本存下来——否则下一轮会覆盖，失败无法归因。"""
    dst = out_dir / sample / "report"
    if dst.exists():
        shutil.rmtree(dst)
    stats = {}
    if REPORT_SRC.exists():
        shutil.copytree(REPORT_SRC, dst)
    try:
        mods = json.loads((REPORT_SRC / "mods.json").read_text("utf-8"))
        stats["mods"] = mods.get("count")
        stats["mod_issues"] = [i.get("code") for i in mods.get("issues") or []]
        apis = json.loads((REPORT_SRC / "apis.json").read_text("utf-8"))
        stats["api_issues"] = [i.get("code") for i in apis.get("issues") or []]
        mix = json.loads((REPORT_SRC / "mixins.json").read_text("utf-8"))
        stats["mixins_failed"] = mix.get("failed") or 0
        launch = json.loads((REPORT_SRC / "launch.json").read_text("utf-8"))
        stats["launch_exit"] = launch.get("exit_code")
    except Exception as e:  # 报告缺失不应让整轮崩
        stats["error"] = str(e)
    return stats


def run_one(sample, closure, timeout_s: int, hard_cap_s: int, out_dir: Path, live: bool = False):
    mods_dir = INSTANCE / "mods.compat" / sample
    if live:
        info = {"installed": sorted(p.name for p in (INSTANCE / "mods").glob("*.jar"))}
    else:
        info, err = prepare(sample, closure, mods_dir)
        if err:
            return {"sample": sample, "verdict": "fail", "reason": err, "infra": info}
    restore_save()

    runtime_json = INSTANCE / "logs" / "superloader-report" / "runtime.json"
    before = runtime_json.stat().st_mtime if runtime_json.exists() else 0.0
    crash_dir = INSTANCE / "crash-reports"
    crash_before = {p.name for p in crash_dir.glob("*.txt")} if crash_dir.exists() else set()
    level_dat = INSTANCE / "saves" / "新的世界" / "level.dat"
    level_before = level_dat.stat().st_mtime if level_dat.exists() else 0.0

    env = dict(os.environ)
    if not live:
        env["SL_MODS_DIR"] = str(mods_dir)
    env["SL_QUICKPLAY"] = "新的世界"
    started = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / ("%s.launch.log" % sample)

    if not live:
        stage_mods(mods_dir)
        guard_fml_config()

    proc = subprocess.Popen([sys.executable, "superloader.py", "launch"], cwd=str(ROOT),
                            env=env, stdout=open(log_path, "wb"), stderr=subprocess.STDOUT)
    fresh = False
    crash_new = []
    strong, weak = [], []
    try:
        while proc.poll() is None:
            now = time.time()
            if runtime_json.exists() and runtime_json.stat().st_mtime > before:
                fresh = True
            crash_new = sorted({p.name for p in crash_dir.glob("*.txt")} - crash_before) if crash_dir.exists() else []
            if log_path.exists():
                fatal, strong, weak, crash_screen = scan_log(log_path.read_text("utf-8", "replace"))
                if strong or crash_new or crash_screen:
                    break
                if fatal:  # 启动期 FATAL：不会再进世界，等 3 秒收尾就够了
                    time.sleep(3)
                    break
            if not fresh and now - started > timeout_s:
                break
            if now - started > hard_cap_s:
                break
            time.sleep(2)
    finally:
        # 关的是游戏进程（java），不是 python 包装器——包装器退出前要渲染报告。
        if strong:
            time.sleep(2)  # 让进入世界后的首批初始化跑完，避免杀在半路
        killed = stop_game(started)
        rc = proc.poll()
        if rc is None:
            try:
                rc = proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                for pid in killed:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                subprocess.run(["taskkill", "/F", "/PID", str(proc.pid)], capture_output=True)
                rc = proc.wait(timeout=30)
        if not live:
            restore_mods()
    duration = round(time.time() - started, 1)
    text = log_path.read_text("utf-8", "replace") if log_path.exists() else ""
    fatal, strong, weak, crash_screen = scan_log(text)
    level_touched = level_dat.exists() and level_dat.stat().st_mtime > level_before + 1

    sample_loaded = None if live else sample_loaded_from_report(closure, sample)[0]

    if fatal:
        verdict, reason = "fail", "fatal_in_log"
    elif crash_new or crash_screen:
        verdict, reason = "fail", "crash_screen"
    elif not fresh:
        verdict, reason = "fail", "timeout_no_runtime"
    elif not live and sample_loaded is not True:
        verdict, reason = "fail", "sample_not_loaded"
    elif not strong:
        verdict, reason = "fail", "no_world_join"
    else:
        verdict, reason = "pass", "ok"

    stats = snapshot_report(sample, out_dir)
    return {
        "sample": sample, "verdict": verdict, "reason": reason,
        "exit_code": rc, "duration_s": duration,
        "runtime_fresh": fresh, "crash_reports": crash_new,
        "fatal": fatal, "world_join_strong": strong[:3], "world_join_weak": weak[:3],
        "level_dat_touched": level_touched, "sample_loaded": sample_loaded,
        "sample_jar": own_jar(closure, sample),
        "log": str(log_path), "mods_dir": str(mods_dir),
        "installed_jars": len(info.get("installed") or []),
        "jar_names": info.get("installed") or [],
        "report": stats,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="auto")
    ap.add_argument("--sample")
    ap.add_argument("--plan", action="store_true", help="只打印拼装计划")
    ap.add_argument("--prepare", action="store_true", help="拼装但不启动")
    ap.add_argument("--timeout", type=int, default=240, help="等待新 runtime.json 的秒数")
    ap.add_argument("--hard-cap", type=int, default=900, help="单样本最长运行秒数")
    ap.add_argument("--live", action="store_true",
                    help="不设 SL_MODS_DIR、用实例现有 mods/ 跑一次（回归检查：默认行为不变）")
    ap.add_argument("--restore-mods", action="store_true",
                    help="把 mods.__baseline 换回 mods/（异常中断后手动收尾）")
    ap.add_argument("--raw-jar", help="负例控制：直接把任意 jar 放进样本 mods 跑（不是 corpus 样本）")
    args = ap.parse_args(argv)

    if args.restore_mods:
        restore_mods()
        print("[mods] 已恢复实例 mods/")
        return 0

    corpus = load_json(CORPUS)
    closure = {r["slug"]: r for r in closure_all()}

    if args.raw_jar:
        if not args.sample:
            raise SystemExit("--raw-jar 需要同时给 --sample <标签>")
        src = Path(args.raw_jar)
        if not src.is_absolute():
            src = (ROOT / src).resolve()
        dst = JAR_CACHE / src.name
        JAR_CACHE.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
        closure[args.sample] = {"slug": args.sample, "mod_id": args.sample, "file": src.name,
                                "install": [{"file": src.name, "id": args.sample,
                                             "sha1": sha1_of(dst), "kind": "fabric"}]}

    if args.live:
        out_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        r = run_one("live-default-mods", closure, args.timeout, args.hard_cap, out_dir, live=True)
        results.append(r)
        print("[live] %s (%s) exit=%s fresh=%s strong_join=%s level_dat=%s" % (
            r["verdict"], r["reason"], r.get("exit_code"), r.get("runtime_fresh"),
            len(r.get("world_join_strong") or []), r.get("level_dat_touched")), flush=True)
        print("[live] jars=%d: %s" % (len(r.get("jar_names") or []), ", ".join(r.get("jar_names") or [])))
        (out_dir / "live.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), "utf-8")
        print("[out] %s" % out_dir)
        return 0

    samples = [args.sample] if args.sample else [r["slug"] for r in sample_group(corpus, args.group)]
    samples = [s for s in samples if args.raw_jar or s in closure]

    if args.plan or args.prepare:
        for s in samples:
            mods_dir = INSTANCE / "mods.compat" / s
            info = plan(s, closure, mods_dir)
            bad = [j["file"] for j in info["jars"] if not j["ok"]]
            print("%-42s jars=%-2d runtime=%s%s" % (
                s, len(info["jars"]), ",".join(info["runtime"]),
                ("  ⚠ 缺/sha1 不符: " + ", ".join(bad)) if bad else ""))
            if args.prepare:
                _, err = prepare(s, closure, mods_dir)
                print("    prepare:", err or "ok")
        return 0

    run_dir = OUT_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for s in samples:
        print("[run] %s" % s, flush=True)
        r = run_one(s, closure, args.timeout, args.hard_cap, run_dir)
        results.append(r)
        print("  -> %s (%s) exit=%s fresh=%s loaded=%s join=%s" % (
            r["verdict"], r["reason"], r.get("exit_code"), r.get("runtime_fresh"),
            r.get("sample_loaded"), len(r.get("world_join_strong") or [])), flush=True)

    ts = run_dir.name
    out_dir = run_dir
    (out_dir / "compat.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), "utf-8")
    lines = ["# 兼容评测结果 %s" % ts, "", "覆盖范围：客户端侧（内容层不在口径内）", ""]
    lines.append("| 样本 | 判定 | 原因 | 样本已加载 | 用时(s) | mods | 模组问题 | API 问题 | mixins failed | 进存档强证据 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        rep = r.get("report") or {}
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["sample"], r["verdict"], r["reason"],
            {True: "yes", False: "NO", None: "-"}.get(r.get("sample_loaded"), "-"),
            r.get("duration_s"),
            rep.get("mods", "?"),
            ",".join(rep.get("mod_issues") or []) or "-",
            ",".join(rep.get("api_issues") or []) or "-",
            rep.get("mixins_failed", "?"),
            len(r.get("world_join_strong") or [])))
    (out_dir / "compat.md").write_text("\n".join(lines) + "\n", "utf-8")
    print("[out] %s" % out_dir)
    return 0


_closure_cache = None


def closure_all():
    global _closure_cache
    if _closure_cache is None:
        d = load_json(CLOSURE)
        _closure_cache = [r for g in ("main", "infra", "content_phase2") for r in d[g]]
    return _closure_cache


if __name__ == "__main__":
    raise SystemExit(main())
