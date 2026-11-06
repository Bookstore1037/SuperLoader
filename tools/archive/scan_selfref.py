import zipfile, pathlib
mods = pathlib.Path(r"D:\SLData\instances\1.21.1\mods")
for jar in sorted(mods.glob("*.jar")):
    try:
        with zipfile.ZipFile(jar) as z:
            for n in z.namelist():
                if n.endswith("mods.toml") or n.endswith("fabric.mod.json"):
                    t = z.read(n).decode("utf-8", "replace")
                    if "superloader_companion" in t and jar.name != "superloader_companion-0.5.1.jar":
                        print(jar.name, n)
                        for line in t.splitlines():
                            if "superloader_companion" in line or "version" in line.lower():
                                print("   ", line.strip()[:120])
    except Exception as e:
        print("ERR", jar.name, e)
