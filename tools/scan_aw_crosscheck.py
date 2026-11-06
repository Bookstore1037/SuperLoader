import json
import pathlib
import zipfile

scan = json.loads(pathlib.Path("logs/inner_accessor_scan.json").read_text("utf-8"))
rows = []
for r in scan["jars"]:
    p = pathlib.Path(r["jar"])
    zf = zipfile.ZipFile(p)
    try:
        fmj = json.loads(zf.read("fabric.mod.json").decode("utf-8", "replace"), strict=False)
    except Exception:
        fmj = {}
    aw = fmj.get("accessWidener")
    awf = [n for n in zf.namelist() if n.endswith(".accesswidener")]
    rows.append((p.name, aw, awf, len(r["hits"])))

for name, aw, awf, n in sorted(rows, key=lambda x: x[0]):
    print("%-46s declared=%-28s files=%s hits=%d" % (name[:46], str(aw)[:28], awf, n))
