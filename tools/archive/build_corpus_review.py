import json, urllib.request, urllib.parse, time, pathlib, sys

UA = {'User-Agent': 'SuperLoader-compat-plan/1.0'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

p = pathlib.Path('logs/compat_corpus_600.json')
for _ in range(60):
    if p.exists():
        break
    time.sleep(5)
rows = json.loads(p.read_text('utf-8'))
fab = [r for r in rows if r.get('has_fabric') and not r.get('has_neoforge')]
print('fabric_only total:', len(fab))

API_LIB = {
 'fabric-api','fabric-language-kotlin','placeholder-api','malilib','cicada','cardinal-components-api',
 'ukulib','bclib','yosbr','mixintrace','vmp-fabric','smooth-scroll','kaleido-config','forge-config-api-port',
 'puzzles-lib','owo-lib','libgui','fabric-permissions-api','trinkets' ,
}
L3 = {
 'indium','c2me-fabric','ebe','animatica','skyboxify','flashback','threadtweak','bobby','axiom',
 'cit-resewn','particular','eating-animation','capes','gamma-utils','iris','sodium-extra','lambdabettergrass',
}
TYPE_HINT = {
 'optimization': '优化', 'utility': '工具', 'decoration': '装饰', 'adventure': '玩法',
 'equipment': '装备', 'worldgen': '世界生成', 'mobs': '生物', 'food': '食物',
 'management': '管理', 'storage': '存储', 'cursed': '趣味', 'library': '库',
 'game-mechanics': '机制', 'technology': '科技', 'magic': '魔法', 'minigame': '小游戏',
 'social': '社交', 'transportation': '交通', 'building': '建筑',
}
CHECK = {
 'zoomify': '按 C 缩放（含平滑过渡）',
 'krypton': '无感；进世界后网络包正常（无断连）',
 'litematica': '打开 Litematica 菜单（M），加载一次放置预览',
 'debugify': 'F3 调试屏出现 debugify 补充项；配置菜单可开',
 'optigui': '装一个 CIT 资源包后容器界面贴图替换生效',
 'visuality': '进世界看区块加载粒子/方块破坏粒子',
 'fallingleaves': '进森林看树叶飘落粒子',
 'presence-footsteps': '走路/跳跃有脚步声（需资源包）',
 'morechathistory': '聊天栏上滚超过 100 条',
 'language-reload': 'F3+T 重载资源包后语言仍正常',
 'fabrishot': 'F9 截图并保存',
 'replaymod': '打开回放菜单，开始录制',
 'main-menu-credits': '主菜单右下角出现滚动字幕',
 'paginatedadvancements': '打开进度界面，翻页正常',
 'tooltipfix': '长 tooltip 不超出屏幕',
 'better-mount-hud': '骑马/坐船时 HUD 正常',
 'fastquit': '关闭游戏立即退出（无卡顿）',
 'trinkets': '打开饰品栏（默认快捷键）并装备一件',
 'carpet': '输入 /carpet 命令能响应',
 'farmers-delight-refabricated': '种植/烹饪一件食物',
 'betterend': '创建/进入 BetterEnd 群系（或看创造物品栏）',
 'betternether': '进入下界看 Nether 群系',
 'repurposed-structures-fabric': '新世界生成后结构出现',
 'friends-and-foes': '创造物品栏出现新生物蛋',
 'sophisticated-core-unofficial-fabric-port': '打开背包升级界面',
 'sophisticated-backpacks-unoffical-fabric-port': '合成背包并打开',
 'beautify-refabricated': '放置装饰方块',
 'better-ping-display-fabric': '多人界面 ping 显示（可离线看 GUI）',
 'smooth-scroll': '列表滚动平滑（默认）',
}

cand = []
for r in fab:
    s = r['slug']
    if s in API_LIB: cls = 'api_lib'
    elif s in L3: cls = 'l3_boundary'
    else: cls = 'candidate'
    cand.append({**r, 'class': cls})

cands = [c for c in cand if c['class'] == 'candidate']
print('candidates:', len(cands))

# fetch required deps for the first 50 candidates
proj_ids = {}
need = []
for c in cands[:50]:
    try:
        vs = get('https://api.modrinth.com/v2/project/%s/version?game_versions=%%5B%%221.21.1%%22%%5D&loaders=%%5B%%22fabric%%22%%5D' % c['slug'])
    except Exception as e:
        c['deps_error'] = str(e); continue
    if not vs:
        c['deps'] = None; continue
    v = vs[0]
    c['file'] = (v.get('files') or [{}])[0].get('filename')
    c['url'] = (v.get('files') or [{}])[0].get('url')
    deps = [d for d in v.get('dependencies', []) if d.get('dependency_type') == 'required']
    c['dep_ids'] = [d['project_id'] for d in deps if d.get('project_id')]
    for pid in c['dep_ids']:
        need.append(pid)
    time.sleep(0.1)

need = sorted(set(need))
names = {}
for i in range(0, len(need), 100):
    chunk = need[i:i+100]
    url = 'https://api.modrinth.com/v2/projects?ids=' + urllib.parse.quote(json.dumps(chunk), safe='')
    for pr in get(url):
        names[pr['id']] = pr['slug']

for c in cands[:50]:
    deps = [names.get(pid, pid) for pid in c.get('dep_ids', [])]
    c['deps'] = [d for d in deps if d not in ('fabric-api',)]

out = []
for c in cands:
    cats = c.get('categories') or []
    t = next((TYPE_HINT[x] for x in cats if x in TYPE_HINT), (cats[0] if cats else ''))
    out.append({'slug': c['slug'], 'title': c['title'], 'downloads': c['downloads'],
                'version': c.get('fabric_version'), 'file': c.get('file'), 'url': c.get('url'),
                'type': t, 'deps': c.get('deps', []), 'check': CHECK.get(c['slug'], '进世界 + 触发主功能'),
                'class': c['class']})

pathlib.Path('compat').mkdir(exist_ok=True)
pathlib.Path('compat/corpus_review.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf-8')

lines = ['# SuperLoader 兼容样本集 v1（待审）', '',
         '口径：MC 1.21.1、只有 Fabric 构建（Modrinth 前 600 个 Fabric mod 筛选）、排除 API/运行时库与 L3 渲染重写；',
         '按下载量排序。主指标只算 `candidate`。', '',
         '| # | mod | 下载量 | 版本 | 类型 | 必需前置 | 抽查项 |', '| --- | --- | ---: | --- | --- | --- | --- |']
i = 0
for c in out:
    if c['class'] != 'candidate':
        continue
    i += 1
    deps = ', '.join(c['deps']) if c['deps'] else '—'
    lines.append(f"| {i} | `{c['slug']}` | {c['downloads']:,} | {c['version']} | {c['type']} | {deps} | {c['check']} |")
lines += ['', '## 排除项', '', '- API/库：' + ', '.join(sorted(x['slug'] for x in out if x['class'] == 'api_lib'))]
lines += ['- L3 边界（不做，仅记录）：' + ', '.join(sorted(x['slug'] for x in out if x['class'] == 'l3_boundary'))]
pathlib.Path('compat/corpus_review.md').write_text('\n'.join(lines) + '\n', 'utf-8')
print('candidates written:', i)
