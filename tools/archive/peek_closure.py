import json
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
r=d['main'][0]
print(json.dumps({k:v for k,v in r.items() if k!='entries'}, ensure_ascii=False, indent=1)[:1500])
print('--- entries[0..2]')
for e in r['entries'][:3]: print(json.dumps(e, ensure_ascii=False))
print('--- install[0]')
print(json.dumps(r['install'][0], ensure_ascii=False))
