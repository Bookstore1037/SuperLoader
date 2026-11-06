import zipfile, io, re, glob, json, pathlib
jar = glob.glob(r'D:\SLData\instances\1.21.1\mods\forgified-fabric-api-*.jar')[0]
print('ffapi jar:', pathlib.Path(jar).name)
mods = []
with zipfile.ZipFile(jar) as z:
    for n in z.namelist():
        if n.startswith('META-INF/jars/') and n.endswith('.jar'):
            with zipfile.ZipFile(io.BytesIO(z.read(n))) as inner:
                try:
                    toml = inner.read('META-INF/neoforge.mods.toml').decode('utf-8', 'replace')
                except KeyError:
                    continue
                mid = re.search(r'modId\s*=\s*"([^"]+)"', toml)
                prov = re.search(r'provides\s*=\s*\[([^\]]*)\]', toml)
                mods.append({'jar': n.split('/')[-1], 'modId': mid.group(1) if mid else None,
                             'provides': re.findall(r'"([^"]+)"', prov.group(1)) if prov else []})
print('modules:', len(mods))
print(json.dumps(mods[:3], ensure_ascii=False, indent=1))
ids = {m['modId'] for m in mods} | {p for m in mods for p in m['provides']}
print('total ids+provides:', len(ids))
print('sample:', sorted(ids)[:20])
pathlib.Path('logs/ffapi_modules.json').write_text(json.dumps(mods, ensure_ascii=False, indent=1), 'utf-8')
