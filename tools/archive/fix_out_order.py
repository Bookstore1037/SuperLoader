import pathlib

p = pathlib.Path(r'D:\IDEA_mods\nfprobe\src\main\java\com\superloader\companion\repair\RefmapRepair.java')
s = p.read_text(encoding='utf-8')
line = '        out.put("mc_jars", mcJars.stream().map(p -> p.getFileName().toString()).toList());\n'
assert line in s
s = s.replace(line, '', 1)
anchor = '        out.put("dry_run", dryRun);\n'
assert anchor in s
s = s.replace(anchor, anchor + line, 1)
p.write_text(s, encoding='utf-8')
print('moved')
