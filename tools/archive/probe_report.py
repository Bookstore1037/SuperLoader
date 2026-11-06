import json,pathlib
r=pathlib.Path(r'D:\SLData\instances\1.21.1\logs\superloader-report')
apis=json.loads((r/'apis.json').read_text('utf-8'))
print('keys:',list(apis.keys()))
for i in apis.get('issues',[]):
    print('ISSUE:',json.dumps(i,ensure_ascii=False)[:500])
mods=json.loads((r/'mods.json').read_text('utf-8'))
print('mods issues:',len(mods.get('issues',[])),'count:',len(mods.get('mods',[])))
