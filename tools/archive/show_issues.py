import json
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
for g in ('main','infra','content_phase2'):
    for r in d[g]:
        if r.get('issues') or r.get('error'):
            print(g, r['slug'], 'error=', r.get('error'))
            for i in r.get('issues') or []: print('   ', json.dumps(i, ensure_ascii=False))
            for e in r.get('entries') or []:
                if not e.get('ok'): print('    entry:', json.dumps(e, ensure_ascii=False))
