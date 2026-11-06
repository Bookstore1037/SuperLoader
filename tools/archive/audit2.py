import json, collections
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
samples=[r for g in ('main','infra','content_phase2') for r in d[g]]
print('samples', len(samples), 'no sha1:', [r['slug'] for r in samples if not r.get('sha1')], 'no vid:', [r['slug'] for r in samples if not r.get('version_id')])
ld=collections.Counter(it.get('loader') for g in ('main','infra','content_phase2') for r in d[g] for it in r.get('install',[]))
print('install loader dist:', dict(ld))
print('entry kind dist:', dict(collections.Counter(e.get('kind') for g in ('main','infra','content_phase2') for r in d[g] for e in r['entries'])))
print('jit entries:', [ (r['slug'], e['id'], e['version']) for g in ('main','infra','content_phase2') for r in d[g] for e in r['entries'] if e.get('kind')=='jij'][:10])
print('with native:', [(r['slug'], r.get('nf_evidence')) for r in samples if r.get('nf_build')=='yes'])
