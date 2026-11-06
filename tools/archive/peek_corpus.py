import json
c=json.load(open('compat/corpus.json',encoding='utf-8'))
print('keys:', list(c))
for k,v in c.items():
    if isinstance(v,list): print(k,'n=',len(v))
r=c['main'][0]
print('main[0] keys:', list(r))
print(json.dumps({k:r[k] for k in r if k not in ('install',)}, ensure_ascii=False)[:600])
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
print('closure keys:', list(d))
print('jij samples:', [r['slug'] for g in ('main','content_phase2') for r in d[g] if any(e['kind']=='jij' for e in r['entries'])])
