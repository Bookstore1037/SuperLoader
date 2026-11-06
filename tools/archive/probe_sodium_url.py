import json,urllib.request
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SuperLoader-planning/1.0'})
    return json.load(urllib.request.urlopen(req,timeout=30))
data=get('https://api.modrinth.com/v2/project/sodium/version')
for v in data:
    if v['version_number']=='mc1.21.1-0.8.13-neoforge':
        for f in v['files']:
            print('URL',f['url'])
            print('SHA1',f['hashes']['sha1'])
            print('SIZE',f['size'])
