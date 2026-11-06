import json, urllib.request, urllib.parse, time, pathlib

UA = {'User-Agent': 'SuperLoader-compat-plan/1.0'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

base = json.loads(pathlib.Path('logs/compat_corpus_300.json').read_text('utf-8'))
seen = {r['slug'] for r in base}
facets = json.dumps([["project_type:mod"], ["categories:fabric"], ["versions:1.21.1"]])
new_hits = []
for offset in (300, 400, 500):
    url = ('https://api.modrinth.com/v2/search?limit=100&offset=%d&index=downloads&facets='
           % offset + urllib.parse.quote(facets, safe=''))
    new_hits += get(url)['hits']
    time.sleep(0.3)
print('extra projects:', len(new_hits), flush=True)

rows = []
for i, h in enumerate(new_hits):
    slug = h['slug']
    if slug in seen:
        continue
    try:
        vs = get(f'https://api.modrinth.com/v2/project/{slug}/version?game_versions=%5B%221.21.1%22%5D')
    except Exception as e:
        rows.append({'slug': slug, 'title': h['title'], 'downloads': h['downloads'], 'err': str(e)})
        continue
    has_f = any('fabric' in v['loaders'] for v in vs)
    has_n = any('neoforge' in v['loaders'] for v in vs)
    fab = next((v for v in vs if 'fabric' in v['loaders']), None)
    rows.append({'slug': slug, 'title': h['title'], 'downloads': h['downloads'],
                 'has_fabric': has_f, 'has_neoforge': has_n,
                 'fabric_version': (fab or {}).get('version_number'), 'categories': h.get('categories')})
    if i % 25 == 0:
        print('progress', i, len(rows), flush=True)
    time.sleep(0.1)

allrows = base + rows
pathlib.Path('logs/compat_corpus_600.json').write_text(json.dumps(allrows, ensure_ascii=False, indent=1), 'utf-8')
fab_only = [r for r in allrows if r.get('has_fabric') and not r.get('has_neoforge')]
print('total=%d fabric_only=%d' % (len(allrows), len(fab_only)), flush=True)
