"""A2/A3b: backfill version_id + sha1 + loaders on every jar, and nf_build evidence.

Reads compat/deps_closure.json, resolves each install jar's Modrinth version id
straight from its CDN url (/data/<project>/versions/<version>/<file>), then writes
back version_id / sha1 / loaders / game_versions.  Also records, per sample,
whether the project ships a NeoForge build for 1.21.1 (with the evidence string).

Caches: .cache/compat/versions_cache.json, .cache/compat/proj_versions_cache.json
Usage: python tools/enrich_meta.py [--refresh]
"""
import json, re, pathlib, sys, time, urllib.request, urllib.parse

ROOT = pathlib.Path('.')
DEP = ROOT / 'compat' / 'deps_closure.json'
CACHE = ROOT / '.cache' / 'compat'
VCACHE = CACHE / 'versions_cache.json'
PCACHE = CACHE / 'proj_versions_cache.json'
UA = {'User-Agent': 'SuperLoader-compat/1.0 (meta)'}
GV = ['1.21.1']
REFRESH = '--refresh' in sys.argv

URL_RE = re.compile(r'/data/([A-Za-z0-9]+)/versions/([A-Za-z0-9]+)/([^/?]+)')


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def load(path, default):
    if path.exists() and not REFRESH:
        return json.loads(path.read_text('utf-8'))
    return default


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), 'utf-8')


def version_info(vid, cache):
    if vid in cache and not REFRESH:
        return cache[vid]
    v = get('https://api.modrinth.com/v2/version/%s' % vid)
    f = v['files'][0]
    info = {
        'version_id': vid,
        'version_number': v['version_number'],
        'sha1': f['hashes']['sha1'],
        'file': f['filename'],
        'url': f['url'],
        'size': f['size'],
        'loaders': v['loaders'],
        'game_versions': v['game_versions'],
        'date_published': v['date_published'][:10],
        'project_id': v['project_id'],
    }
    cache[vid] = info
    time.sleep(0.15)
    return info


def project_versions(pid, cache):
    if pid in cache and not REFRESH:
        return cache[pid]
    q = urllib.parse.quote(json.dumps(GV))
    vs = get('https://api.modrinth.com/v2/project/%s/version?game_versions=%s' % (pid, q))
    cache[pid] = vs
    time.sleep(0.2)
    return vs


PCACHE_SLUG = CACHE / 'proj_id_cache.json'
_pid_cache = load(PCACHE_SLUG, {})


def project_id(slug):
    if slug in _pid_cache and not REFRESH:
        return _pid_cache[slug]
    try:
        p = get('https://api.modrinth.com/v2/project/%s' % slug)
    except Exception:
        return None
    _pid_cache[slug] = p['id']
    return p['id']


def by_filename(slug, filename, pvcache):
    """Fallback for CDN urls that embed version_number instead of version id."""
    pid = project_id(slug)
    if not pid:
        return None
    for v in project_versions(pid, pvcache):
        for f in v['files']:
            if f['filename'] == filename:
                return {
                    'version_id': v['id'], 'version_number': v['version_number'],
                    'sha1': f['hashes']['sha1'], 'file': f['filename'], 'url': f['url'],
                    'size': f['size'], 'loaders': v['loaders'],
                    'game_versions': v['game_versions'],
                    'date_published': v['date_published'][:10], 'project_id': pid,
                }
    return None


def loader_label(loaders):
    has_f = 'fabric' in loaders
    has_n = 'neoforge' in loaders
    if has_f and has_n:
        return 'both'
    if has_n:
        return 'neoforge'
    return 'fabric'


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    d = json.loads(DEP.read_text('utf-8'))
    vcache = load(VCACHE, {})
    pcache = load(PCACHE, {})

    groups = [g for g in ('main', 'infra', 'content_phase2') if g in d]
    n_jar = 0
    for g in groups:
        for r in d[g]:
            # sample itself
            m = URL_RE.search(r.get('url', ''))
            info = version_info(m.group(2), vcache) if m else by_filename(r['slug'], r.get('file'), pcache)
            if info:
                r['version_id'] = info['version_id']
                r['sha1'] = info['sha1']
                r['file_size'] = info['size']
                r['game_versions'] = info['game_versions']
                r['loader'] = loader_label(info['loaders'])
                r['project_id'] = info['project_id']
                n_jar += 1
            # install set
            for it in r.get('install', []):
                m = URL_RE.search(it.get('url', ''))
                info = version_info(m.group(2), vcache) if m else by_filename(
                    it.get('id') or r['slug'], it.get('file'), pcache)
                if not info:
                    continue
                it['version_id'] = info['version_id']
                it['sha1'] = info['sha1']
                it['file_size'] = info['size']
                it['game_versions'] = info['game_versions']
                it['loader'] = loader_label(info['loaders'])
                it['project_id'] = info['project_id']
                n_jar += 1
            # nf_build evidence
            pid = r.get('project_id')
            if pid:
                vs = project_versions(pid, pcache)
                nf = [v for v in vs if 'neoforge' in v['loaders']]
                if nf:
                    best = sorted(nf, key=lambda v: v['date_published'])[-1]
                    r['nf_build'] = 'yes'
                    r['nf_evidence'] = '%s %s (%s, loaders=%s)' % (
                        r['slug'], best['version_number'], best['date_published'][:10],
                        ','.join(best['loaders']))
                else:
                    r['nf_build'] = 'no'
                    r['nf_evidence'] = '%s: 1.21.1 共 %d 个版本，无一含 neoforge loader（实测 loader=%s）' % (
                        r['slug'], len(vs), r.get('loader'))
    save(DEP, d)
    save(VCACHE, vcache)
    save(PCACHE, pcache)
    save(PCACHE_SLUG, _pid_cache)
    print('jars annotated:', n_jar, 'version cache:', len(vcache), 'projects:', len(pcache))
    for g in groups:
        for r in d[g]:
            print('%-6s %-32s nf=%-3s loader=%-8s %s' % (
                g[:6], r['slug'], r.get('nf_build'), r.get('loader'), r.get('version_id')))


if __name__ == '__main__':
    main()
