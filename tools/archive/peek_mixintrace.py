import json
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
r=[x for x in d['main'] if x['slug']=='mixintrace'][0]
print(json.dumps({k:v for k,v in r.items() if k not in ('entries','install')}, ensure_ascii=False, indent=1))
print(json.dumps(r['install'], ensure_ascii=False, indent=1)[:600])
