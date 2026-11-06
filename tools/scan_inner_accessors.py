"""Scan jars for @Invoker/@Accessor mixins whose target is an inner class (Outer$Inner).

Heuristic class-file scan (no ASM):
  * a class qualifies if its constant pool references Mixin's Invoker or Accessor annotation
  * and it references at least one net/minecraft descriptor containing '$'
  * and the '$' class is the mixin target candidate

Usage:
    python tools/scan_inner_accessors.py [--jars DIR ...] [--json PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent.parent
DESC = re.compile(r"L(net/minecraft[^;]*\$[^;]*);")


def _parse_class(data: bytes):
    """Return (cp_utf8_list, cp_class_names, has_invoker_or_accessor)."""
    if len(data) < 10 or data[:4] != b"\xca\xfe\xba\xbe":
        return None
    pos = 8
    count = struct.unpack_from(">H", data, pos)[0]
    pos += 2
    utf8 = {}
    cls_refs = {}
    i = 1
    while i < count:
        tag = data[pos]
        pos += 1
        if tag == 1:
            ln = struct.unpack_from(">H", data, pos)[0]
            pos += 2
            utf8[i] = data[pos:pos + ln].decode("utf-8", "replace")
            pos += ln
        elif tag in (7, 8, 16, 19, 20):
            if tag == 7:
                cls_refs[i] = struct.unpack_from(">H", data, pos)[0]
            pos += 2
        elif tag in (15,):
            pos += 3
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            pos += 4
        elif tag in (5, 6):
            pos += 8
            i += 1
        else:
            return None
        i += 1
    return utf8, cls_refs


def scan_jar(path: Path):
    hits = []
    try:
        zf = zipfile.ZipFile(path)
    except Exception:
        return hits
    with zf:
        for name in zf.namelist():
            if not name.endswith(".class"):
                continue
            try:
                data = zf.read(name)
            except Exception:
                continue
            parsed = _parse_class(data)
            if not parsed:
                continue
            utf8, _ = parsed
            strings = list(utf8.values())
            if not any(s in ("Lorg/spongepowered/asm/mixin/gen/Invoker;", "Lorg/spongepowered/asm/mixin/gen/Accessor;") for s in strings):
                continue
            targets = sorted({m.group(1).replace("/", ".") for s in strings for m in [DESC.search(s)] if m})
            if not targets:
                continue
            hits.append({"class": name[:-6].replace("/", "."), "targets": targets})
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jars", action="append", default=[])
    ap.add_argument("--json", default=str(CODE_ROOT / "logs" / "inner_accessor_scan.json"))
    args = ap.parse_args(argv)

    dirs = [Path(p) for p in args.jars] or [
        CODE_ROOT / ".cache" / "compat" / "jars",
        Path(r"D:\SLData\instances\1.21.1\mods"),
    ]
    rows = []
    for d in dirs:
        if not d.exists():
            continue
        for jar in sorted(d.glob("*.jar")):
            hits = scan_jar(jar)
            if hits:
                rows.append({"jar": str(jar), "hits": hits})

    total = sum(len(r["hits"]) for r in rows)
    print(f"jars_with_inner_accessor_targets={len(rows)} mixin_classes={total}")
    for r in rows:
        print(f"\n{Path(r['jar']).name}")
        for h in r["hits"]:
            print(f"  {h['class']} -> {', '.join(h['targets'])}")

    out = {"generated_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
           "dirs": [str(x) for x in dirs], "jars": rows, "mixin_classes": total}
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[json] {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
