"""Run the six minimal repro sets one by one and capture debug.log + crash report.

Each case installs only: connector + forgified fabric api (+ the case's own mods) into
D:\\SLData\\instances\\1.21.1\\mods, launches the game, waits for the crash (or a timeout),
then copies logs/debug.log, logs/latest.log and any new crash report into
D:\\SuperLoader\\compat\\issues\\logs\\<case>\\.

The player's full mod pack lives in mods.bak (moved away by the user); this script never
touches it. Pass --restore to move mods.bak back into mods/ at the end.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(r"D:\SuperLoader")
INST = pathlib.Path(r"D:\SLData\instances\1.21.1")
MODS = INST / "mods"
BAK = INST / "mods.bak"
CACHE = ROOT / ".cache" / "compat" / "jars"
OUT = ROOT / "compat" / "issues" / "logs"
BASE_NAMES = [
    "connector-2.0.0-beta.17+1.21.1-full.jar",
    "forgified-fabric-api-0.116.15+2.3.6+1.21.1.jar",
]


def stage_base() -> list[pathlib.Path]:
    """Copy connector + FFAPI from mods/ or mods.bak into a staging dir once."""
    staged = OUT / "_base"
    staged.mkdir(parents=True, exist_ok=True)
    out = []
    for name in BASE_NAMES:
        dst = staged / name
        if not dst.exists():
            src = None
            for cand in (MODS / name, BAK / name):
                if cand.exists():
                    src = cand
                    break
            if src is None:
                raise SystemExit(f"base jar not found: {name}")
            shutil.copy2(src, dst)
        out.append(dst)
    return out

CASES = [
    dict(key="01-replaymod", jars=[BAK / "replaymod-1.21-2.6.28.jar"],
         quickplay=True, typing=False, timeout=240),
    dict(key="02-minihud", jars=[CACHE / "malilib-fabric-1.21-0.21.10.jar",
                                 CACHE / "minihud-fabric-1.21-0.32.60.jar"],
         quickplay=False, typing=False, timeout=180),
    dict(key="03-bumblezone", jars=[CACHE / "the_bumblezone-7.17.3+1.21.1-fabric.jar",
                                    CACHE / "resourcefullib-fabric-1.21-3.0.12.jar",
                                    CACHE / "midnightlib-fabric-1.10.0+1.21.1.jar"],
         quickplay=False, typing=False, timeout=240),
    dict(key="04-farmers-delight-refabricated",
         jars=[CACHE / "FarmersDelight-1.21.1-3.3.6+refabricated.jar"],
         quickplay=False, typing=False, timeout=180),
    dict(key="05-friends-and-foes", jars=[CACHE / "friendsandfoes-fabric-5.0.4+mc1.21.1.jar",
                                          CACHE / "resourcefullib-fabric-1.21-3.0.12.jar"],
         quickplay=False, typing=False, timeout=180),
    dict(key="06-language-reload", jars=[CACHE / "language-reload-1.7.6+1.21.1.jar"],
         quickplay=True, typing=True, timeout=300),
]

CRASH_HINTS = ("InjectionError", "MixinTransformerError", "Mixin apply for mod",
               "Exception in thread \"main\"", "Could not execute entrypoint",
               "Encountered error while transforming", "crash report")
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
TYPING_PS = (
    "$ws = New-Object -ComObject WScript.Shell; "
    "$ok = $ws.AppActivate('Minecraft'); "
    "Write-Output ('activated=' + $ok); "
    "if ($ok) { Start-Sleep -Milliseconds 3000; "
    "$ws.SendKeys('t'); Start-Sleep -Milliseconds 1200; "
    "$ws.SendKeys('/gamemode creative'); Start-Sleep -Milliseconds 300; "
    "$ws.SendKeys('{ENTER}'); Start-Sleep -Milliseconds 2500; "
    "$ws.SendKeys('e'); Start-Sleep -Milliseconds 4000; "
    "$ws.SendKeys('abc') }"
)


def java_pids() -> set[str]:
    try:
        out = subprocess.run(
            [POWERSHELL, "-NoProfile", "-Command",
             "Get-Process java,javaw -ErrorAction SilentlyContinue | ForEach-Object { $_.Id }"],
            capture_output=True, text=True, timeout=30)
        return {line.strip() for line in out.stdout.splitlines() if line.strip().isdigit()}
    except Exception:
        return set()


def kill_pids(pids: set[str]) -> None:
    for pid in pids:
        for flags in (["/PID", pid], ["/PID", pid, "/F"]):
            subprocess.run(["taskkill.exe", *flags], capture_output=True, text=True)


def snapshot_crashes() -> set[str]:
    d = INST / "crash-reports"
    return {p.name for p in d.glob("*")} if d.exists() else set()


def copy_if_exists(src: pathlib.Path, dst: pathlib.Path) -> bool:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def wait_for_join(deadline: float) -> bool:
    log = INST / "logs" / "debug.log"
    while time.time() < deadline:
        if log.exists():
            try:
                if "Time elapsed" in log.read_text("utf-8", errors="replace"):
                    return True
            except Exception:
                pass
        time.sleep(2)
    return False


def run_case(case: dict, base: list[pathlib.Path]) -> dict:
    key = case["key"]
    out = OUT / key
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    MODS.mkdir(parents=True, exist_ok=True)
    for p in MODS.glob("*.jar"):
        p.unlink()
    for src in base + case["jars"]:
        if not src.exists():
            raise SystemExit(f"missing jar for {key}: {src}")
        shutil.copy2(src, MODS / src.name)

    started = time.time()
    crashes_before = snapshot_crashes()
    pids_before = java_pids()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("SL_JVM_ARGS", None)
    env.pop("SL_MODS_DIR", None)
    if case.get("quickplay"):
        env["SL_QUICKPLAY"] = "新的世界"
    else:
        env.pop("SL_QUICKPLAY", None)

    run_log = open(out / "run.log", "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "superloader.py", "launch"],
                            cwd=str(ROOT), env=env, stdout=run_log, stderr=subprocess.STDOUT)

    typed = False
    crash_at = None
    while True:
        time.sleep(2)
        if proc.poll() is not None:
            break
        if time.time() - started > case["timeout"]:
            break
        new_crashes = snapshot_crashes() - crashes_before
        if new_crashes and crash_at is None:
            crash_at = time.time()
        if crash_at and time.time() - crash_at > 15:
            break
        if case.get("typing") and not typed and time.time() - started > 20:
            if wait_for_join(time.time() + 90):
                subprocess.run([POWERSHELL, "-NoProfile", "-Command", TYPING_PS],
                               capture_output=True, text=True, timeout=120)
                typed = True
                print(f"[{key}] typing sent", flush=True)

    new_pids = java_pids() - pids_before
    if proc.poll() is None and new_pids:
        kill_pids(new_pids)
    try:
        rc = proc.wait(timeout=90)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait()
    run_log.close()

    time.sleep(2)
    new_pids = java_pids() - pids_before
    if new_pids:
        kill_pids(new_pids)

    new_crashes = sorted(snapshot_crashes() - crashes_before)
    report = new_crashes[-1] if new_crashes else None
    got_debug = copy_if_exists(INST / "logs" / "debug.log", out / "debug.log")
    got_latest = copy_if_exists(INST / "logs" / "latest.log", out / "latest.log")
    got_crash = copy_if_exists(INST / "crash-reports" / report, out / "crash-report.txt") if report else False

    text = ""
    if got_debug:
        text = (out / "debug.log").read_text("utf-8", errors="replace")
    hints = [h for h in CRASH_HINTS if h in text]

    result = dict(key=key, exit_code=rc, elapsed_s=round(time.time() - started, 1),
                  jars=[p.name for p in (base + case["jars"])],
                  crash_report=report, debug_log=got_debug, latest_log=got_latest,
                  crash_report_copied=got_crash, hints=hints[:6], typed=typed)
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def restore_pack() -> None:
    if not BAK.exists():
        print("no mods.bak, nothing to restore", flush=True)
        return
    for p in MODS.glob("*.jar"):
        p.unlink()
    moved = 0
    for p in sorted(BAK.glob("*.jar")):
        shutil.move(str(p), str(MODS / p.name))
        moved += 1
    print(f"restored {moved} jars from mods.bak", flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    base = stage_base()
    cases = [c for c in CASES if only is None or c["key"] == only]
    results = []
    for case in cases:
        print(f"=== {case['key']}", flush=True)
        try:
            results.append(run_case(case, base))
        except Exception as exc:  # noqa: BLE001
            print(f"[{case['key']}] FAILED: {exc}", flush=True)
            results.append(dict(key=case["key"], error=str(exc)))
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    if "--restore" in sys.argv:
        restore_pack()
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
