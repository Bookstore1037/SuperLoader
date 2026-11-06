import json, io, re, zipfile, urllib.request, urllib.parse, pathlib, sys, time

UA = {'User-Agent': 'SuperLoader-compat-deps/1.0'}
CACHE = pathlib.Path('.cache/compat'); JARS = CACHE / 'jars'
CACHE.mkdir(parents=True, exist_ok=True); JARS.mkdir(parents=True, exist_ok=True)

def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

def download(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    req = urllib.request.Request(url, headers=UA)
    tmp = dest.with_suffix(dest.suffix + '.part')
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, 'wb') as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk: break
            f.write(chunk)
    tmp.replace(dest)
    return dest

# ---- version predicate (Fabric-ish) ----
def vtuple(v):
    v = v.split('+')[0]
    parts = re.split(r'[.\-]', v)
    out = []
    for p in parts:
        m = re.match(r'^(\d+)', p)
        if m: out.append(int(m.group(1)))
        elif p in ('x', 'X', '*'): out.append(None)
        else: break
    return out

def vcmp(a, b):
    ta, tb = vtuple(a), vtuple(b)
    n = max(len(ta), len(tb))
    ta += [0] * (n - len(ta)); tb += [0] * (n - len(tb))
    for x, y in zip(ta, tb):
        if x is None or y is None: return 0
        if x != y: return -1 if x < y else 1
    return 0

def match_one(ver, pred):
    pred = pred.strip()
    if pred in ('*', ''): return True
    if pred.startswith('>='): return vcmp(ver, pred[2:]) >= 0
    if pred.startswith('<='): return vcmp(ver, pred[2:]) <= 0
    if pred.startswith('>'): return vcmp(ver, pred[1:]) > 0
    if pred.startswith('<'): return vcmp(ver, pred[1:]) < 0
    if pred.startswith('='): return vcmp(ver, pred[1:]) == 0
    if pred.startswith('^'):
        base = pred[1:]; t = vtuple(base)
        if vcmp(ver, base) < 0: return False
        return vtuple(ver)[0] == t[0]
    if pred.startswith('~'):
        base = pred[1:]; t = vtuple(base)
        if vcmp(ver, base) < 0: return False
        return vtuple(ver)[:2] == t[:2]
    if 'x' in pred.lower() or '*' in pred:
        t = vtuple(pred); vt = vtuple(ver)
        return all(p is None or p == q for p, q in zip(t, vt))
    return vcmp(ver, pred) == 0

def match_range(ver, spec):
    if not spec: return True
    spec = spec.strip()
    if spec in ('*',): return True
    if '||' in spec:
        return any(match_range(ver, s) for s in spec.split('||'))
    return all(match_one(ver, p) for p in spec.split())

# ---- ffapi ----
ff = json.loads(pathlib.Path('logs/ffapi_modules.json').read_text('utf-8'))
FFAPI = {}
for m in ff:
    ver = m['jar'].split('-')[0]
    pass
# version per module parsed from inner jar name: fabric-<module>-<version>+<hash>.jar
for m in ff:
    name = m['jar'][:-4]
    ids = ([m['modId']] if m['modId'] else []) + m['provides']
    for i in ids:
        FFAPI[i] = name

def ffapi_version(mid):
    name = FFAPI.get(mid)
    if not name: return None
    # fabric-screen-api-v1-2.0.26+9991ca2f19
    idx = name.rfind('-')
    return name[idx+1:]

BUILTIN = {'minecraft': '1.21.1', 'java': '25', 'fabricloader': '2.5.68',
           'fabric': '2.5.68', 'fabric-loader': '2.5.68'}

# mod id -> Modrinth slug (ids that don't equal their slug)
ALIAS = {
    'yet_another_config_lib_v3': 'yacl',
    'cloth_config': 'cloth-config',
    'cloth-config2': 'cloth-config',
    'resourcefullib': 'resourceful-lib',
    'wover': 'worldweaver',
    'fabric-permissions-api-v0': 'fabric-permissions-api',
    'forgeconfigapiport': 'forge-config-api-port',
}

def read_fmj(path):
    with zipfile.ZipFile(path) as z:
        with z.open('fabric.mod.json') as f:
            return json.loads(f.read().decode('utf-8', 'replace'), strict=False)

def dep_specs(dep):
    out = {}
    for k, v in (dep or {}).items():
        if isinstance(v, str): out[k] = v
        elif isinstance(v, dict): out[k] = v.get('version') or '*'
    return out

def _norm(s):
    return re.sub(r'[-_]', '', s.lower())

def project_meta(slug):
    for cand in (ALIAS.get(slug), slug, slug.replace('_', '-'), slug.replace('-', '_')):
        if not cand:
            continue
        try:
            return get_json(f'https://api.modrinth.com/v2/project/{cand}')
        except Exception:
            continue
    # 最后按搜索兜底：slug 去掉 -/_ 后与 mod id 一致才算命中
    try:
        q = urllib.parse.quote(slug)
        facets = urllib.parse.quote('[["project_type:mod"]]', safe='')
        res = get_json(f'https://api.modrinth.com/v2/search?query={q}&limit=8&facets={facets}')
        for hit in res.get('hits', []):
            if _norm(hit['slug']) == _norm(slug):
                return get_json(f"https://api.modrinth.com/v2/project/{hit['slug']}")
    except Exception:
        pass
    return None

def pick_version(project_slug, prefer_native=False):
    try:
        vs = get_json(f'https://api.modrinth.com/v2/project/{project_slug}/version?game_versions=%5B%221.21.1%22%5D')
    except Exception:
        return None
    if prefer_native:
        for v in vs:
            if 'neoforge' in v['loaders']:
                return v, 'neoforge'
    for v in vs:
        if 'fabric' in v['loaders']:
            return v, 'fabric'
    return None

cache = json.loads((CACHE / 'deps_cache.json').read_text('utf-8')) if (CACHE / 'deps_cache.json').exists() else {}
# 丢弃上次遗留的“查不到”与“原生构建”缓存，避免旧结论污染
cache = {k: v for k, v in cache.items() if not v.get('missing') and v.get('loader') != 'neoforge'}
def save_cache():
    (CACHE / 'deps_cache.json').write_text(json.dumps(cache, ensure_ascii=False, indent=1), 'utf-8')

NATIVE_PREF = set()  # 依赖闭包一律按 Fabric 构建解析（有 fabric.mod.json）；原生版在安装阶段另行决定

def resolve_id(mid, spec, required_by, trace):
    """Return entry dict + list of children to resolve."""
    if mid in BUILTIN:
        ver = BUILTIN[mid]
        return {'id': mid, 'kind': 'builtin', 'version': ver, 'spec': spec,
                'ok': match_range(ver, spec)}, []
    if mid in FFAPI:
        ver = ffapi_version(mid)
        return {'id': mid, 'kind': 'ffapi', 'version': ver, 'spec': spec,
                'ok': match_range(ver, spec)}, []
    key = mid
    if key not in cache:
        m = project_meta(mid)
        if not m:
            alt = mid.replace('_', '-')
            if alt != mid: m = project_meta(alt)
        if not m:
            cache[key] = {'missing': True}
        else:
            slug = m['slug']
            pv = pick_version(slug, prefer_native=slug in NATIVE_PREF)
            if not pv:
                cache[key] = {'missing': True, 'slug': slug}
            else:
                v, loader = pv
                f = (v.get('files') or [{}])[0]
                cache[key] = {'slug': slug, 'title': m['title'], 'version': v['version_number'],
                              'loader': loader, 'file': f.get('filename'), 'url': f.get('url'),
                              'sha1': (f.get('hashes') or {}).get('sha1'),
                              'deps': dep_specs({d['project_id']: d.get('version_number') or '*'
                                                 for d in v.get('dependencies', [])
                                                 if d.get('dependency_type') == 'required'})}
        save_cache()
        time.sleep(0.1)
    c = cache[key]
    if c.get('missing'):
        return {'id': mid, 'kind': 'missing', 'spec': spec, 'ok': False}, []
    jar = JARS / c['file']
    try:
        fmj = read_fmj(download(c['url'], jar))
    except Exception as e:
        return {'id': mid, 'kind': 'error', 'spec': spec, 'ok': False, 'error': str(e)}, []
    children = [(cid, cs) for cid, cs in dep_specs(fmj.get('depends')).items()]
    # 版本号以 jar 内 fabric.mod.json 为准；Modrinth 的 version_number 常带前缀/后缀
    # （例：v21.1.6-1.21.1-Fabric），直接拿去做 semver 比较会误判为不满足。
    ver = fmj.get('version') or c['version']
    return {'id': mid, 'kind': c['loader'], 'version': ver, 'spec': spec,
            'ok': match_range(ver, spec), 'file': c['file'], 'url': c['url'],
            'modrinth_version': c['version'],
            'slug': c['slug'], 'real_id': fmj.get('id')}, children

def close(slug, want_loader='fabric'):
    c = cache.get(slug)
    if not c or c.get('missing'):
        m = project_meta(slug)
        if not m: return None
        pv = pick_version(slug, prefer_native=(slug in NATIVE_PREF))
        if not pv: return None
        v, loader = pv
        f = (v.get('files') or [{}])[0]
        c = {'slug': slug, 'title': m['title'], 'version': v['version_number'], 'loader': loader,
             'file': f.get('filename'), 'url': f.get('url'), 'sha1': (f.get('hashes') or {}).get('sha1'), 'deps': {}}
        cache[slug] = c; save_cache()
    jar = JARS / c['file']
    fmj = read_fmj(download(c['url'], jar))
    # jar-in-jar：内嵌 jar 自身满足的 mod id（Fabric loader 会自动挂载，Connector 侧需 remap）
    nested = {}
    try:
        with zipfile.ZipFile(jar) as z:
            for name in z.namelist():
                if not (name.startswith('META-INF/jars/') and name.endswith('.jar')):
                    continue
                try:
                    with zipfile.ZipFile(io.BytesIO(z.read(name))) as nz:
                        nf = json.loads(nz.read('fabric.mod.json').decode('utf-8', 'replace'), strict=False)
                except Exception:
                    continue
                for nid in [nf.get('id')] + list(nf.get('provides') or []):
                    if nid:
                        nested.setdefault(nid, nf.get('version'))
    except Exception:
        pass
    entries, issues = [], []
    seen = set()
    def walk(dep_id, spec, by):
        if dep_id in seen: return
        seen.add(dep_id)
        if dep_id == 'fabric-api' or dep_id == 'fabric_api':
            e, ch = {'id': dep_id, 'kind': 'ffapi-root', 'version': 'provided-by-forgified', 'spec': spec, 'ok': True}, []
        elif dep_id in FFAPI:
            fv = ffapi_version(dep_id)
            e, ch = {'id': dep_id, 'kind': 'ffapi', 'version': fv, 'spec': spec,
                     'ok': match_range(fv, spec)}, []
        elif dep_id in nested and nested[dep_id]:
            e, ch = {'id': dep_id, 'kind': 'jij', 'version': nested[dep_id], 'spec': spec,
                     'ok': match_range(nested[dep_id], spec)}, []
        else:
            e, ch = resolve_id(dep_id, spec, by, set())
        e['required_by'] = by
        entries.append(e)
        if not e.get('ok'):
            issues.append({'id': dep_id, 'spec': spec, 'required_by': by, 'kind': e.get('kind'), 'version': e.get('version')})
        for cid, cs in ch:
            walk(cid, cs, dep_id)
    roots = dep_specs(fmj.get('depends'))
    for did, spec in roots.items():
        walk(did, spec, fmj.get('id'))
    install = {c['slug']: {'id': fmj.get('id'), 'file': c['file'], 'url': c['url'], 'version': c['version']}}
    for e in entries:
        if e.get('kind') in ('fabric', 'neoforge') and e.get('file'):
            install[e.get('slug') or e['id']] = {'id': e['id'], 'file': e['file'], 'url': e['url'], 'version': e['version']}
    size = 0
    for it in install.values():
        p = JARS / it['file']
        if p.exists():
            size += p.stat().st_size
    return {'slug': slug, 'mod_id': fmj.get('id'), 'mod_version': fmj.get('version'),
            'environment': fmj.get('environment'), 'file': c['file'], 'url': c['url'], 'loader': c['loader'],
            'entries': entries, 'issues': issues,
            'install': list(install.values()), 'install_jars': len(install), 'install_bytes': size}

corpus = json.loads(pathlib.Path('compat/corpus.json').read_text('utf-8'))
report = {'main': [], 'infra': [], 'content_phase2': []}
for group in ('main', 'infra', 'content_phase2'):
    for it in corpus[group]:
        try:
            r = close(it['slug'])
        except Exception as e:
            r = {'slug': it['slug'], 'error': repr(e)}
        if not r:
            report[group].append({'slug': it['slug'], 'error': 'project not found'})
            continue
        r['group'] = group; r['check'] = it['check']
        r['check'] = it['check']
        for k in ('verdict_mode', 'expected', 'expected_layer', 'expected_reason',
                  'scope', 'auto_assert', 'manual_check'):
            if k in it:
                r[k] = it[k]
        r['ok'] = not r.get('issues') and not r.get('error')
        report[group].append(r)
        print(('OK  ' if r['ok'] else 'FAIL'), group, it['slug'],
              '%d deps, %d issues%s' % (len(r.get('entries', [])), len(r.get('issues', [])),
                                        (' err=' + r['error']) if r.get('error') else ''), flush=True)

pathlib.Path('compat/deps_closure.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), 'utf-8')
