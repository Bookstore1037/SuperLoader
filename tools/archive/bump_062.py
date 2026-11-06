import pathlib
import re

root = pathlib.Path(r'D:\IDEA_mods\nfprobe')
java = root / 'src/main/java/com/superloader/companion/SuperLoaderCompanion.java'
t = java.read_text(encoding='utf-8')
t2 = re.sub(r'VERSION = "\d+\.\d+\.\d+"', 'VERSION = "0.6.2"', t)
assert t2 != t
java.write_text(t2, encoding='utf-8')

g = root / 'gradle.properties'
s = g.read_text(encoding='utf-8')
s2 = re.sub(r'(?m)^mod_version=.*$', 'mod_version=0.6.2', s)
assert s2 != s
g.write_text(s2, encoding='utf-8')
print('bumped to 0.6.2')
