import sys, pathlib, json, tempfile

sys.path.insert(0, r'D:\SuperLoader')
from core import suspects as S

report_dir = pathlib.Path(r'D:\SLData\instances\1.21.1\logs\superloader-report')
mods = json.loads((report_dir / 'mods.json').read_text('utf-8'))
mixins = json.loads((report_dir / 'mixins.json').read_text('utf-8'))

index = {}
for m in mods.get('mods', []):
    if m.get('mod_id'):
        index[m['mod_id']] = {'mod_id': m['mod_id'], 'jar': m.get('jar')}

cases = {
    'replaymod': r'D:\SLData\instances\1.21.1\crash-reports\crash-2026-11-05_13.40.40-client.txt',
    'languagereload': r'D:\SLData\instances\1.21.1\crash-reports\crash-2026-11-05_20.24.47-client.txt',
}
for name, path in cases.items():
    text = pathlib.Path(path).read_text('utf-8', errors='replace')
    body = '[06Nov2026 12:00:00.000] [Render thread/FATAL] [ne.ne.fm.ModLoader/CORE]: Error during pre-loading phase\n'
    body += '---- Minecraft Crash Report ----\n' + text
    tmp = pathlib.Path(tempfile.gettempdir()) / f'replay_{name}.log'
    tmp.write_text(body, encoding='utf-8')
    hits = S.scan_crash_frames(tmp, index, mixins)
    print(name, '->', {k: v[0][:130] for k, v in hits.items()})
