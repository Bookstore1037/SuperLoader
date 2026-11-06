import json
import pathlib

p = pathlib.Path(r"D:\SuperLoader\compat\corpus.json")
d = json.loads(p.read_text("utf-8"))
entry = {
    "slug": "replaymod",
    "version": "1.21-2.6.28",
    "file": "replaymod-1.21-2.6.28.jar",
    "layer": "L2",
    "cause": (
        "NeoForge 21.1 把 GameRenderer.render 里的 Screen;renderWithTooltip 调用换成 ClientHooks.drawScreen，"
        "原注入点消失；Connector 把 @At target 重写成 DeltaTracker;getGameTimeDeltaTicks 且丢掉 shift=AFTER，"
        "handler 每帧在 overlay 阶段执行，GuiGraphics 为 null 时 VanillaGuiScreen$EventHandler.onGuiRender 的 "
        "stack.flush() NPE"
    ),
    "not_mod_bug": (
        "replaymod 的 mixins.jgui.refmap.json 里有该注入点的正确映射（class_437;method_47413），"
        "Fabric 上靠 refmap 正常工作；同类的 @ModifyArg 在 mapped jar 里未被改写"
    ),
    "cluster": (
        "165 个 jar 里只有 replaymod 的 MixinGameRenderer 在 GameRenderer.render 里注入被移走的 "
        "Screen;renderWithTooltip；其余（chatpatches/cloth-config/JEI/Jade/sodium/midnightlib/lenientdeath）"
        "只是调用 GuiGraphics.flush() 或注入 Screen 自己的方法"
    ),
    "action": "不在 companion 写特判；作为 Connector 上游 mixin patch 缺口处理，issue 草稿见 compat/replaymod-investigation.md",
    "date": "2026-11-05",
    "evidence": "compat/replaymod-investigation.md; crash-reports/crash-2026-11-05_13.40.40-client.txt",
}
d.setdefault("excluded_upstream_defects", []).append(entry)
d.setdefault("notes", []).append(
    "replaymod 1.21-2.6.28 在 NeoForge 21.1 下必崩（L2 目标迁移 + Connector 错误重定位 @At），"
    "不是 mod 自身 bug，也不是 refmap 缺口；详见 compat/replaymod-investigation.md。")
p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("ok", len(d["excluded_upstream_defects"]), "defects")
