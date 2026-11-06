import zipfile, json, io
conn = r"D:\SLData\instances\1.21.1\mods\connector-2.0.0-beta.17+1.21.1-full.jar"
with zipfile.ZipFile(conn) as z:
    data = z.read("mappings/mappings.tiny").decode("utf-8", "replace")
lines = data.splitlines()
print("header:", lines[0])
targets = []
for ln in lines:
    if "\tmethod_30092\t" in ln or "\tmethod_8408\t" in ln:
        targets.append(ln)
for t in targets:
    print("TINY:", t)
# find class_1937 class line
for ln in lines:
    if ln.startswith("CLASS") and ("\tclass_1937\t" in ln or "net/minecraft/world/level/Level" in ln):
        print("CLASS:", ln)
