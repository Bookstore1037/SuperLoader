import json, urllib.request, urllib.error
UA={'User-Agent':'SuperLoader-compat/1.0'}
def get(u):
    r=urllib.request.Request(u,headers=UA)
    try:
        with urllib.request.urlopen(r,timeout=30) as f: return json.load(f)
    except urllib.error.HTTPError as e:
        return {'_err': e.code}
for slug in ('distancetransform','distance-transform','sophisticated-core-unofficial-fabric-port','beautify-refabricated','repurposed-structures-fabric','better-ping-display-fabric','the-bumblezone-fabric','farmers-delight-refabricated','cave-dust','wakes'):
    d=get('https://api.modrinth.com/v2/project/'+slug)
    if '_err' in d:
        print(slug,'-> HTTP',d['_err']); continue
    print(slug,'|',d.get('title'),'| 1.21.1:', '1.21.1' in (d.get('game_versions') or []), '| src:', d.get('source_url'))
