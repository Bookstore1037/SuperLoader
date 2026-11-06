import json
d = json.load(open('compat/deps_closure.json', encoding='utf-8'))
for g in ('main','infra','content_phase2'):
    for r in d[g]:
        if not r.get('ok'):
            print(g, r['slug'], r.get('error') or r.get('issues'))
