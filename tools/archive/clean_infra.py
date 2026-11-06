import json, pathlib
for p in ('compat/corpus.json','compat/deps_closure.json'):
    d=json.loads(pathlib.Path(p).read_text('utf-8'))
    for r in d.get('infra',[]):
        for k in ('verdict_mode','manual_check','auto_assert','expected','expected_layer','scope'):
            r.pop(k,None)
    pathlib.Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=1),'utf-8')
c=json.loads(pathlib.Path('compat/corpus.json').read_text('utf-8'))
print('notes:', json.dumps(c.get('notes'), ensure_ascii=False)[:600])
