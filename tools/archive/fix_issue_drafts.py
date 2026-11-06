import pathlib

ISS = pathlib.Path(r"D:\SuperLoader\compat\issues")
BLOCK = (
    "### Logs\n\n"
    "- `debug.log` (NeoForge debug log, crashing run): <link>\n"
    "- `crash-report.txt`: <link>\n\n"
)

for f in sorted(ISS.glob("0*.md")):
    t = f.read_text("utf-8")
    s = t.find("### Logs")
    e = t.find("### Additional context")
    if s < 0 or e < 0:
        print("skip", f.name)
        continue
    t = t[:s] + BLOCK + t[e:]
    f.write_text(t, encoding="utf-8")
    print("logs fixed:", f.name)

p = ISS / "01-replaymod.md"
t = p.read_text("utf-8")
old = (
    "- Original annotation (jar) vs. transformed annotation (`.cache/connector/replaymod-1.21-2.6.28_mapped_moj_1.21.1.jar`) and the\n"
    "  NeoForge `GameRenderer.render` bytecode offsets are collected in\n"
    "  `compat/connector-issues.md` (§1) of our local notes — happy to paste the full `javap -v` output in a comment."
)
new = (
    "- The two annotation variants above come from the original jar and from the Connector-remapped copy of it; the offsets 289\n"
    "  (`getGameTimeDeltaTicks`) and 745 (`ClientHooks.drawScreen`) are from the vanilla 1.21.1 client classes and the\n"
    "  NeoForge 21.1.265 patched classes. I can paste the full `javap -v` output in a comment if useful."
)
if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("01 context fixed")
else:
    print("01 context: pattern not found")
