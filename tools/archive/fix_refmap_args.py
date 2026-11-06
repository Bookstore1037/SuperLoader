import pathlib

p = pathlib.Path(r'D:\SuperLoader\superloader.py')
s = p.read_text(encoding='utf-8')

s = s.replace('from core.paths import MC_VERSION\n',
              'from core.paths import MC_VERSION\nfrom pathlib import Path\n\nCODE_ROOT = Path(__file__).resolve().parent\n', 1)

s = s.replace('    lock = paths.root / "compat" / "mappings.lock.json"',
              '    lock = CODE_ROOT / "compat" / "mappings.lock.json"', 1)
s = s.replace('                "--cache", str(paths.root / ".cache" / "compat" / "mappings"),',
              '                "--cache", str(CODE_ROOT / ".cache" / "compat" / "mappings"),', 1)
s = s.replace('    corpus = paths.root / "compat" / "corpus.json"',
              '    corpus = CODE_ROOT / "compat" / "corpus.json"', 1)
s = s.replace('        entry = (data.get("yarn") or {}).get(paths.MC_VERSION) or {}',
              '        entry = (data.get("yarn") or {}).get(MC_VERSION) or {}', 1)
s = s.replace('        if paths.MC_VERSION in jar.parent.name:',
              '        if MC_VERSION in jar.parent.name:', 1)

p.write_text(s, encoding='utf-8')
print('fixed')
