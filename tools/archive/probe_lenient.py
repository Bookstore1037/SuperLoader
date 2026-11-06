import json, zipfile, pathlib
c = json.load(open('.cache/compat/deps_cache.json', encoding='utf-8'))
e = c.get('lenient-death')
print(e['file'], e['version'], e['slug'])
p = pathlib.Path('.cache/compat/jars') / e['file']
z = zipfile.ZipFile(p)
print([n for n in z.namelist() if n.startswith('META-INF/jars')][:10])
fmj = json.loads(z.read('fabric.mod.json').decode('utf-8','replace'), strict=False)
print('id', fmj.get('id'), 'depends', fmj.get('depends'))
print('provides?', fmj.get('provides'))
print('jars', [j.get('file') for j in fmj.get('jars', [])])
