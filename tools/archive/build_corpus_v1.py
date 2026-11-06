import json, urllib.request, urllib.parse, time, pathlib

UA = {'User-Agent': 'SuperLoader-compat-plan/1.0'}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

MAIN = [
 ('modmenu', '工具', '打开 Mods 列表，能看到全部 mod'),
 ('zoomify', '工具', '按 C 缩放（含平滑过渡）'),
 ('krypton', '优化', '无感；进世界后网络正常（无断连）'),
 ('language-reload', '优化', 'F3+T 重载资源包后语言/字体仍正常'),
 ('presence-footsteps', '装饰', '走路/跳跃有脚步声（需资源包）'),
 ('debugify', '优化', 'F3 调试屏出现 debugify 补充项；配置菜单可开'),
 ('visuality', '装饰', '区块加载/方块破坏粒子出现'),
 ('morechathistory', '社交', '聊天栏上滚超过 100 条'),
 ('litematica', '工具', 'M 打开 Litematica 菜单，加载一次放置预览'),
 ('fallingleaves', '装饰', '树林里树叶飘落粒子'),
 ('optigui', '装饰', '装 CIT 资源包后容器界面贴图替换生效'),
 ('better-mount-hud', '工具', '骑马/坐船时 HUD 正常'),
 ('fastquit', '优化', '关闭游戏立即退出（无卡顿）'),
 ('fabrishot', '工具', 'F9 截图并保存'),
 ('replaymod', '工具', '打开回放菜单，开始录制'),
 ('paginatedadvancements', '工具', '进度界面翻页正常'),
 ('main-menu-credits', '装饰', '主菜单右下角滚动字幕'),
 ('tooltipfix', '优化', '长 tooltip 不超出屏幕'),
 ('better-ping-display-fabric', '工具', '多人界面 ping 显示正常'),
 ('beautify-refabricated', '装饰', '放置一件装饰方块'),
 ('carpet', '机制', '/carpet 命令有响应'),
 ('no-resource-pack-warnings', '工具', '无资源包警告弹窗'),
 ('stendhal', '工具', '书与笔界面出现新功能'),
 ('forcecloseworldloadingscreen', '工具', '加载世界时关闭界面不崩'),
 ('tweakeroo', '工具', 'M 打开 Tweakeroo 菜单，开关一项'),
 ('status-effect-bars', '装饰', '状态效果条显示（吃一瓶药水）'),
 ('cave-dust', '装饰', '洞穴内看到尘埃粒子'),
 ('wakes', '装饰', '水面/船尾迹粒子'),
 ('better-selection', '工具', '方块选中框更贴合形状'),
 ('chatpatches', '装饰', '聊天栏复制/时间戳正常'),
 ('custom-splash-screen', '装饰', '启动时自定义 splash'),
 ('held-item-info', '装饰', '手持物品信息 HUD'),
 ('hold-my-items', '装饰', '手持物品位置/动画变化'),
 ('connectiblechains', '装饰', '铁链连接方块正常渲染'),
 ('lazy-language-loader', '优化', '切换语言不卡死'),
 ('fpsdisplay', '工具', 'FPS 显示叠加层'),
 ('reacharound', '工具', '远距离放置方块（reach 扩展）'),
 ('inmis', '玩法', '打开背包物品栏'),
 ('universal-graves', '机制', '死亡后墓碑生成并取回物品'),
 ('lenient-death', '机制', '死亡不掉落/惩罚可配置'),
 ('totemcounter', '工具', '图腾数量 HUD'),
 ('minihud', '工具', 'M 打开 Minihud 菜单，开一个信息行'),
]
INFRA = [
 ('fabric-language-kotlin', '库', '依赖它的 mod（zoomify/optigui）能起来'),
 ('malilib', '库', '依赖它的 mod（litematica/tweakeroo/minihud）能起来'),
 ('cardinal-components-api', '库', '依赖它的 mod 能起来'),
 ('cloth-config', '库（原生版）', '配置界面能打开'),
 ('yacl', '库（原生版）', '配置界面能打开'),
 ('resourceful-lib', '库', '依赖它的 mod 能起来'),
 ('placeholder-api', '库', 'modmenu 依赖'),
 ('ukulib', '库', 'totemcounter 依赖'),
]
CONTENT = [
 ('farmers-delight-refabricated', '内容', '种植/烹饪一件食物'),
 ('betterend', '内容', '创造物品栏出现 BetterEnd 方块'),
 ('betternether', '内容', '进入下界看新群系'),
 ('friends-and-foes', '内容', '创造物品栏出现新生物蛋'),
 ('the-bumblezone-fabric', '内容', '进入 Bumblezone 维度'),
 ('repurposed-structures-fabric', '内容', '新世界生成后结构出现'),
]
L3 = ['vulkanmod','exordium','nvidium','cull-less-leaves','indium','c2me-fabric','ebe','animatica',
      'skyboxify','flashback','threadtweak','bobby','axiom','cit-resewn','particular','eating-animation',
      'capes','gamma-utils','sodium-extra','iris','sodium','distancetransform' ]

all_slugs = [s for s,_,_ in MAIN] + [s for s,_,_ in INFRA] + [s for s,_,_ in CONTENT]
meta = {}
for s in all_slugs:
    try:
        vs = get('https://api.modrinth.com/v2/project/%s/version?game_versions=%%5B%%221.21.1%%22%%5D&loaders=%%5B%%22fabric%%22%%5D' % s)
    except Exception as e:
        meta[s] = {'error': str(e)}; continue
    if not vs:
        meta[s] = {'error': 'no fabric 1.21.1 version'}; continue
    v = vs[0]
    f = (v.get('files') or [{}])[0]
    meta[s] = {'version': v.get('version_number'), 'file': f.get('filename'), 'url': f.get('url'),
               'sha1': (f.get('hashes') or {}).get('sha1'),
               'dep_ids': [d['project_id'] for d in v.get('dependencies', [])
                           if d.get('dependency_type') == 'required' and d.get('project_id')]}
    time.sleep(0.1)

ids = sorted({i for m in meta.values() for i in m.get('dep_ids', [])})
names = {}
for i in range(0, len(ids), 100):
    url = 'https://api.modrinth.com/v2/projects?ids=' + urllib.parse.quote(json.dumps(ids[i:i+100]), safe='')
    for pr in get(url):
        names[pr['id']] = pr['slug']
for s, m in meta.items():
    m['deps'] = [names.get(i, i) for i in m.get('dep_ids', [])]

def rows(group):
    out = []
    for s, t, chk in group:
        m = dict(meta.get(s, {}))
        out.append({'slug': s, 'type': t, 'check': chk, 'version': m.get('version'),
                    'file': m.get('file'), 'url': m.get('url'), 'sha1': m.get('sha1'),
                    'deps': m.get('deps', []), 'error': m.get('error')})
    return out

corpus = {
 'game_version': '1.21.1', 'loader': 'neoforge 21.1.265 + connector 2.0.0-beta.17',
 'main': rows(MAIN), 'infra': rows(INFRA), 'content_phase2': rows(CONTENT),
 'excluded_l3': L3,
 'notes': [
   '主样本集 = 90% 主指标的分母；infra/content 单独统计。',
   'cloth-config / yacl 有 NeoForge 原生构建：作为前置时装原生版（用户真实做法），不是 Fabric 版。',
   'sodium 已是原生 NeoForge 构建，不在 corpus（L3 边界，见 HANDOFF 决策 29）。',
   '坏 jar 会毒化 Connector early remap，必须单 mod 跑（HANDOFF 决策 28）。',
 ]
}
pathlib.Path('compat').mkdir(exist_ok=True)
pathlib.Path('compat/corpus.json').write_text(json.dumps(corpus, ensure_ascii=False, indent=1), 'utf-8')

def table(items, title):
    lines = [f'## {title}', '', '| # | mod | 版本 | 类型 | 必需前置（Fabric 版） | 抽查项 | 下载 |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    rows_ = json.loads(pathlib.Path('logs/compat_corpus_600.json').read_text('utf-8'))
    dl = {r['slug']: r.get('downloads') for r in rows_}
    for i, it in enumerate(items, 1):
        deps = ', '.join(d for d in it['deps'] if d != 'fabric-api') or '—'
        d = dl.get(it['slug'])
        lines.append(f"| {i} | `{it['slug']}` | {it['version']} | {it['type']} | {deps} | {it['check']} | {d:,} |" if d
                     else f"| {i} | `{it['slug']}` | {it['version']} | {it['type']} | {deps} | {it['check']} | ? |")
    return lines

md = ['# SuperLoader 兼容样本集 v1（待审）', '',
      '口径：MC 1.21.1，Modrinth 前 600 个 Fabric mod → 127 个只有 Fabric 构建 → 人工筛出下列；',
      '排除 API/运行时库与 L3 渲染重写（见文末）。主指标只用「主样本集」。', '',
      '主样本集 %d 个；基础设施 %d 个；内容组（阶段 2）%d 个。' % (len(MAIN), len(INFRA), len(CONTENT)), '']
md += table(corpus['main'], '主样本集（90%% 分母，%d 个）' % len(MAIN))
md += ['']
md += table(corpus['infra'], '基础设施集（单独统计，%d 个）' % len(INFRA))
md += ['']
md += table(corpus['content_phase2'], '内容组（阶段 2，单独统计，%d 个）' % len(CONTENT))
md += ['', '## 排除：L3 渲染/内核重写（不做，仅记录）', '', ', '.join('`%s`' % s for s in L3), '']
md += ['## 测试方法要点', '',
       '1. 每个样本单独一次 launch：基础前置集（FFAPI/Connector + 该样本所需前置）+ 1 个候选，跑完恢复 `mods/`；',
       '2. 判定：无 FATAL + 无 crash report + 进入「新的世界」+ 抽查项通过；',
       '3. 前置有原生版（cloth-config / yacl）时装原生；Fabric-only 前置（FLK / malilib / cardinal-components / resourceful-lib）装 Fabric 版，失败会连坐，归因时先看前置；',
       '4. 单 mod 跑是硬要求：坏 jar 会让 Connector early remap 整轮跳过（HANDOFF 决策 28）。']
pathlib.Path('compat/corpus_v1.md').write_text('\n'.join(md) + '\n', 'utf-8')
errs = [s for s, m in meta.items() if m.get('error')]
print('main=%d infra=%d content=%d errors=%s' % (len(MAIN), len(INFRA), len(CONTENT), errs))

