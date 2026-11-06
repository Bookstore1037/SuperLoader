import json
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
yes=[r for g in ('main','infra','content_phase2') for r in d[g] if r.get('nf_build')=='yes']
print('nf=yes:', len(yes))
for r in yes: print(' ', r['group'], r['slug'], '|', r.get('nf_evidence'))
print('nf=no:', sum(1 for g in d for r in d[g] if r.get('nf_build')=='no'))
print('missing nf:', [r['slug'] for g in d for r in d[g] if r.get('nf_build') not in ('yes','no')])
print()
print('main auto:', [r['slug'] for r in d['main'] if r.get('verdict_mode')=='auto'])
print('main fail:', [(r['slug'],r.get('expected_layer')) for r in d['main'] if r.get('expected')=='fail'])
print('jars unique:', len({it['file'] for g in d for r in d[g] for it in r.get('install',[])}))
print('sha1 missing:', [it['file'] for g in d for r in d[g] for it in r.get('install',[]) if not it.get('sha1')])
