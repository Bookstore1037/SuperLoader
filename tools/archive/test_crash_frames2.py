import sys, pathlib, json, tempfile

sys.path.insert(0, r'D:\SuperLoader')
from core import suspects as S

report_dir = pathlib.Path(r'D:\SLData\instances\1.21.1\logs\superloader-report')
mods = json.loads((report_dir / 'mods.json').read_text('utf-8'))
mixins = json.loads((report_dir / 'mixins.json').read_text('utf-8'))
index = {m['mod_id']: {'mod_id': m['mod_id'], 'jar': m.get('jar')} for m in mods.get('mods', []) if m.get('mod_id')}

log = """[06Nov2026 12:00:00.000] [Render thread/FATAL] [ne.ne.fm.ModLoader/CORE]: Error during pre-loading phase: boom
java.lang.RuntimeException: boom
\tat TRANSFORMER/bclib@21.0.13/org.betterx.bclib.api.v2.datafixer.DataFixerAPI.fixData(DataFixerAPI.java:100)
\tat TRANSFORMER/minecraft@1.21.1/net.minecraft.client.Minecraft.runTick(Minecraft.java:1195)
[06Nov2026 12:00:01.000] [Thread-8/WARN] [bclib/]: Failed to create backup of level
java.io.IOException: file locked
\tat java.base/sun.nio.ch.FileDispatcherImpl.write0(Native Method)
"""
tmp = pathlib.Path(tempfile.gettempdir()) / 'replay_frames.log'
tmp.write_text(log, encoding='utf-8')
print('hits:', S.scan_crash_frames(tmp, index, mixins))
print('console:', S.scan_console(tmp, index))
