import pathlib

tiny = pathlib.Path(r'D:\IDEA_mods\nfprobe\src\main\java\com\superloader\companion\repair\TinyMappings.java')
s = tiny.read_text(encoding='utf-8')
anchor = '''    /** 生成 refmap value：{@code L<mojangOwner>;<mojangName><mojangDesc>}（字段用 ':' 分隔名与描述符）。 */'''
helper = '''    /** 静态校验用（intermediary 写法）：value 仍是 intermediary 时，直接用映射表核实成员是否存在。 */
    public boolean hasInterMember(String intermediaryClass, String interName, String interDesc) {
        for (Member m : members(intermediaryClass)) {
            if (!m.interName().equals(interName)) {
                continue;
            }
            if (toIntermediaryDesc(m.officialDesc()).equals(interDesc)) {
                return true;
            }
        }
        return false;
    }

'''
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)
tiny.write_text(s, encoding='utf-8')

rep = pathlib.Path(r'D:\IDEA_mods\nfprobe\src\main\java\com\superloader\companion\repair\RefmapRepair.java')
r = rep.read_text(encoding='utf-8')
old = '''        if (mc != null) {
            boolean method = rest.indexOf('(') >= 0;'''
new = '''        // 老的/自带的 refmap 里 value 往往是 intermediary（Connector 之后会重映射），
        // 这类值只能拿映射表核实，不能拿去 mojang 运行时类里找。
        if (owner.contains("class_") || name.startsWith("method_") || name.startsWith("field_")) {
            return tiny.hasInterMember(owner, name, desc);
        }
        if (mc != null) {
            boolean method = rest.indexOf('(') >= 0;'''
assert old in r
r = r.replace(old, new, 1)
rep.write_text(r, encoding='utf-8')
print('patched')
