import pathlib

p = pathlib.Path(r'D:\IDEA_mods\nfprobe\src\main\java\com\superloader\companion\repair\RefmapRepair.java')
s = p.read_text(encoding='utf-8')

old = '''                    if (zf.getEntry(refmap) != null) {
                        cfgOut.put("status", "present");
                        configs.add(cfgOut);
                        continue;
                    }'''
new = '''                    if (zf.getEntry(refmap) != null) {
                        cfgOut.put("status", "present");
                        // 已经修补过（或 mod 自带）：仍然逐条校验一遍，保证每次 repair 都产出
                        // "哪些映射真的能在运行时类里找到"的证据，而不是只说一句 present。
                        Existing existing = verifyExisting(read(zf, zf.getEntry(refmap)), tiny, mc);
                        cfgOut.put("entries", existing.count);
                        if (!existing.details.isEmpty()) {
                            cfgOut.put("mappings", existing.details);
                        }
                        if (!existing.bad.isEmpty()) {
                            cfgOut.put("unverified", existing.bad);
                        }
                        entries += existing.count;
                        unresolved += existing.bad.size();
                        configs.add(cfgOut);
                        continue;
                    }'''
assert old in s
s = s.replace(old, new, 1)

anchor = '''    private static boolean verify(TinyMappings tiny, McClasses mc, String value) {'''
helper = '''    /** 已存在的 refmap：逐条复核 value 是否真能在运行期类里找到。 */
    private record Existing(int count, List<Object> details, List<String> bad) {
    }

    private static Existing verifyExisting(String json, TinyMappings tiny, McClasses mc) {
        List<Object> details = new ArrayList<>();
        List<String> bad = new ArrayList<>();
        int count = 0;
        Map<String, Object> root;
        try {
            root = Json.parseObject(json);
        } catch (RuntimeException e) {
            bad.add("refmap 不是合法 JSON: " + e.getMessage());
            return new Existing(0, details, bad);
        }
        if (!(root.get("mappings") instanceof Map<?, ?> classes)) {
            return new Existing(0, details, bad);
        }
        for (Map.Entry<?, ?> cls : classes.entrySet()) {
            if (!(cls.getValue() instanceof Map<?, ?> members)) {
                continue;
            }
            for (Map.Entry<?, ?> m : members.entrySet()) {
                String key = String.valueOf(m.getKey());
                String value = String.valueOf(m.getValue());
                boolean ok = verify(tiny, mc, value);
                count++;
                if (!ok) {
                    bad.add(cls.getKey() + " :: " + key + " -> " + value);
                }
                Map<String, Object> d = new LinkedHashMap<>();
                d.put("class", String.valueOf(cls.getKey()));
                d.put("key", key);
                d.put("value", value);
                d.put("via", "existing");
                d.put("verified", ok);
                details.add(d);
            }
        }
        return new Existing(count, details, bad);
    }

'''
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)
p.write_text(s, encoding='utf-8')
print('existing verification added')
