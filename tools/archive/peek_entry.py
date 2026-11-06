import json
d=json.load(open('compat/deps_closure.json',encoding='utf-8'))
r=[x for x in d['main'] if x['slug']=='zoomify'][0]
print('keys:', list(r))
print(json.dumps(r['entries'][:6], ensure_ascii=False, indent=1))
print('install[0]:', json.dumps(r['install'][0], ensure_ascii=False))
