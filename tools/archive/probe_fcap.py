import json, urllib.request, urllib.parse
UA={'User-Agent':'SuperLoader-compat/1.0'}
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))
c=json.load(open('.cache/compat/deps_cache.json',encoding='utf-8'))
print('cache entry:', json.dumps(c.get('forgeconfigapiport'), ensure_ascii=False)[:400])
for slug in ('forge-config-api-port','forgeconfigapiport'):
    try:
        p=get('https://api.modrinth.com/v2/project/'+slug)
        vs=get('https://api.modrinth.com/v2/project/%s/version?game_versions=%%5B%%221.21.1%%22%%5D'%p['id'])
        print(slug,'->',p['slug'],p['title'],'versions:',len(vs),[ (v['version_number'],v['loaders']) for v in sorted(vs,key=lambda v:v['date_published'])[-3:]])
    except Exception as e:
        print(slug,'ERR',e)
