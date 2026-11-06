import json, urllib.request, urllib.parse, time, pathlib

UA = {'User-Agent': 'SuperLoader-compat/1.0'}
CACHE = pathlib.Path('.cache/compat/probe_cache.json')
cache = json.loads(CACHE.read_text('utf-8')) if CACHE.exists() else {}


def get(url):
    if url in cache:
        return cache[url]
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.load(r)
            cache[url] = data
            time.sleep(0.2)
            return data
        except Exception:
            if i == 2:
                raise
            time.sleep(1.5)


GV = urllib.parse.quote(json.dumps(['1.21.1']))


def versions(pid_or_slug):
    return get('https://api.modrinth.com/v2/project/%s/version?game_versions=%s' % (pid_or_slug, GV))


print('=== C1: fastquit / tooltipfix —— 1.21.1 上所有 Fabric 版本')
for slug in ('fastquit', 'tooltipfix'):
    vs = versions(slug)
    print(slug, 'count=', len(vs))
    for v in vs[:5]:
        print('   ', v['version_number'], v['loaders'], v['date_published'][:10], v['files'][0]['filename'])

print()
print('=== B3: L3 排除名单 —— 是否有 NeoForge 1.21.1 构建')
l3 = ['vulkanmod', 'exordium', 'nvidium', 'cull-less-leaves', 'indium', 'c2me-fabric', 'ebe',
      'animatica', 'skyboxify', 'flashback', 'threadtweak', 'bobby', 'axiom', 'cit-resewn',
      'particular', 'eating-animation', 'capes', 'gamma-utils', 'sodium-extra', 'iris', 'sodium',
      'distancetransform']
out = {}
for slug in l3:
    try:
        vs = versions(slug)
    except Exception as e:
        print(slug, 'ERR', e)
        continue
    nf = [v for v in vs if 'neoforge' in v['loaders']]
    fab = [v for v in vs if 'fabric' in v['loaders']]
    out[slug] = {'total': len(vs), 'nf': len(nf), 'fabric': len(fab),
                 'nf_latest': (sorted(nf, key=lambda v: v['date_published'])[-1]['version_number'] if nf else None),
                 'nf_date': (sorted(nf, key=lambda v: v['date_published'])[-1]['date_published'][:10] if nf else None)}
    print('%-20s total=%-3d fabric=%-3d neoforge=%-3d latest_nf=%s %s' % (
        slug, len(vs), len(fab), len(nf), out[slug]['nf_latest'] or '—', out[slug]['nf_date'] or ''))

print()
print('=== A3/C3 候选: 纯后台可 auto 的 fabric-only mod')
for slug in ('dynamic-fps', 'noisium', 'memoryleakfix', 'badoptimizations', 'fastload',
             'clumps', 'ferrite-core', 'krypton', 'debugify'):
    try:
        vs = versions(slug)
    except Exception as e:
        print(slug, 'ERR', e)
        continue
    v = sorted(vs, key=lambda v: v['date_published'])[-1] if vs else None
    if not v:
        print(slug, 'no 1.21.1 version')
        continue
    print('%-16s %-28s loaders=%-18s %s' % (slug, v['version_number'], ','.join(v['loaders']), v['date_published'][:10]))

CACHE.write_text(json.dumps(cache, ensure_ascii=False), 'utf-8')
pathlib.Path('logs/l3_nf_status.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf-8')
