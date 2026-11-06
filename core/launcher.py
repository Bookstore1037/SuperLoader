# core/launcher.py
import json
import os
import subprocess

from core.libraries import os_matches
from core.paths import Paths, NF_ID


def _resolve(value, ctx: dict) -> str:
    for k, v in ctx.items():
        value = value.replace("${" + k + "}", v)
    return value


def _resolve_list(args, ctx: dict) -> list[str]:
    out = []
    for a in args:
        if isinstance(a, str):
            out.append(_resolve(a, ctx))
        elif isinstance(a, dict):
            if os_matches(a.get("rules")):
                v = a.get("value")
                if isinstance(v, str):
                    out.append(_resolve(v, ctx))
                elif isinstance(v, list):
                    out.extend(_resolve(x, ctx) for x in v)
    return out


class Launcher:
    def __init__(self, paths: Paths, classpath: str, memory_mb: int = 4096,
                 javaagent_path: str | None = None):
        self.paths = paths
        self.classpath = classpath
        self.memory_mb = memory_mb
        self.javaagent_path = javaagent_path

    def build(self) -> list[str]:
        mc = json.loads(self.paths.mc_json.read_text(encoding="utf-8"))
        nf = json.loads(self.paths.nf_json.read_text(encoding="utf-8"))

        ctx = {
            "library_directory": str(self.paths.libraries),
            "classpath_separator": ";",
            "version_name": NF_ID,
            "classpath": self.classpath,
            "natives_directory": str(self.paths.natives),
            "launcher_name": "SuperLoader",
            "launcher_version": "1",
            "game_directory": str(self.paths.instance),
            "assets_root": str(self.paths.assets),
            "assets_index_name": mc["assetIndex"]["id"],
            "auth_player_name": "Steve",
            "auth_uuid": "0" * 32,
            "auth_access_token": "0",
            "clientid": "",
            "auth_xuid": "",
            "user_type": "legacy",
            "version_type": "release",
        }

        cmd = ["java", f"-Xmx{self.memory_mb}M"]
        extra = os.environ.get("SL_JVM_ARGS", "").strip()
        if extra:
            cmd += extra.split()
        if self.javaagent_path:
            cmd.append(f"-javaagent:{self.javaagent_path}")
        cmd += _resolve_list(nf["arguments"]["jvm"], ctx)
        cmd += _resolve_list(mc["arguments"]["jvm"], ctx)
        cmd.append(nf["mainClass"])
        cmd += _resolve_list(nf["arguments"]["game"], ctx)
        cmd += _resolve_list(mc["arguments"]["game"], ctx)
        quickplay = os.environ.get("SL_QUICKPLAY", "").strip()
        if quickplay:
            cmd += ["--quickPlaySingleplayer", quickplay]
        return cmd

    def launch(self) -> int:
        cmd = self.build()
        print("[launch] 启动中...")

        log_path = self.paths.instance / "logs" / "superloader-launch.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        proc = subprocess.Popen(
            cmd,
            cwd=str(self.paths.instance),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        with open(log_path, "w", encoding="utf-8", errors="replace") as logf:
            for line in proc.stdout:
                logf.write(line)
                logf.flush()
                try:
                    print(line, end="")
                except UnicodeEncodeError:
                    print(line.encode("ascii", "replace").decode("ascii"), end="")

        return proc.wait()