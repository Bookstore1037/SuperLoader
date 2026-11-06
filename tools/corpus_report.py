# 渲染 compat/corpus_v2.md（样本集 v5：首轮 auto 实测已回填）
import json
import pathlib
from collections import Counter, OrderedDict

C = pathlib.Path("compat/corpus.json")
D = pathlib.Path("compat/deps_closure.json")
OUT = pathlib.Path("compat/corpus_v2.md")

c = json.loads(C.read_text("utf-8"))
d = json.loads(D.read_text("utf-8"))
closure = {r["slug"]: r for g in ("main", "infra", "content_phase2") for r in d[g]}
rd = c["rate_definition"]
asm = c.get("assembly") or {}

L = []
A = L.append

A("# SuperLoader 兼容样本集 v5（2026-11-04，含首轮 auto 实测）\n")
A("> 数据源：`compat/deps_closure.json`（每个 jar 带 `version_id` + `sha1`，可复现安装）。")
A("> 首轮实测：`logs/compat/20261104-124552/`（auto 9 个，9 pass / 0 fail）。")
A("> 逐条修订说明见 `REVISION.md` §12 / §v4。\n")

A("## 0. 判定口径\n")
A("- **%s**" % rd["scope_banner"])
A("- `auto`：样本 jar 真的进 ModList（`sample_loaded=true`）+ 进存档 + 无 FATAL + 无 crash report（超时未产生新 runtime.json 判 fail）")
A("- `manual`：auto 四条 + 人工核查“核心功能可用”")
A("- 通过率：`%s`；`%s`" % (rd["auto"], rd["manual"]))
A("- 负例（expected=fail）与移植类（provenance=ported）不进任何分母")
A("- 90% 数字旁边必须带覆盖范围声明，不允许裸报")
A("- ⚠ %s" % rd["auto_scope_note"])
lr = c.get("last_run") or {}
if lr:
    A("- 首轮实测（%s）：auto **%d/%d pass**；manual 尚未人工核（分母仍 %d）\n"
      % (lr.get("dir"), lr.get("auto_pass", 0), lr.get("auto_n", 0), rd["manual_n"]))
else:
    A("")

A("## 0.1 v1 覆盖范围\n")
sd = c.get("scope_declaration") or {}
A("- 覆盖：**%s**" % sd.get("covered", "客户端侧（UI/HUD/QoL/性能/库）"))
A("- 不覆盖：**%s**" % sd.get("not_covered", "服务端/内容层（worldgen、结构、配方、生物）"))
if sd.get("reason"):
    A("- 理由：%s" % sd["reason"])
A("")

A("## 0.2 其他约定\n")
for n in c.get("notes") or []:
    A("- %s" % n)
A("")

A("## 0.3 实例拼装与判定规则（写死）\n")
A("| 项 | 规则 |")
A("|---|---|")
A("| fabric-api(桥接) | %s |" % asm.get("ffapi", ""))
A("| 运行时模组 | %s |" % "、".join("`%s`" % x for x in asm.get("runtime_mods") or []))
A("| mods 隔离 | %s |" % asm.get("isolation", asm.get("mods_isolation", "")))
A("| 判定门槛 | %s |" % asm.get("verdict_gate", ""))
A("| fail 顺序 | %s |" % asm.get("fail_order", ""))
A("| 存档 | %s |" % asm.get("save", ""))
A("| 超时 | %s |" % asm.get("timeout", ""))
A("| crash screen | %s |" % asm.get("crash_screen", ""))
A("| 进存档证据 | %s |" % asm.get("join_evidence", ""))
A("")

def verdict_label(r):
    if r.get("expected") == "fail":
        return "negative"
    return r.get("verdict_mode") or "?"


def fmt_deps(r):
    items = r.get("deps_detail") or []
    if not items:
        return "—"
    out = []
    for it in items:
        name = it.get("slug") or it.get("id")
        tag = it.get("loader")
        ver = it.get("version")
        if it.get("loader") == "jij":
            out.append("%s（内嵌）" % name)
        elif it.get("version") == "provided-by-forgified":
            out.append("%s〔%s〕" % (name, tag))
        else:
            out.append("%s@%s〔%s〕" % (name, ver, tag) if ver else "%s〔%s〕" % (name, tag))
    return "、".join(out)


main = c["main"]
A("## 1. 主样本集（%d 个；auto %d / manual %d）\n" % (len(main), rd["auto_n"], rd["manual_n"]))
A("| # | 样本 | 版本 | 判定 | 实测 | 来源 | NeoForge 构建 | 直接前置〔loader〕 | conn_dep | 闭包 | 安装集 |")
A("|---|---|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(main, 1):
    cl = closure.get(r["slug"]) or {}
    av = r.get("actual_verdict")
    act = ("%s/%s" % (av, r.get("actual_layer"))) if av else "未测"
    A("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d jar / %.1f MB |" % (
        i, r["slug"], r.get("version"), verdict_label(r), act, r.get("provenance", "official"),
        "无" if (r.get("nf_build") or "no") == "no" else r.get("nf_build"),
        fmt_deps(r), r.get("connector_dep", "no"),
        len(cl.get("entries") or []),
        cl.get("install_jars") or 0, (cl.get("install_bytes") or 0) / 1048576))
A("")
A("`conn_dep=yes` 表示闭包里带 jar-in-jar 依赖，失败时先查 Connector 是否 remap 内层 jar（L4）。\n")

auto = [r for r in main if r.get("verdict_mode") == "auto"]
A("## 2. auto 子集（%d 个；第一版通过率只用它）\n" % len(auto))
A("| # | 样本 | 自动断言点 | 首轮实测 |")
A("|---|---|---|---|")
for i, r in enumerate(auto, 1):
    av = r.get("actual_verdict")
    act = ("%s（%s）" % (av, r.get("actual_layer"))) if av else "未测"
    A("| %d | %s | %s | %s |" % (i, r["slug"],
                                 (r.get("manual_check") or r.get("check") or "").replace("|", "/"), act))
A("")
A("auto 判定 = sample_loaded + 进存档 + 无 FATAL + 无 crash report，再叠加表里断言点；不满足任一即 fail。\n")

neg = c.get("negative") or []
A("## 3. 负例（%d 个，expected=fail，不进分母）\n" % len(neg))
A("| 样本 | 判定 | 预期层 | 预期原因 | 实测层 |")
A("|---|---|---|---|---|")
for r in neg:
    act = ("%s（%s）" % (r.get("actual_verdict"), r.get("actual_layer"))) if r.get("actual_verdict") else "未测"
    A("| %s | negative | %s | %s | %s |" % (
        r["slug"], r.get("expected_layer"), (r.get("expected_reason") or r.get("check") or "").replace("|", "/"), act))
A("")
A("用途：验证判定器“判得出失败、层归得对”。若实测通过说明假设错，改回 pass 并记录。\n")

nc = c.get("negative_controls") or []
if nc:
    A("### 3.1 负例控制（可直接复现的已知失败，不进分母）\n")
    A("| 控制 | jar | 预期层 | 实测 | 证据 |")
    A("|---|---|---|---|---|")
    for x in nc:
        ob = x.get("observed") or {}
        A("| %s | `%s` | %s | %s（%s） | %s |" % (
            x["slug"], x.get("jar"), x.get("expected_layer"),
            ob.get("verdict", "未测"), ob.get("reason", "-"),
            (x.get("note") or "").replace("|", "/")))
    A("")

ported = c.get("ported_out") or []
A("## 4. 移植类（%d 个，provenance=ported，不进分母）\n" % len(ported))
A("| 样本 | 版本 | 判定 | 移出理由 |")
A("|---|---|---|---|")
for r in ported:
    A("| %s | %s | %s | %s |" % (r["slug"], r.get("version"), r.get("verdict_mode"), r.get("provenance_reason", "")))
A("")
A("理由：失败优先归因移植质量，对 Connector 桥接补丁无指导意义。内容组里的移植类只影响内容组，不影响主指标。\n")

A("## 5. 基础设施（%d 个，评测台预装，不计通过率）\n" % len(c["infra"]))
A("| 样本 | 版本 | NeoForge 构建 | 装哪一版 | 直接前置〔loader〕 |")
A("|---|---|---|---|---|")
for r in c["infra"]:
    A("| %s | %s | %s | Fabric（测 remap） | %s |" % (
        r["slug"], r.get("version"), "有" if r.get("nf_build") == "yes" else "无", fmt_deps(r)))
A("")
A("`yacl` 的 `fabric-api(桥接)` 由运行时模组 FFAPI 提供，见 §0.3。\n")

A("## 6. 内容组（%d 个，阶段 2；不进 90%% 分母）\n" % len(c["content_phase2"]))
A("| 样本 | 版本 | 来源 | 直接前置〔loader〕 | 安装集 |")
A("|---|---|---|---|---|")
for r in c["content_phase2"]:
    cl = closure.get(r["slug"]) or {}
    A("| %s | %s | %s | %s | %d jar / %.1f MB |" % (
        r["slug"], r.get("version"), r.get("provenance", "official"), fmt_deps(r),
        cl.get("install_jars") or 0, (cl.get("install_bytes") or 0) / 1048576))
A("")

A("## 7. L3 排除名单\n")
A("### (a) L3 且无原生构建（真不做）\n")
A("、".join(c.get("excluded_l3_no_native") or []))
A("")
A("### (b) L3 但有原生构建（记录 + 推荐原生，不算兼容性失败）\n")
A("| 样本 | 原生构建证据 | 结论 |")
A("|---|---|---|")
for r in c.get("excluded_l3_with_native") or []:
    if isinstance(r, dict):
        A("| %s | %s | 推荐原生；Connector 路径不追，不计失败 |" % (r.get("slug"), (r.get("evidence") or "").replace("|", "/")))
    else:
        A("| %s | — | 推荐原生 |" % r)
A("")
A("Sodium 与 c2me 不并列：Sodium 有官方 NeoForge 构建且实测通过（HANDOFF 决策 29），c2me 没有。\n")

A("## 8. 共用前置统计（主样本）\n")
cnt = Counter()
for r in main:
    for it in r.get("deps_detail") or []:
        if it.get("loader") == "fabric":
            cnt[it.get("slug") or it.get("id")] += 1
A("| 前置 | 被几个主样本依赖 |")
A("|---|---|")
for k, v in cnt.most_common():
    A("| %s | %d |" % (k, v))
A("")

A("## 9. jar 清单（去重，含 version_id + sha1）\n")
seen = OrderedDict()
for g in ("main", "infra", "content_phase2"):
    for r in d[g]:
        for it in r.get("install") or []:
            seen.setdefault(it["file"], it)
A("共 **%d** 个去重 jar。\n" % len(seen))
A("| jar | loader | version_id | sha1 |")
A("|---|---|---|---|")
for fn, it in seen.items():
    A("| `%s` | %s | `%s` | `%s` |" % (fn, it.get("loader", "fabric"), it.get("version_id"), (it.get("sha1") or "")[:16]))
A("")

A("## 10. 已移出：上游缺陷（不修、不改 jar）\n")
up = c.get("excluded_upstream_defects") or []
if up:
    A("| slug | version | 层 | 原因 | 处置 | 证据 |")
    A("|---|---|---|---|---|---|")
    for r in up:
        A("| `%s` | %s | %s | %s | %s | %s |" % (
            r.get("slug"), r.get("version"), r.get("layer"), r.get("cause"),
            r.get("action"), r.get("evidence")))
else:
    A("- （无）")
A("")

A("## 11. 已知口径例外\n")
exc = c.get("exceptions") or []
if exc:
    for e in exc:
        A("- %s" % e)
else:
    A("- （无）")
A("")
A("## 12. manual 验收进度（用户实测）\n")
mr = c.get("manual_results") or []
if mr:
    in_corpus = [r for r in mr if r.get("in_corpus", True)]
    npass = sum(1 for r in in_corpus if r.get("result") == "pass")
    A("已核 **%d / %d** 条，pass **%d**（分母来自 main 里 `verdict_mode=manual` 且未被移出的样本；未核不计入分子）。明细：\n" % (
        len(in_corpus), rd["manual_n"], npass))
    A("| mod | 检查点 | 结果 | 日期 | 备注 |")
    A("|---|---|---|---|---|")
    for r in mr:
        A("| `%s` | %s | %s | %s | %s |" % (
            r.get("slug"), r.get("check"), r.get("result"), r.get("date"),
            r.get("note") or ("不在 corpus（不进分母）" if r.get("in_corpus") is False else "")))
else:
    A("- （无）")
A("")

OUT.write_text("\n".join(L) + "\n", "utf-8")
print("written %s lines=%d" % (OUT, len(L)))
print("main=%d auto=%d manual=%d negative=%d ported=%d infra=%d content=%d jars=%d" % (
    len(main), rd["auto_n"], rd["manual_n"], len(neg), len(ported), len(c["infra"]), len(c["content_phase2"]), len(seen)))
