import json
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
for s in ('presence-footsteps','custom-splash-screen'):
    r=[x for x in d['main'] if x['slug']==s][0]
    print(s,'mod_id=',r['mod_id'])
    for e in r['entries']: print('  ',e['id'],e['kind'],'required_by=',e.get('required_by'),'spec=',e.get('spec'))
