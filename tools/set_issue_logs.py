"""Fill the `### Logs` section of an issue draft with paste-site URLs.

Usage:
    python tools/set_issue_logs.py 01-replaymod https://mclo.gs/aaaa https://mclo.gs/bbbb
    python tools/set_issue_logs.py --all compat/issues/log_urls.json
    python tools/set_issue_logs.py --dry-run 01-replaymod https://example.com/x

The first URL is labelled "debug.log", the second "crash report". If you have only
one URL, use the `crash=` / `debug=` prefixes to say which one it is:
    python tools/set_issue_logs.py 02-minihud debug=https://mclo.gs/aaaa
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ISS = ROOT / "compat" / "issues"


def build_block(items: list[tuple[str, str]]) -> str:
    lines = [
        "### Logs",
        "",
        "Minimal setup: Connector 2.0.0-beta.17 + Forgified Fabric API + this mod"
        " (and its dependencies) only, see \"Steps to reproduce\".",
        "",
    ]
    for label, url in items:
        lines.append(f"- `{label}`: {url}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def patch(case: str, items: list[tuple[str, str]], dry: bool) -> None:
    f = ISS / f"{case}.md"
    if not f.exists():
        raise SystemExit(f"no such draft: {f}")
    t = f.read_text("utf-8")
    start = t.find("### Logs")
    end = t.find("### Additional context")
    if start < 0 or end < 0:
        raise SystemExit(f"{f.name}: cannot find the Logs/Additional context sections")
    new = t[:start] + build_block(items) + t[end:]
    if dry:
        print(new[start:start + 600])
        return
    f.write_text(new, encoding="utf-8")
    print(f"{case}: {len(items)} link(s) written")


def parse_args(argv: list[str]) -> tuple[bool, str | None, str | None]:
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    allfile = None
    if "--all" in argv:
        i = argv.index("--all")
        allfile = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    case = argv[0] if argv else None
    return dry, allfile, case


def main() -> int:
    dry, allfile, case = parse_args(sys.argv[1:])
    if allfile:
        data = json.loads(pathlib.Path(allfile).read_text("utf-8"))
        for name, urls in data.items():
            items = [(f"url {i + 1}", u) for i, u in enumerate(urls)]
            patch(name, items, dry)
        return 0
    if not case:
        print(__doc__)
        return 2
    items: list[tuple[str, str]] = []
    for arg in sys.argv[1:]:
        if arg.startswith("debug="):
            items.append(("debug.log", arg.split("=", 1)[1]))
        elif arg.startswith("crash="):
            items.append(("crash report", arg.split("=", 1)[1]))
        elif arg.startswith("http"):
            items.append(("debug.log" if not items else "crash report", arg))
    if not items:
        print("no URLs given")
        return 2
    patch(case, items, dry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
