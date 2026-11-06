import zipfile, json
jar = r"D:\SLData\instances\1.21.1\mods\fabric-carpet-1.21-1.4.147+v240613.jar"
with zipfile.ZipFile(jar) as z:
    rm = json.loads(z.read("fabric-carpet-refmap.json").decode("utf-8"))
    m = rm["mappings"]
    print("classes in refmap:", len(m))
    for k in m:
        if "Level_fillUpdates" in k:
            print("KEY:", k)
            print(json.dumps(m[k], indent=1))
    print("---- config ----")
    cfg = json.loads(z.read("carpet.mixins.json").decode("utf-8"))
    print(json.dumps({k:v for k,v in cfg.items() if k!='mixins' and k!='client' and k!='server'}, indent=1)[:1500])
    print("declared mixins:", [x for x in (cfg.get('mixins') or [])+(cfg.get('client') or []) if 'fillUpdates' in x])
