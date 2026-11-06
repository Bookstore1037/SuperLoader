import json, hashlib, pathlib
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
J=pathlib.Path('.cache/compat/jars')
seen={}
for g in ('main','infra','content_phase2'):
    for r in d[g]:
        for it in r['install']:
            seen[it['file']]=it
bad=[]
for fn,it in seen.items():
    p=J/fn
    if not p.exists(): bad.append((fn,'missing')); continue
    h=hashlib.sha1(p.read_bytes()).hexdigest()
    if h!=it.get('sha1'): bad.append((fn,h,it.get('sha1')))
print('jars', len(seen), 'mismatch', len(bad))
for b in bad[:5]: print(b)
r=d['main'][0]
print('sample fields:', {k:r[k] for k in ('slug','version_id','sha1','file_size','loader','nf_build')})
