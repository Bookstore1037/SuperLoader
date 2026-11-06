import json, pathlib
p=pathlib.Path('compat/corpus.json'); c=json.loads(p.read_text('utf-8'))
c['assembly']['join_evidence'] = (
 "companion 的 world_joined 事件尚未实现（P1 待办）。当前用客户端日志的强证据判定："
 "(A) LoggerChunkProgressListener 的 `Time elapsed: <n> ms`（出生点区块加载完成，一次性打印）；"
 "(B) `Saving chunks for level`（世界被保存过，只可能发生在进入之后）。"
 "弱证据只记录不判定：AdvancementTree 的 `Loaded <n> advancements`、`Preparing spawn area`。"
 "同时记录 `level.dat` mtime 是否推进作为旁证。实测 2026-11-04 12:06 原生 Sodium 启动："
 "强证据命中 `Time elapsed: 273 ms`，弱证据命中 `Loaded 1465 advancements`，level.dat 被写。"
)
p.write_text(json.dumps(c,ensure_ascii=False,indent=1),'utf-8')
print('assembly.join_evidence set')
