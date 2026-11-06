import gzip
import pathlib
import re

LOGS = pathlib.Path(r"D:\SLData\instances\1.21.1\logs")
PAT = re.compile(r"fallingleaves|HARD_DEP|Resolution failed|MutableSpriteSet|connectiblechains", re.I)

rows = []
for f in sorted(LOGS.iterdir()):
    if not f.is_file():
        continue
    try:
        if f.name.endswith(".gz"):
            text = gzip.open(f, "rt", encoding="utf-8", errors="replace").read()
        else:
            text = f.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    hits = [l.strip()[:220] for l in text.splitlines() if PAT.search(l)]
    if hits:
        rows.append((f.name, len(hits), hits[:6]))

for name, n, hits in rows:
    print("==", name, n)
    for h in hits:
        print("   ", h)
