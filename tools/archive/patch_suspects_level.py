import pathlib

p = pathlib.Path(r'D:\SuperLoader\core\suspects.py')
t = p.read_text('utf-8')

old = 'LOG_SUSPECT = re.compile(r"\\[(?:\\w[^\\]/]*/)?(?:ERROR|FATAL)\\]|Exception|Caused by:")'
assert old in t, 'LOG_SUSPECT not found'

new = old + '\n' + (
    '# 日志级别，形如 [Thread-8/WARN]；WARN 里附带的异常栈只是警告，不算可疑模组\n'
    'LEVEL = re.compile(r"\\[(?:[^\\]]*/)?(ERROR|FATAL|WARN|INFO|DEBUG|TRACE)\\]")\n'
    'HARD_LEVEL = re.compile(r"\\[(?:[^\\]]*/)?(?:ERROR|FATAL)\\]")'
)
t = t.replace(old, new, 1)

old2 = """    for line in _read_log_lines(log_path):
        if not LOG_SUSPECT.search(line):
            continue
        owner = _attribute(line, index, jars)"""
assert old2 in t, 'loop not found'

new2 = """    level = None
    for line in _read_log_lines(log_path):
        m = LEVEL.search(line)
        if m:
            level = m.group(1)
        if not LOG_SUSPECT.search(line):
            continue
        # WARN/INFO 块里附带的 Exception 只是警告（如 bclib 备份存档时文件被锁），不算可疑模组
        if level not in (None, "ERROR", "FATAL") and not HARD_LEVEL.search(line):
            continue
        owner = _attribute(line, index, jars)"""
t = t.replace(old2, new2, 1)
p.write_text(t, encoding='utf-8')
print('scan_console level guard added')
