import json, urllib.request
UA={'User-Agent':'SuperLoader/1.0'}
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40))
for slug in ('fastquit','tooltipfix','carpet','held-item-info','replaymod'):
    vs = get(f'https://api.modrinth.com/v2/project/{slug}/version?game_versions=%5B%221.21.1%22%5D')
    v = vs[0]
    print(slug, '|', v['version_number'], '|', v['game_versions'], '|', v['loaders'], '|', v['date_published'][:10], '|', v['files'][0]['filename'])
