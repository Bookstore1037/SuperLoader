import pathlib, re

gp = pathlib.Path(r'D:\IDEA_mods\nfprobe\gradle.properties')
s = gp.read_text(encoding='utf-8')
s2 = re.sub(r'(?m)^mod_version\s*=.*$', 'mod_version=0.5.2', s)
gp.write_text(s2, encoding='utf-8')

j = pathlib.Path(r'D:\IDEA_mods\nfprobe\src\main\java\com\superloader\companion\SuperLoaderCompanion.java')
t = j.read_text(encoding='utf-8')
t2 = re.sub(r'VERSION\s*=\s*"[^"]*"', 'VERSION = "0.5.2"', t)
j.write_text(t2, encoding='utf-8')

print([l for l in s2.splitlines() if 'mod_version' in l])
print([l for l in t2.splitlines() if 'VERSION' in l][:3])
