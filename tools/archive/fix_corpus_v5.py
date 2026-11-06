"""v5 修正：反例假设被实测推翻；补样本加载门槛与隔离说明；记录两个真负例控制。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "compat" / "corpus.json"
data = json.loads(CORPUS.read_text("utf-8"))

for r in data.get("negative") or []:
    if r["slug"] == "carpet":
        r["expected"] = "pass"
        r["expected_layer"] = "none"
        r["expected_reason"] = ("原假设 L2（改 vanilla 行为）被实测推翻：12:16 首轮隔离失效时通过；"
                                "12:2x 修好隔离后仍需复核。旧证据不可用。")
        r["hypothesis_falsified"] = True
    if r["slug"] == "mixintrace":
        r["expected"] = "pass"
        r["expected_layer"] = "none"
        r["expected_reason"] = ("原假设 L4（钩 MixinService/agent）被实测推翻；首轮为基线实例进世界，"
                                "不算证据，修好隔离后需重跑。")
        r["hypothesis_falsified"] = True

data["negative_controls"] = [
    {
        "slug": "neg_dep_test",
        "jar": "logs/dep-test/superloader_dep_test-1.0.0.jar",
        "expected": "fail",
        "expected_layer": "L0",
        "observed": {"verdict": "fail", "reason": "fatal_in_log",
                     "fatal": "Error during pre-loading phase: Some of your mods are incompatible ... requires version 99.0.0 or later of fabric_screen_api_v1"},
        "note": "纯元数据 jar，depends fabric-screen-api-v1 >=99.0.0；证明判定器能抓到初始化阶段依赖失败",
    },
    {
        "slug": "neg_sodium_fabric",
        "jar": "logs/tmp-mods-backup/[钠] sodium-fabric-0.8.13+mc1.21.1.jar",
        "expected": "fail",
        "expected_layer": "L2",
        "observed": {"verdict": "fail", "reason": "fatal_in_log",
                     "fatal": "Mixin apply for mod sodium failed ... InvalidInjectionException ... Found unexpected argument type float[] at index 2, expected float"},
        "note": "Fabric 版 Sodium 经 Connector 重映射后 @WrapMethod handler 签名不匹配；证明判定器能抓到 mixin 注解重映射失败",
    },
]

asm = data.setdefault("assembly", {})
asm["isolation"] = ("每样本 mods.compat/<slug>/ → 运行时把实例 mods/ 暂存为 mods.__baseline、"
                    "复制样本目录到 mods/（FML 只扫 gameDir/mods），跑完立即换回；异常中断用 --restore-mods")
asm["verdict_gate"] = ("pass 还要求 sample_loaded=true：样本自己的 jar 必须出现在本次 ModList 且 loaded 非空，"
                       "否则 fail(sample_not_loaded)——首轮 12:16 的 9 个 pass 就是没过这道门（游戏读的是实例 mods/）")
asm["fail_order"] = "fatal_in_log > crash_screen > timeout_no_runtime > sample_not_loaded > no_world_join > pass"

CORPUS.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
print("negative:", [(r["slug"], r["expected"], r.get("expected_layer")) for r in data["negative"]])
print("controls:", [c["slug"] for c in data["negative_controls"]])
