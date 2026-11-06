import json, pathlib
p=pathlib.Path('compat/corpus.json'); c=json.loads(p.read_text('utf-8'))
REASON={
 'carpet':'用 mixin/ASM 深度改造服务端类与指令树；Connector 的重映射覆盖不到这类“改 vanilla 行为”的注入，预期在 apply 阶段失败',
 'mixintrace':'钩住 Fabric 的 MixinService/agent 内部实现；NeoForge 自带 mixin 服务与 Fabric 版本不同源，预期在类加载/服务替换阶段失败',
}
for r in c['negative']:
    r['expected_reason']=REASON[r['slug']]
p.write_text(json.dumps(c,ensure_ascii=False,indent=1),'utf-8')
print([ (r['slug'], r['expected_reason'][:20]) for r in c['negative']])
