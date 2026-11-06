import json, pathlib
p=pathlib.Path('compat/corpus.json')
c=json.loads(p.read_text('utf-8'))
c['notes']=[
 '主样本集 = auto / manual 两套判据的分母；infra、content 单独统计；反例（expected=fail）不进分母。',
 '依赖一律装 Fabric 构建（测 Connector remap 路径）；cloth-config / yacl / resourceful-lib 的原生构建只作参照组，评测台不自动装。',
 'L3 且已有原生构建的（sodium / iris / sodium-extra）列在 excluded_l3_with_native，不进主样本，也不算兼容性失败。',
 '坏 jar 会毒化 Connector early remap，必须单样本隔离跑（HANDOFF 决策 28）。',
 '依赖闭包 61/61 完整；每个 jar 带 version_id + sha1，评测台装完必须校验（compat/deps_closure.json）。',
]
p.write_text(json.dumps(c,ensure_ascii=False,indent=1),'utf-8')
print('notes updated')
