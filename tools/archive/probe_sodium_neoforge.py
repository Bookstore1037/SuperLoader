import json,urllib.request
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SuperLoader-planning/1.0'})
    return json.load(urllib.request.urlopen(req,timeout=30))
data=get('https://api.modrinth.com/v2/project/sodium/version')
sel=[v for v in data if '1.21.1' in v['game_versions'] and 'neoforge' in v['loaders']]
print('neoforge 1.21.1 count:',len(sel))
for v in sorted(sel,key=lambda x:x['date_published'],reverse=True)[:4]:
    print('---')
    print(v['version_number'],'|',v.get('name'))
    print(' date:',v['date_published'][:10],'| featured:',v.get('featured'),'| status:',v.get('status'))
    print(' deps:',[(d.get('project_id'),d.get('dependency_type'),d.get('version_id')) for d in v.get('dependencies') or []])
    for f in v['files']:
        print(' file:',f['filename'],round(f['size']/1e6,2),'MB')
    print(' changelog:',(v.get('changelog') or '')[:300].replace('\n',' / '))
