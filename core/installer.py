# core/installer.py
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from core.downloader import Downloader
from core.paths import Paths, NF_VERSION

MIRROR_HOST = "neoforged.forgecdn.net"
OFFICIAL_HOST = "maven.neoforged.net"
PATCH_TARGETS = {"version.json", "install_profile.json"}


class Installer:
    def __init__(self, paths: Paths, downloader: Downloader):
        self.paths = paths
        self.downloader = downloader

    def install(self) -> None:
        if self.paths.libraries.is_dir():
            print("[安装] libraries 已存在，跳过")
            return

        self._download_installer()
        self._patch_installer()
        self._run_installer()

    def _download_installer(self) -> None:
        urls = [
            f"https://{OFFICIAL_HOST}/releases/net/neoforged/neoforge/"
            f"{NF_VERSION}/neoforge-{NF_VERSION}-installer.jar",
            f"https://{MIRROR_HOST}/releases/net/neoforged/neoforge/"
            f"{NF_VERSION}/neoforge-{NF_VERSION}-installer.jar",
        ]
        dest = self.paths.installer_original
        if dest.is_file():
            print(f"[安装] installer 已存在: {dest}")
            return
        for u in urls:
            try:
                print(f"[安装] 下载 installer: {u}")
                self.downloader.download(u, dest)
                return
            except Exception as e:
                print(f"[安装] 下载失败: {e}")
        raise RuntimeError("所有 installer 下载源都失败")

    def _patch_installer(self) -> None:
        src = self.paths.installer_original
        dst = self.paths.installer_patched
        if dst.is_file():
            print(f"[安装] patched installer 已存在: {dst}")
            return

        total = 0
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in PATCH_TARGETS:
                    text = data.decode("utf-8")
                    c = text.count(OFFICIAL_HOST)
                    if c:
                        text = text.replace(OFFICIAL_HOST, MIRROR_HOST)
                        data = text.encode("utf-8")
                        total += c
                zout.writestr(item, data)
        print(f"[安装] installer 已打补丁，替换 {total} 处 -> {dst}")

    def _run_installer(self) -> None:
        instance = self.paths.instance
        instance.mkdir(parents=True, exist_ok=True)

        profiles = instance / "launcher_profiles.json"
        if not profiles.is_file():
            profiles.write_text(
                '{"profiles":{},"selectedProfile":"","clientToken":"",'
                '"authenticationDatabase":{},"launcherVersion":{"name":"","format":21}}',
                encoding="utf-8",
            )
            print(f"[安装] 写入占位 launcher_profiles.json")

        print(f"[安装] 运行 installer -> {instance}")
        code = subprocess.call([
            "java", "-jar", str(self.paths.installer_patched),
            "--installClient", str(instance),
        ])
        if code != 0:
            raise RuntimeError(f"installer 退出码 {code}")
        print("[安装] 完成")