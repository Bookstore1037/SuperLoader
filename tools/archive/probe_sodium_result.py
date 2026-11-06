import json,pathlib
r=pathlib.Path(r'D:\SLData\instances\1.21.1\logs\superloader-report')
mods=json.loads((r/'mods.json').read_text('utf-8'))
for m in mods['mods']:
    if 'sodium' in (m.get('mod_id') or '') or 'sodium' in json.dumps(m,ensure_ascii=False).lower():
        print(json.dumps({k:m.get(k) for k in ('mod_id','name','version','target','jar','loaded','versions')},ensure_ascii=False)[:600])
apis=json.loads((r/'apis.json').read_text('utf-8'))
print('ffapi totals:',json.dumps(apis['totals'],ensure_ascii=False))
dep=[d for d in apis['fabric_depends'] if 'sodium' in json.dumps(d,ensure_ascii=False).lower()]
print('sodium depends entry:',json.dumps(dep,ensure_ascii=False)[:500])
cls=json.loads((r/'classloading.json').read_text('utf-8'))
print('cls totals:',json.dumps(cls.get('totals') or cls.get('counts') or {},ensure_ascii=False)[:400])
ev=json.loads((r/'events_report.json').read_text('utf-8'))
print('events keys:',list(ev.keys())[:8])
print('events coverage:',json.dumps(ev.get('coverage') or ev.get('totals') or {},ensure_ascii=False)[:300])
