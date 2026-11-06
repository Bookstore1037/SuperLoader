import json
d = json.load(open('compat/deps_closure.json', encoding='utf-8'))
for g in ('main','infra','content_phase2'):
    for r in d[g]:
        print(g, r['slug'], r['install_jars'], round(r['install_bytes']/1048576, 1))
