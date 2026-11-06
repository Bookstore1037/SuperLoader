import pathlib

p = pathlib.Path(r'D:\SuperLoader\HANDOFF.md')
lines = p.read_text('utf-8').splitlines()

new_item = """2. **bclib 去皮桥**（companion 0.6.0 → 0.6.3，2026-11-05）
   - 缺口：bclib 的 `AxeItemMixin` 把去皮逻辑挂在 `AxeItem.getStripped(BlockState)`（`@Inject` HEAD，cancellable），
     靠 `org.betterx.bclib.interfaces.tools.AxeCanStrip#strippedState(BlockState)` 给自定义方块提供结果。
     NeoForge 21.1 起斧头改走 `BlockState.getToolModifiedState(UseOnContext, ItemAbility, Z)` → 数据映射
     `NeoForgeDataMaps.STRIPPABLES`，`getStripped` 变成 private 且全 jar 无调用者 → 注入点成了死代码：
     不报错、也不生效（betterend/betternether 的方块斧头不去皮）
   - 补丁：`com.superloader.companion.AxeStripBridge` 监听 NeoForge 的 `BlockEvent.BlockToolModificationEvent`
     （`EventHooks.onToolUse` 会为斧头发这个事件），当 `getItemAbility() == ItemAbilities.AXE_STRIP`、
     方块实现 bclib `AxeCanStrip`、且 `finalState` 没有被换成**另一个方块**时，用 `strippedState(state)` 作为结果
   - **`finalState` 语义（0.6.0/0.6.1 的坑）**：NeoForge 把事件的 `finalState` 初始化成**原方块状态**，不是 null；
     用 `finalState != null` 判断"别人已经给了结果"会永远提前返回 → 桥装上了但从不命中。正确判据是
     `finalState.getBlock() != state.getBlock()`
   - 覆盖类别：所有依赖 bclib `AxeCanStrip` 的模组（betterend / betternether / 后续 betterx 系），不认 mod id、不认 jar 名
   - 兼容性：接口按**名字符串**递归判断（子接口 + 父类链），方法用反射 `getMethod("strippedState", BlockState.class)`；
     先用 `Class.forName` 判断 bclib 是否存在会在 Connector 的独立加载器下抛 `ClassNotFoundException` 并静默禁用（0.6.0 的坑）
   - 开关：`SL_NO_AXE_BRIDGE=1` 或 `-Dsuperloader.axeBridge.disabled=true`
   - 日志：安装 `[sl-bridge] axe strip bridge installed ...`（0.6.2+ 另打加载器可见性与首个 tool 事件）；前 5 次命中打 `[sl-bridge] axe strip: <旧> -> <新> (hit #n)`
   - 状态：**已实测生效（2026-11-05 20:55，companion 0.6.3，实例 65 jar）**——`latest.log` 里 5 条 `axe strip:`，
     `betterend:lacugrove_log -> betterend:lacugrove_stripped_log`、`betternether:nether_sakura_log -> betternether:nether_sakura_stripped_log`"""

start = 85
end = 98
assert lines[start].startswith('2. **bclib 去皮桥**'), lines[start]
assert '待实测' in lines[end - 1], lines[end - 1]
lines[start:end] = new_item.split('\n')
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('ledger item 2 replaced, file lines =', len(lines))
