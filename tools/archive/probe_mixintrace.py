import json, urllib.request, urllib.parse
UA={'User-Agent':'SuperLoader-compat/1.0'}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))
c=json.load(open('.cache/compat/deps_cache.json',encoding='utf-8'))
print('cache:', json.dumps(c.get('mixintrace'), ensure_ascii=False)[:500])
vs=get('https://api.modrinth.com/v2/project/mixintrace/version?game_versions=%5B%221.21.1%22%5D')
for v in vs: print(v['id'], v['version_number'], v['files'][0]['filename'], v['files'][0]['url'])
