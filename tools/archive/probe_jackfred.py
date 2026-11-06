import json, urllib.request, urllib.parse, zipfile, io
UA={'User-Agent':'SuperLoader-compat/1.0'}
def get(u):
    r=urllib.request.Request(u,headers=UA)
    return json.load(urllib.request.urlopen(r,timeout=40))
res=get('https://api.modrinth.com/v2/search?query=jackfredlib&limit=5')
for h in res['hits']:
    print(h['slug'], '|', h['title'], '|', h['downloads'])
