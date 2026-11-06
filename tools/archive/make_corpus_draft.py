import json, pathlib

rows = json.loads(pathlib.Path('logs/compat_corpus_300.json').read_text('utf-8'))
fab = [r for r in rows if r.get('has_fabric') and not r.get('has_neoforge')]

API_LIB = {
 'fabric-api','fabric-language-kotlin','placeholder-api','malilib','cicada','cardinal-components-api',
 'ukulib','bclib','yosbr','mixintrace','vmp-fabric','smooth-scroll',
}
L3 = {
 'indium','c2me-fabric','ebe','animatica','skyboxify','flashback','threadtweak','bobby','axiom',
 'cit-resewn','particular','eating-animation','capes','gamma-utils',
}

draft = []
for r in fab:
    if r['slug'] in API_LIB: cls = 'api_lib'
    elif r['slug'] in L3: cls = 'l3_boundary'
    else: cls = 'candidate'
    draft.append({'slug': r['slug'], 'title': r['title'], 'downloads': r['downloads'],
                  'fabric_version': r['fabric_version'], 'class': cls})

pathlib.Path('compat').mkdir(exist_ok=True)
out = pathlib.Path('compat/corpus_draft.json')
out.write_text(json.dumps(draft, ensure_ascii=False, indent=1), 'utf-8')

from collections import Counter
c = Counter(d['class'] for d in draft)
print('fabric_only total:', len(draft), dict(c))
print('--- candidates ---')
for d in draft:
    if d['class'] == 'candidate':
        print(f"{d['downloads']:>9}  {d['slug']:<34} {d['fabric_version']}")
