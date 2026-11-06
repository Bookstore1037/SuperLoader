# tools/inspect_mdk.py
"""扫 MDK 项目，列出结构 + 模板残留（examplemod / ExampleMod 等）。

用法:
    python tools/inspect_mdk.py <mdk项目路径>
    python tools/inspect_mdk.py D:\\NeoForgeProbe
"""
import re
import sys
from pathlib import Path

# 跳过这些目录（构建产物、IDE 缓存、运行时数据）
SKIP_DIRS = {".gradle", "build", ".git", ".idea", "run", "out", "bin", ".vscode"}

# 模板残留的关键词，大小写敏感地分别列，避免误报
PATTERNS = [
    re.compile(r"examplemod"),
    re.compile(r"ExampleMod"),
    re.compile(r"example_mod"),
    re.compile(r"Example Mod"),
    re.compile(r"com\.example"),
]

# 文本文件才读内容，二进制跳过（.jar/.png/.class 等）
TEXT_SUFFIXES = {".java", ".kt", ".gradle", ".properties", ".toml", ".json",
                 ".mcmeta", ".md", ".txt", ".xml", ".yml", ".yaml", ".gitignore"}


def is_text(p: Path) -> bool:
    if p.name in {".gitignore", "gradlew", "gradlew.bat"}:
        return True
    return p.suffix.lower() in TEXT_SUFFIXES


def walk(root: Path):
    """递归遍历，跳过 SKIP_DIRS。返回 (文件列表)。"""
    files = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            files.append(p)
    return sorted(files)


def print_tree(root: Path, files):
    print("=== 目录结构 ===")
    for p in files:
        rel = p.relative_to(root)
        depth = len(rel.parts) - 1
        print(f"{'  ' * depth}{rel.name}")


def scan_residue(root: Path, files):
    print("\n=== 模板残留（按文件） ===")
    hits = 0
    for p in files:
        if not is_text(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        matched = []
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat in PATTERNS:
                if pat.search(line):
                    matched.append((lineno, line.strip()))
                    break
        if matched:
            hits += 1
            rel = p.relative_to(root)
            print(f"\n{rel}")
            for lineno, line in matched:
                # 截断过长行
                snippet = line if len(line) <= 160 else line[:160] + " ..."
                print(f"  L{lineno}: {snippet}")
    if hits == 0:
        print("（无残留）")
    else:
        print(f"\n共 {hits} 个文件含残留")


def scan_resources(root: Path):
    print("\n=== src/main/resources 下的文件 ===")
    res = root / "src" / "main" / "resources"
    if not res.exists():
        print("（不存在）")
        return
    for p in sorted(res.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(res)}")


def main():
    if len(sys.argv) != 2:
        print("用法: python tools/inspect_mdk.py <mdk项目路径>")
        sys.exit(2)
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"不是目录: {root}")
        sys.exit(2)

    files = walk(root)
    print(f"项目根: {root}")
    print(f"文件总数（跳过 .gradle/build/.git 等）: {len(files)}")

    print_tree(root, files)
    scan_residue(root, files)
    scan_resources(root)


if __name__ == "__main__":
    main()