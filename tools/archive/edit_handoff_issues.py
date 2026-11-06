import pathlib

p = pathlib.Path(r'D:\SuperLoader\HANDOFF.md')
t = p.read_text('utf-8')

old = """- **C. 整理 Connector issue 合集**：✅ 已完成（2026-11-06）——`compat/connector-issues.md`（6 个 L2 案例，含环境表、
  根因、字节码证据、建议修法、提 issue 需要附的材料）"""
new = """- **C. 整理 Connector issue 合集**：✅ 已完成（2026-11-06）——按官方 `mod_incompatibility.yml` 模板写成
  **一模组一份英文草稿**：`compat/issues/01-replaymod.md` … `06-language-reload.md`（索引 `compat/issues/README.md`，
  每份含 Mod Name / Homepage / Minecraft version / Describe / Steps / Logs / Additional context、最小复现集、相关既有 issue）；
  `compat/connector-issues.md` 保留为中文取证附录。提之前只差 Logs 的 Gist 链接（模板不收文件上传）"""
assert old in t
t = t.replace(old, new, 1)

old2 = "- 六个 L2 案例的取证文档都在 `compat/*-investigation.md`，可直接整理成 Connector issue 合集"
new2 = ("- 六个 L2 案例的取证文档都在 `compat/*-investigation.md`；英文 issue 草稿已按官方模板拆好（`compat/issues/`，"
        "一模组一份，提交前只需补 Logs 的粘贴链接）")
assert old2 in t
t = t.replace(old2, new2, 1)

p.write_text(t, encoding='utf-8')
print('HANDOFF updated')
