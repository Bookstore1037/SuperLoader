import json
import pathlib
import re
import subprocess
import tempfile
import zipfile

TINY = pathlib.Path(r"D:\SuperLoader\logs\tmp-tiny-mappings.tiny")
CONNECTOR = pathlib.Path(r"D:\SLData\instances\1.21.1\mods") 
# export tiny from connector jar once
if not TINY.exists():
    cj = next(pathlib.Path(r"D:\SLData\instances\1.21.1\mods").glob("connector-*.jar"))
    with zipfile.ZipFile(cj) as zf:
        TINY.write_bytes(zf.read("mappings/mappings.tiny"))

inter2moj = {}
with TINY.open("r", encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("CLASS\t"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4:
                inter2moj[p[2]] = p[3]

targets = {
    "cave_dust": "net/minecraft/class_638$class_5271",
    "fastquit": "net/minecraft/class_32$class_5143",
    "held-item-info": "net/minecraft/class_7225$class_7874",
    "language-reload": "net/minecraft/class_426$class_4195",
    "fallingleaves": "net/minecraft/class_702$class_4090",
    "trinkets": "net/minecraft/class_1799$class_9284",
}

jar = r"D:\SLData\instances\1.21.1\libraries\net\minecraft\client\1.21.1-20240808.144430\client-1.21.1-20240808.144430-srg.jar"
javap = r"C:\Program Files\Java\jdk-21\bin\javap.exe"

for mod, inter in targets.items():
    moj = inter2moj.get(inter)
    if not moj:
        print(mod, inter, "NO MAPPING")
        continue
    cls = moj.replace("/", ".")
    try:
        out = subprocess.run([javap, "-v", "-p", "-cp", jar, cls], capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        print(mod, cls, "ERR", e)
        continue
    head = out.splitlines()[1] if len(out.splitlines()) > 1 else ""
    flags = ""
    for i, line in enumerate(out.splitlines()):
        if "flags:" in line:
            flags = line.strip()
            break
    inner = []
    for line in out.splitlines():
        if "MutableSpriteSet=" in line or "InnerClasses:" in line:
            inner.append(line.strip())
    print("%-14s %-60s %-40s %s" % (mod, cls, flags, head.strip()[:60]))
