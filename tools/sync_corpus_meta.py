import json, pathlib
d = json.load(open('compat/deps_closure.json', encoding='utf-8'))
p = pathlib.Path('compat/corpus.json')
c = json.loads(p.read_text('utf-8'))
by = {r['slug']: r for g in ('main','infra','content_phase2') for r in d[g]}
n = 0
for g in ('main','infra','content_phase2'):
    for e in c[g]:
        r = by.get(e['slug'])
        if not r: continue
        e['version'] = r.get('mod_version'); e['file'] = r.get('file'); e['url'] = r.get('url')
        e['sha1'] = r.get('sha1'); e['version_id'] = r.get('version_id')
        e['nf_build'] = r.get('nf_build'); e['nf_evidence'] = r.get('nf_evidence')
        n += 1
p.write_text(json.dumps(c, ensure_ascii=False, indent=1), 'utf-8')
print('synced', n)
