import re
import subprocess

out = subprocess.run(
    [r"C:\Program Files\Java\jdk-21\bin\javap.exe", "-v", "-p", "-cp",
     r"D:\SuperLoader\logs\bz",
     "com.telepathicgrunt.the_bumblezone.mixin.fabric.entity.LivingEntityMixin"],
    capture_output=True, text=True).stdout

# constant pool: map index -> utf8 string
cp = {}
for m in re.finditer(r"^\s+#(\d+) = Utf8\s+(.*)$", out, re.M):
    cp[int(m.group(1))] = m.group(2)
for m in re.finditer(r"^\s+#(\d+) = String\s+#(\d+)", out, re.M):
    cp[int(m.group(1))] = cp.get(int(m.group(2)), "?")

lines = out.splitlines()
blocks, cur = [], None
for ln in lines:
    if re.match(r"^  (public|protected|private).*\(.*\).*;$", ln):
        cur = [ln]
        blocks.append(cur)
    elif cur is not None:
        cur.append(ln)

for b in blocks:
    body = "\n".join(b)
    if "bumblezone$" not in b[0]:
        continue
    print("=====", b[0].strip())
    # dump the annotation section with cp references resolved inline
    started = False
    for ln in b:
        if "RuntimeInvisibleAnnotations" in ln or "RuntimeVisibleAnnotations" in ln:
            started = True
        if started:
            m = re.search(r"#(\d+)", ln)
            print(ln.rstrip(), "   <-", cp.get(int(m.group(1)), "") if m else "")
        if started and ln.strip() == "":
            started = False
