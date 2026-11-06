import json, urllib.request, urllib.parse, time
UA={'User-Agent':'SuperLoader-compat/1.0'}
CACHE='.cache/compat/probe_cache.json'
import pathlib
p=pathlib.Path(CACHE); cache=json.loads(p.read_text('utf-8')) if p.exists() else {}
def get(u):
    if u in cache: return cache[u]
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40) as r:
                d=json.load(r); cache[u]=d; time.sleep(0.2); return d
        except Exception:
            if i==2: raise
            time.sleep(1.5)
GV=urllib.parse.quote(json.dumps(['1.21.1']))
for slug in ('ferrite-core','clumps','badoptimizations','memoryleakfix','connectivity','packet-fix','netherportalfix','smoothboot','fastload','dynamic-fps','noisium'):
    try:
        vs=get('https://api.modrinth.com/v2/project/%s/version?game_versions=%s'%(slug,GV))
    except Exception as e:
        print(slug,'ERR',e); continue
    lab=[(v['version_number'],','.join(v['loaders']),v['date_published'][:10]) for v in sorted(vs,key=lambda v:v['date_published'])[-3:]]
    print('%-18s n=%-3d %s'%(slug,len(vs),lab))
p.write_text(json.dumps(cache,ensure_ascii=False),'utf-8')
