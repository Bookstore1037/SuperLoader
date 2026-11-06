import json, urllib.request, urllib.parse, time, pathlib

UA = {'User-Agent': 'SuperLoader-compat-plan/1.0'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

facets = json.dumps([["project_type:mod"], ["categories:fabric"], ["versions:1.21.1"]])
hits = []
for offset in (0, 100, 200):
    url = ('https://api.modrinth.com/v2/search?limit=100&offset=%d&index=downloads&facets='
           % offset + urllib.parse.quote(facets, safe=''))
    hits += get(url)['hits']
    time.sleep(0.3)
print('projects:', len(hits))

rows = []
for h in hits:
    slug = h['slug']
    try:
        vs = get(f'https://api.modrinth.com/v2/project/{slug}/version?game_versions=%5B%221.21.1%22%5D')
    except Exception as e:
        rows.append({'slug': slug, 'title': h['title'], 'downloads': h['downloads'], 'err': str(e)})
        continue
    has_f = any('fabric' in v['loaders'] for v in vs)
    has_n = any('neoforge' in v['loaders'] for v in vs)
    fab = next((v for v in vs if 'fabric' in v['loaders']), None)
    rows.append({
        'slug': slug, 'title': h['title'], 'downloads': h['downloads'],
        'has_fabric': has_f, 'has_neoforge': has_n,
        'fabric_version': (fab or {}).get('version_number'),
        'categories': h.get('categories'),
    })
    time.sleep(0.12)

pathlib.Path('logs/compat_corpus_300.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), 'utf-8')
fab_only = [r for r in rows if r.get('has_fabric') and not r.get('has_neoforge')]
print('fabric_only=%d both=%d' % (len(fab_only), sum(1 for r in rows if r.get('has_fabric') and r.get('has_neoforge'))))
for r in fab_only[:60]:
    print(f"{r['downloads']:>10}  {r['slug']:<30} {r['fabric_version']}")
