import subprocess

JAR = r"D:\SLData\instances\1.21.1\mods\connector-2.0.0-beta.17+1.21.1-full.jar"
CLS = "org.sinytra.connector.transformer.transform.OptimizedRenamingTransformer$MixinAnnotationVisitor"
JAVAP = r"C:\Program Files\Java\jdk-21\bin\javap.exe"

r = subprocess.run([JAVAP, "-p", "-c", "-cp", JAR, CLS],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout[:12000])
print(r.stderr[:2000])
