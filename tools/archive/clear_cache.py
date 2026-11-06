import json
p='.cache/compat/deps_cache.json'
c=json.load(open(p,encoding='utf-8'))
c.pop('forgeconfigapiport',None)
json.dump(c,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('cleared')
