import json
d = json.load(open('compat/deps_closure.json', encoding='utf-8'))
for group in ('main','infra','content_phase2'):
    for r in d[group]:
        if not r.get('ok'):
            print(group, r['slug'], r.get('error') or '')
            for i in r.get('issues', []):
                print('   issue:', i)
print('--- incomplete-by-dep ---')
from collections import Counter
c = Counter()
for group in ('main','infra','content_phase2'):
    for r in d[group]:
        for i in r.get('issues', []):
            c[(i['id'], i.get('kind'), i.get('spec'))] += 1
for k, v in c.most_common():
    print(v, k)
