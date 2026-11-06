import json, urllib.request, urllib.parse
UA={'User-Agent':'SuperLoader-compat/1.0'}
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
by={r['slug']:r for g in ('main','infra','content_phase2') for r in d[g]}
for slug in ('replaymod','inmis','universal-graves','modmenu','krypton'):
    r=by[slug]
    vs=get('https://api.modrinth.com/v2/project/%s/version?game_versions=%%5B%%221.21.1%%22%%5D'%r['project_id'])
    print(slug, 'versions:', len(vs))
    for v in vs[:6]:
        print('   ', v['version_number'], v['loaders'], v['date_published'][:10])
