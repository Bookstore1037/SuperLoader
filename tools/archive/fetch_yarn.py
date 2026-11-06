import hashlib, pathlib, urllib.request, zipfile, io, re

cache = pathlib.Path(r'D:\SuperLoader\.cache\compat\mappings')
cache.mkdir(parents=True, exist_ok=True)
ver = '1.21.1+build.3'
for kind in ('v2', 'v1'):
    name = f'yarn-{ver}-{kind}.jar'
    p = cache / name
    if not p.exists():
        url = f'https://maven.fabricmc.net/net/fabricmc/yarn/{ver}/{name}'
        print('downloading', url)
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        p.write_bytes(data)
    sha1 = hashlib.sha1(p.read_bytes()).hexdigest()
    print(kind, 'size', p.stat().st_size, 'sha1', sha1)

    with zipfile.ZipFile(p) as zf:
        tiny = zf.read('mappings/mappings.tiny')
    lines = tiny.decode('utf-8').splitlines()
    print(kind, 'header:', lines[0])
    print(kind, 'lines:', len(lines))
    hits = [l for l in lines if 'getNeighboringEntry' in l]
    print(kind, 'getNeighboringEntry lines:', hits[:3])
