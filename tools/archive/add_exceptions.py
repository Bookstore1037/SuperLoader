import json, pathlib
p=pathlib.Path('compat/corpus.json'); c=json.loads(p.read_text('utf-8'))
c['exceptions']=[
 'fastquit 3.0.0+1.20.6：jar 内 depends.minecraft = ">=1.20.5"（读自 fabric.mod.json），1.21.1 满足，不会触发 L0；版本号只是旧命名（1.21.1 上无更新构建）。',
 'tooltipfix 1.1.1-1.20：jar 内 depends 里**没有 minecraft 项**（只有 fabricloader>=0.12.5 与 fabric），FML 不会因 MC 版本拒绝加载；但它是 1.20 编译的，风险落在 L2/L4（映射/方法签名），不在 L0。',
 'distancetransform / distance-transform 在 Modrinth 均 404，没能确认是改名重发；已从 L3 排除名单删除（项目不存在，不属于“L3 不做”）。',
]
p.write_text(json.dumps(c,ensure_ascii=False,indent=1),'utf-8')
print('ok')
