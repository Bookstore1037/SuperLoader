import subprocess, sys, re

JAR = r"D:\SLData\instances\1.21.1\mods\connector-2.0.0-beta.17+1.21.1-full.jar"
JAVAP = r"C:\Program Files\Java\jdk-21\bin\javap.exe"

cls = sys.argv[1]
pat = sys.argv[2] if len(sys.argv) > 2 else None
r = subprocess.run([JAVAP, "-p", "-c", "-cp", JAR, cls], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
out = r.stdout or r.stderr
if pat:
    lines = out.splitlines()
    for i, ln in enumerate(lines):
        if re.search(pat, ln):
            print("\n".join(lines[max(0, i - 3):i + 6]))
            print("....")
else:
    print(out[:15000])
