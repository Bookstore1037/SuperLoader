import pathlib

p = pathlib.Path(r'D:\IDEA_mods\nfprobe\src\main\java\com\superloader\companion\repair\RefmapRepair.java')
s = p.read_text(encoding='utf-8')

s = s.replace("        Path cache = null;\n        Path corpus = null;",
              "        Path cache = null;\n        Path corpus = null;\n        List<Path> mcJars = new ArrayList<>();", 1)
s = s.replace('                case "--yarn-sha1" -> yarnSha1 = args[++i];',
              '                case "--yarn-sha1" -> yarnSha1 = args[++i];\n                case "--mc-jar" -> mcJars.add(Path.of(args[++i]));', 1)

s = s.replace("        TinyMappings tiny = TinyMappings.load(connector);\n",
              "        TinyMappings tiny = TinyMappings.load(connector);\n"
              "        McClasses mc = mcJars.isEmpty() ? null : new McClasses(mcJars);\n"
              '        out.put("mc_jars", mcJars.stream().map(p -> p.getFileName().toString()).toList());\n', 1)

s = s.replace("Resolved resolved = resolve(ci, tiny, yarn);", "Resolved resolved = resolve(ci, tiny, yarn, mc);")
s = s.replace("private static Resolved resolve(ClassFileInfo ci, TinyMappings tiny, YarnMappings yarn) {",
              "private static Resolved resolve(ClassFileInfo ci, TinyMappings tiny, YarnMappings yarn, McClasses mc) {")
s = s.replace('put(map, refs, s, value, "intermediary", verify(tiny, value));',
              'put(map, refs, s, value, "intermediary", verify(tiny, mc, value));')
s = s.replace('put(map, refs, s, value, via, verify(tiny, value));',
              'put(map, refs, s, value, via, verify(tiny, mc, value));')
s = s.replace('boolean ok = verify(tiny, value);', 'boolean ok = verify(tiny, mc, value);')

s = s.replace("    private static boolean verify(TinyMappings tiny, String value) {",
              "    private static boolean verify(TinyMappings tiny, McClasses mc, String value) {", 1)

old_tail = """        return tiny.hasMojangMember(owner, name, desc);
    }"""
new_tail = """        if (mc != null) {
            boolean method = rest.indexOf('(') >= 0;
            Boolean runtime = mc.hasMember(owner, name, desc, method);
            if (runtime != null) {
                return runtime;
            }
        }
        return tiny.hasMojangMember(owner, name, desc);
    }"""
assert old_tail in s
s = s.replace(old_tail, new_tail, 1)

p.write_text(s, encoding='utf-8')
print('patched')
