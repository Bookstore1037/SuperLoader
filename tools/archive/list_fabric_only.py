import json
rows=json.load(open('logs/compat_corpus_600.json',encoding='utf-8'))
f=[r for r in rows if r.get('has_fabric') and not r.get('has_neoforge')]
seen=set(); out=[]
for r in f:
    if r['slug'] in seen: continue
    seen.add(r['slug']); out.append(r)
print(len(out))
for r in out:
    print('%-32s %-12d %-28s %s' % (r['slug'], r['downloads'], r.get('fabric_version'), r.get('categories')))
