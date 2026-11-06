# 样本集 v4：provenance / connector_dep / 负例与移植类移出分母 / 口径写死
import json
import pathlib

C = pathlib.Path("compat/corpus.json")
D = pathlib.Path("compat/deps_closure.json")
c = json.loads(C.read_text("utf-8"))
d = json.loads(D.read_text("utf-8"))

PORTED = {
    "beautify-refabricated": "社区 refabrication（Suel-ki），非原作者发布",
    "sophisticated-core-unofficial-fabric-port": "Unofficial Fabric port（Salandora）",
    "farmers-delight-refabricated": "社区移植（MehVahdJukaar），内容组，本就不进分母",
}

closure = {r["slug"]: r for g in ("main", "infra", "content_phase2") for r in d[g]}


def loader_of(e):
    kind = e.get("kind")
    if kind == "jij":
        return "jij"
    if kind in ("ffapi", "ffapi-root"):
        return "ffapi(桥接)"
    return "fabric"


def deps_detail(slug):
    r = closure.get(slug) or {}
    owners = {slug, r.get("mod_id") or slug}
    out = []
    for e in r.get("entries") or []:
        if e.get("required_by") not in owners or e.get("kind") == "builtin":
            continue
        out.append({
            "id": e.get("id"),
            "slug": e.get("slug"),
            "kind": e.get("kind"),
            "loader": loader_of(e),
            "version": e.get("version"),
            "spec": e.get("spec"),
        })
    return out


def conn_dep(slug):
    r = closure.get(slug) or {}
    return "yes" if any(e.get("kind") == "jij" for e in (r.get("entries") or [])) else "no"


def decorate(r):
    slug = r["slug"]
    r["provenance"] = "ported" if slug in PORTED else "official"
    r["connector_dep"] = conn_dep(slug)
    r["deps_detail"] = deps_detail(slug)
    if slug in PORTED:
        r["provenance_reason"] = PORTED[slug]
    return r


# 从 closure 的原始 48 个主样本重建分组（脚本可重跑）
old = {r["slug"]: r for r in (c.get("main") or []) + (c.get("negative") or []) + (c.get("ported_out") or [])}
base = []
for r in d["main"]:
    rec = dict(old.get(r["slug"]) or {})
    rec.setdefault("slug", r["slug"])
    rec.setdefault("version", r.get("mod_version"))
    rec.setdefault("file", r.get("file"))
    rec.setdefault("url", r.get("url"))
    rec.setdefault("sha1", r.get("sha1"))
    rec.setdefault("version_id", r.get("version_id"))
    rec.setdefault("nf_build", r.get("nf_build"))
    rec.setdefault("nf_evidence", r.get("nf_evidence"))
    rec.setdefault("verdict_mode", r.get("verdict_mode"))
    rec.setdefault("expected", r.get("expected") or "pass")
    rec.setdefault("expected_layer", r.get("expected_layer"))
    rec.setdefault("manual_check", r.get("manual_check"))
    rec.setdefault("check", r.get("check"))
    rec.setdefault("type", r.get("type"))
    base.append(decorate(rec))

main = [r for r in base if r["provenance"] == "official" and r.get("expected") != "fail"]
negative = [r for r in base if r.get("expected") == "fail"]
ported_out = [r for r in base if r["provenance"] == "ported"]

c["main"], c["negative"], c["ported_out"] = main, negative, ported_out

for r in c.get("content_phase2") or []:
    decorate(r)

auto_n = sum(1 for r in main if r.get("verdict_mode") == "auto")
manual_n = sum(1 for r in main if r.get("verdict_mode") == "manual")
c["rate_definition"] = {
    "auto_n": auto_n,
    "manual_n": manual_n,
    "fixed": True,
    "auto": "auto_rate = auto_pass_n / %d" % auto_n,
    "manual": "manual_rate = manual_pass_n / %d（分母写死；manual_pass 只算用户人工核过的，未核既不计入分子也不改分母）" % manual_n,
    "negative": "expected=fail 的样本不进任何分母，只验证判定器判得出失败且层归对",
    "ported": "provenance=ported 的样本不进任何分母：失败优先归因移植质量，对 Connector 桥接补丁无指导意义",
    "scope_banner": "覆盖范围：客户端侧（UI/HUD/QoL/性能/库）；内容层与服务端不在 90% 口径内",
    "auto_scope_note": "auto 子集是按“能否自动断言”挑的（无 UI / 有文件产物 / 有日志标记），不代表主样本集分布；auto_rate 只描述这 %d 个样本" % auto_n,
}
c["assembly"] = {
    "ffapi": "fabric-api(桥接) = SuperLoader 运行时模组 forgified-fabric-api-<ver>+<n>+1.21.1.jar（44 个模块），由 superloader.py 的 MOD_SLUGS 下载到 <mods>/；不是样本依赖，不从 Modrinth 装 fabric-api",
    "runtime_mods": ["connector-*-full.jar", "forgified-fabric-api-*.jar", "superloader_companion-*.jar"],
    "mods_isolation": "每样本独立 mods 目录 instances/1.21.1/mods.compat/<slug>/，经 SL_MODS_DIR 指过去；libraries/versions/assets 只读共享，不复制",
    "save": "运行前从 logs/compat/save-backup/新的世界 恢复存档（首次运行先备份，17 MB），避免样本间污染",
    "timeout": "启动后 240 秒内 runtime.json 未更新（mtime 与 generated_at 都不变）→ verdict=fail reason=timeout_no_runtime",
    "crash_screen": "进程存活但出现新的 crash-reports/*.txt 或日志出现 crash screen 标记 → fail reason=crash_screen（关窗 exit_code=0 不算 pass）",
}
c["notes"] = [
    "主样本 = 分母（auto %d / manual %d）；负例、移植类、infra、内容组都不进分母。" % (auto_n, manual_n),
    "依赖一律装 Fabric 构建（测 Connector remap 路径）；cloth-config / yacl / resourceful-lib 的原生构建只作参照组，评测台不自动装。",
    "fabric-api(桥接) 指运行时模组 forgified-fabric-api（44 模块），不是 Modrinth 上的 fabric-api，见 assembly.ffapi。",
    "坏 jar 会毒化 Connector early remap，必须单样本隔离跑（HANDOFF 决策 28）：隔离粒度是 mods 目录 + 存档，不是整实例复制。",
    "依赖闭包 61/61 完整；每个 jar 带 version_id + sha1，评测台装完必须校验（compat/deps_closure.json）。",
]

C.write_text(json.dumps(c, ensure_ascii=False, indent=1), "utf-8")
print("main=%d auto=%d manual=%d negative=%d ported=%d" % (len(main), auto_n, manual_n, len(negative), len(ported_out)))
print("negative:", [r["slug"] for r in negative], "| ported:", [r["slug"] for r in ported_out])
print("connector_dep=yes:", [r["slug"] for r in main if r["connector_dep"] == "yes"])
