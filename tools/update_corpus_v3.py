"""v3 corpus update — A2/A3/B1/B3/C1/C2/C3 fields.

Adds to every corpus entry: verdict_mode (auto|manual), expected (pass|fail),
expected_layer, scope (client|content), auto_assert / manual_check text.
Promotes malilib to a main sample (C2), adds 5 fabric-only samples so the pure
auto subset reaches 10, adds 2 negative controls (C3), and splits the L3
exclusion list into "no native build" vs "has native build" (B3).
"""
import json, pathlib

P = pathlib.Path('compat/corpus.json')
c = json.loads(P.read_text('utf-8'))

AUTO = {
    'krypton': '无 UI / 纯传输层：进存档 + 无 FATAL/crash + Netty handler 安装无异常',
    'debugify': '无 UI / 修 bug：进存档 + 无 FATAL/crash + 其 mixin 全部 applied',
    'no-resource-pack-warnings': '无 UI / 只压警告：启动日志中不再出现该类警告',
    'lazy-language-loader': '启动期加载：启动到主菜单无卡死/异常',
    'fastquit': '关窗路径：关窗后进程在阈值内退出（不做人工确认）',
    'forcecloseworldloadingscreen': '进世界路径：进入世界后加载屏已关闭',
    'yosbr': '配置文件产物：首次启动后 options.txt 含其写入的默认值',
    'stackdeobf': '启动产物：日志出现 stackdeobf 标记、堆栈可读',
    'faster-random': '无 UI / 随机数加速：进存档 + 无 FATAL/crash + 世界生成不报错',
    'sophisticated-core-unofficial-fabric-port': '库：ModList 出现 + 进存档 + 无 FATAL/crash',
}

MANUAL = {
    'modmenu': '打开 Mods 列表能看到全部 mod',
    'zoomify': '按住缩放键实际生效',
    'language-reload': 'F3+T 重载语言不崩、界面文字正确',
    'presence-footsteps': '脚步粒子/音效在移动时出现',
    'visuality': '粒子效果按配置出现',
    'morechathistory': '聊天记录条数超出原版上限',
    'litematica': '打开投影菜单、加载/放置投影正常',
    'fallingleaves': '树叶粒子下落效果可见',
    'optigui': 'GUI 背景/按钮纹理被替换且不崩',
    'better-mount-hud': '骑乘时 HUD 显示血量/跳跃条',
    'fabrishot': '截图快捷键生成本地高清截图文件',
    'replaymod': '录制开始/停止、回放能加载（预期失败，见 expected）',
    'paginatedadvancements': '进度界面分页可用',
    'main-menu-credits': '主菜单右下角出现版本/署名文本',
    'tooltipfix': '长提示文本换行而非溢出屏幕',
    'better-ping-display-fabric': '多人服务器中 HUD 显示 ping/延迟条',
    'beautify-refabricated': '装饰方块/物品外观生效',
    'carpet': '/carpet 指令可用、规则生效（预期失败，见 expected）',
    'stendhal': '打开书本/任务界面、翻页正常',
    'tweakeroo': '打开配置界面、任一 tweak 生效',
    'status-effect-bars': '状态效果 HUD 条显示且位置正确',
    'cave-dust': '洞穴尘埃粒子可见',
    'wakes': '水中尾迹粒子可见',
    'better-selection': '方块选中框样式改变',
    'chatpatches': '聊天记录持久化、重启后仍在',
    'custom-splash-screen': '启动画面 logo/背景被替换',
    'held-item-info': '手持物品时 HUD 显示附魔/耐久信息',
    'hold-my-items': '切换物品栏时手持物不消失/位置正确',
    'connectiblechains': '链条连接相邻栅栏',
    'fpsdisplay': 'HUD 显示帧率且数值随场景变化',
    'reacharound': '远距离放置方块时手臂伸展',
    'inmis': '背包物品栏可用、存取正常',
    'universal-graves': '死亡后生成墓碑并可取回物品',
    'lenient-death': '死亡惩罚按配置生效（不掉落/保留经验等）',
    'totemcounter': 'HUD 显示图腾数量',
    'minihud': '打开信息行显示坐标/生物群系等',
    'malilib': 'Mods → MaLiLib → Config 能打开其配置 GUI，热键注册无异常',
    'mixintrace': 'mixin 服务正常（预期失败，见 expected）',
}

EXPECTED_FAIL = {
    'carpet': ('L2', 'Carpet 通过 mixin/ASM 深度改造服务端类与指令树；Connector 的 mixin 重映射对这类“改 vanilla 行为”的注入覆盖不到，预期在 apply 阶段失败'),
    'mixintrace': ('L4', 'Mixintrace 钩住 Fabric 的 MixinService/agent 内部实现；NeoForge 自带 mixin 服务与 Fabric 版本不同源，预期在类加载/服务替换阶段失败'),
}

NEW_SAMPLES = [
    ('yosbr', '配置默认值', '客户端'),
    ('stackdeobf', '调试工具', '客户端'),
    ('faster-random', '性能', '客户端'),
    ('sophisticated-core-unofficial-fabric-port', '库（非官方 Fabric 移植）', '客户端'),
    ('mixintrace', '调试工具（反例）', '客户端'),
]


def norm(entry, group):
    slug = entry['slug']
    entry['scope'] = 'client' if group != 'content_phase2' else 'content'
    if slug in EXPECTED_FAIL:
        entry['expected'] = 'fail'
        entry['expected_layer'] = EXPECTED_FAIL[slug][0]
        entry['expected_reason'] = EXPECTED_FAIL[slug][1]
        entry['verdict_mode'] = 'manual'
        entry['manual_check'] = MANUAL.get(slug, entry.get('check') or '')
    elif group == 'content_phase2':
        entry['expected'] = 'pass'
        entry['expected_layer'] = None
        entry['verdict_mode'] = 'manual'
        entry['manual_check'] = entry.get('check') or ''
    elif slug in AUTO:
        entry['expected'] = 'pass'
        entry['expected_layer'] = None
        entry['verdict_mode'] = 'auto'
        entry['auto_assert'] = AUTO[slug]
    else:
        entry['expected'] = 'pass'
        entry['expected_layer'] = None
        entry['verdict_mode'] = 'manual'
        entry['manual_check'] = MANUAL.get(slug, entry.get('check') or '')
    return entry


# C2: malilib 提为独立主样本（原 infra 里的条目移走）
malilib = next((e for e in c['infra'] if e['slug'] == 'malilib'), None)
if malilib:
    c['infra'] = [e for e in c['infra'] if e['slug'] != 'malilib']
    malilib['type'] = '库（C2 独立样本）'
    malilib['check'] = 'Mods 界面能打开 MaLiLib 配置 GUI；热键注册无异常'
    c['main'].append(malilib)

existing = {e['slug'] for e in c['main']}
for slug, typ, check in NEW_SAMPLES:
    if slug in existing:
        continue
    c['main'].append({'slug': slug, 'type': typ, 'check': check,
                      'version': None, 'file': None, 'url': None, 'sha1': None,
                      'deps': [], 'error': None})

for g in ('main', 'infra', 'content_phase2'):
    c[g] = [norm(e, g) for e in c[g]]

# B3: L3 拆分
OLD_L3 = list(c.get('excluded_l3') or [])
WITH_NATIVE = {
    'sodium': 'mc1.21.1-0.8.13-neoforge（2026-08-28，官方构建，已实测进世界通过：决策 29）',
    'iris': '1.8.14-beta.1+1.21.1-neoforge（2026-06-13）',
    'sodium-extra': 'mc1.21.1-0.9.5+neoforge（2026-10-25）',
}
NO_NATIVE = [s for s in OLD_L3 if s not in WITH_NATIVE and s != 'distancetransform']
c['excluded_l3_no_native'] = NO_NATIVE
c['excluded_l3_with_native'] = [{'slug': s, 'evidence': e} for s, e in WITH_NATIVE.items()]
c.pop('excluded_l3', None)
c['excluded_l3_notes'] = {
    'removed': ['distancetransform（Modrinth 上无此 slug，404，删除）'],
    'indium_note': 'indium 无 NeoForge 构建，且它是 Sodium 的 Fabric 端 FRAPI 实现补丁；NeoForge 上不需要，属“真不做”而非“没得做”',
}
c['scope_declaration'] = {
    'v1': '客户端侧（UI/HUD/QoL/性能/库）',
    'out_of_scope': '服务端/内容层（worldgen、结构、配方、生物）不进 90% 口径',
    'reason': '内容正确性无法用“进存档 + 无崩溃”判定（要按种子比对地形/结构/掉落），smoke 测试只会给出假数字；仅保留 6 个内容组样本在阶段 2 做“能进世界”的 smoke，单独报告',
}
c['rate_definition'] = {
    'auto_pass': '进存档 + 无 FATAL + 无 crash report',
    'manual_pass': 'auto 三条 + 人工核查“核心功能可用”',
    'formula': 'auto_rate = auto_pass_n / auto_n；manual_rate = manual_pass_n / manual_n；对外同时给两个数，不给混合数',
    'negative_controls': 'expected=fail 的样本不进分母，只验证“评测台判得出失败且层归对”',
}
P.write_text(json.dumps(c, ensure_ascii=False, indent=1), 'utf-8')
print('main=%d infra=%d content=%d auto=%d manual=%d fail_ctrl=%d' % (
    len(c['main']), len(c['infra']), len(c['content_phase2']),
    sum(1 for e in c['main'] if e['verdict_mode'] == 'auto'),
    sum(1 for e in c['main'] if e['verdict_mode'] == 'manual'),
    sum(1 for e in c['main'] if e['expected'] == 'fail')))
for e in c['main']:
    print('%-45s %-6s %-5s %s' % (e['slug'], e['verdict_mode'], e['expected'], e.get('expected_layer') or ''))
