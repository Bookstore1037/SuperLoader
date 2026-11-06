import re
import subprocess

out = subprocess.run(
    [r"C:\Program Files\Java\jdk-21\bin\javap.exe", "-v", "-p", "-cp",
     r"D:\SuperLoader\logs\bz",
     "com.telepathicgrunt.the_bumblezone.mixin.fabric.entity.LivingEntityMixin"],
    capture_output=True, text=True).stdout

text = out
# split at method declarations near the end
idx = text.find("  public ")
lines = text.splitlines()
blocks = []
cur = None
for i, ln in enumerate(lines):
    if re.match(r"^  (public|protected|private).*\(.*\).*;$", ln):
        cur = [ln]
        blocks.append(cur)
    elif cur is not None:
        cur.append(ln)

for b in blocks:
    head = b[0].strip()
    body = "\n".join(b)
    anns = re.findall(r"\b(ModifyReturnValue|Inject|Redirect|ModifyVariable|WrapOperation|ModifyExpressionValue|ModifyArg|ModifyArgs|At|Constant|Slice)\b[^\n]*", body)
    print("==", head)
    for a in anns[:10]:
        print("   ", a.strip()[:240])
