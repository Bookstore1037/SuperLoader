import json, zipfile, pathlib
J=pathlib.Path('.cache/compat/jars')
for fn in ('[SECRET] fastquit','tooltipfix'):
    pass
cands=[p for p in J.iterdir() if p.name.lower().startswith(('fastquit','tooltipfix'))]
for p in cands:
    with zipfile.ZipFile(p) as z:
        fmj=json.loads(z.read('fabric.mod.json').decode('utf-8','replace'), strict=False)
    print(p.name, '| id=', fmj.get('id'), '| ver=', fmj.get('version'))
    print('  depends=', json.dumps(fmj.get('depends'), ensure_ascii=False))
    print('  breaks=', json.dumps(fmj.get('breaks'), ensure_ascii=False))
    print('  custom=', json.dumps(fmj.get('custom'), ensure_ascii=False)[:200])
