import json, pathlib, zipfile
p = pathlib.Path(r"D:\SLData\instances\1.21.1\logs\superloader-report\mixins.json")
ents = json.loads(p.read_text(encoding="utf-8"))
print("entries:", len(ents))
from collections import Counter
print("statuses:", Counter(e.get("status") for e in ents))
ya = [e for e in ents if e.get("mod")=="yet_another_config_lib_v3"]
print("yacl mixins:", len(ya))
for e in ya:
    print("  ", e.get("config"), e.get("mixin"), e.get("status"), "| targets:", e.get("targets"))
jar = pathlib.Path(r"D:\IDEA_mods\nfprobe\build\libs\superloader_companion-0.5.1.jar")
with zipfile.ZipFile(jar) as z:
    for n in z.namelist():
        if "mods.toml" in n or n.endswith("fabric.mod.json") or n.endswith(".toml"):
            t = z.read(n).decode("utf-8", "replace")
            print("==", n)
            for line in t.splitlines():
                if "version" in line.lower():
                    print("   ", line.strip()[:120])
