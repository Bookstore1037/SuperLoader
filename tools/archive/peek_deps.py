import json
c=json.load(open('compat/corpus.json',encoding='utf-8'))
for s in ('modmenu','zoomify','lenient-death','presence-footsteps'):
    r=[x for x in c['main'] if x['slug']==s][0]
    print(s, r['provenance'], 'conn_dep=',r['connector_dep'], '|', [(d['id'],d['loader']) for d in r.get('deps_detail') or []])
