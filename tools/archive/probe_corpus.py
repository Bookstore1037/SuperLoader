import json, urllib.request, urllib.parse, time, pathlib

UA = {'User-Agent': 'SuperLoader-compat-plan/1.0'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

facets = json.dumps([["project_type:mod"], ["categories:fabric"], ["versions:1.21.1"]])
url = ('https://api.modrinth.com/v2/search?limit=100&index=downloads&facets='
       + urllib.parse.quote(facets, safe=''))
res = get(url)
hits = res['hits']
print('top fabric 1.21.1 mods:', len(hits), 'total_hits:', res.get('total_hits'))

rows = []
for h in hits:
    slug = h['slug']
    try:
        vs = get(f'https://api.modrinth.com/v2/project/{slug}/version?game_versions=%5B%221.21.1%22%5D')
    except Exception as e:
        rows.append({'slug': slug, 'title': h['title'], 'downloads': h['downloads'], 'err': str(e)})
        continue
    loaders = set()
    fab = None
    neo = None
    for v in vs:
        loaders.update(v['loaders'])
        if 'fabric' in v['loaders'] and fab is None:
            fab = v
        if 'neoforge' in v['loaders'] and neo is None:
            neo = v
    rows.append({
        'slug': slug, 'title': h['title'], 'downloads': h['downloads'],
        'loaders': sorted(loaders), 'has_fabric': fab is not None, 'has_neoforge': neo is not None,
        'fabric_version': (fab or {}).get('version_number'),
        'neoforge_version': (neo or {}).get('version_number'),
        'categories': h.get('categories'),
    })
    time.sleep(0.15)

pathlib.Path('logs').mkdir(exist_ok=True)
pathlib.Path('logs/compat_corpus_probe.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), 'utf-8')

fab_only = [r for r in rows if r.get('has_fabric') and not r.get('has_neoforge')]
both = [r for r in rows if r.get('has_fabric') and r.get('has_neoforge')]
neo_only = [r for r in rows if r.get('has_neoforge') and not r.get('has_fabric')]
errs = [r for r in rows if r.get('err')]
print(f'fabric_only={len(fab_only)} both={len(both)} neoforge_only={len(neo_only)} err={len(errs)}')
print('--- top fabric-only (candidate benchmark corpus) ---')
for r in fab_only[:25]:
    print(f"{r['downloads']:>10}  {r['slug']:<28} {r['fabric_version']}")
print('--- both (native available; NOT the main line) ---')
for r in both[:15]:
    print(f"{r['downloads']:>10}  {r['slug']:<28} fab={r['fabric_version']} neo={r['neoforge_version']}")
