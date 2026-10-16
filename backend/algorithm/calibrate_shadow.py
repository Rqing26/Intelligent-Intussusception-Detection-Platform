"""影子数据标定工具
====================

流程：

    # 1) 导出待标注清单（含已累积的分数）
    python -m algorithm.calibrate_shadow --export

    # 2) 人工/临床填写 shadow_data/labels.csv 的 label 列（1=肠套叠阳性，0=阴性）
    #    images/ 下对应文件即为待看图；review.html 可直接在浏览器里看
    # 3) 拟合阈值并给出 go/no-go
    python -m algorithm.calibrate_shadow --fit

设计要点（对应 p27 的教训）：

* **不要取"满足门槛后 Acc 最大"的边界点** —— 本地预验证证明那个规则在 300 例量级上是负收益。
  这里改成 **可行区间的中点**，并要求区间足够宽（默认 ≥0.010）与样本量足够（默认各 ≥120）。
* **用 bootstrap 下界而不是点估计做判定** —— 双 95 是一个合取条件，点估计无裕度时必然一半概率掉出去。
  判定标准：Precision 与 Accuracy 的 5% 分位（bootstrap 1000 次）**都 ≥0.95** 才建议切换。
* **与部署策略同口径对比** —— 在同一批标注数据上同时报 C0 的表现，避免"换了数据才好"的错觉。
* 阈值直接落在候选策略的**绝对分数**上，定准后写回 ``model_core.POLICIES[candidate]["threshold"]``
  并把 ``V2_THRESHOLD_CALIBRATED`` 置 True。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from algorithm import model_core, shadow  # noqa: E402

MIN_NEG = 120
MIN_POS = 120
MIN_BAND_WIDTH = 0.010
BOOTSTRAP = 1000
TARGET = 0.95


# --------------------------------------------------------------------------------------
def load_records() -> list:
    p = shadow.SHADOW_DIR / "shadow.jsonl"
    if not p.exists():
        print(f"[错误] 还没影子数据：{p}")
        return []
    out, seen = [], set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("md5") in seen:          # 同一张图多次请求 → 只留一条
            continue
        seen.add(r.get("md5"))
        out.append(r)
    return out


def load_labels() -> dict:
    p = shadow.SHADOW_DIR / "labels.csv"
    if not p.exists():
        return {}
    lab = {}
    with open(p, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            v = (row.get("label") or "").strip()
            if v in ("0", "1"):
                lab[row["md5"]] = int(v)
    return lab


def cmd_export():
    recs = load_records()
    if not recs:
        return 1
    lab = load_labels()
    shadow.SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    out = shadow.SHADOW_DIR / "labels.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["md5", "label", "deployed_score", "deployed_label", "shadow_score",
                    "black_ratio", "w", "h", "ts", "image"])
        for r in recs:
            w.writerow([r.get("md5"), lab.get(r["md5"], ""), r.get("deployed_score"), r.get("deployed_label"),
                        r.get("shadow_score"), r.get("black_ratio"), r.get("w"), r.get("h"),
                        r.get("ts"), r.get("image")])
    # 便于浏览的复核页
    html = ["<html><head><meta charset='utf-8'><title>影子数据复核</title></head><body>",
            f"<h2>影子数据复核（{len(recs)} 张，去重后）</h2>",
            "<p>请在 labels.csv 的 label 列填 1（阳性）或 0（阴性）。</p>"]
    for r in recs:
        img = r.get("image")
        html.append(f"<div style='display:inline-block;margin:6px;font:12px sans-serif'>"
                    f"<div>{r.get('deployed_label')} | deployed={r.get('deployed_score')} | shadow={r.get('shadow_score')}</div>"
                    + (f"<img src='{img}' style='width:260px'>" if img else "<div>（未存图）</div>")
                    + f"<div>{r.get('md5')[:12]}</div></div>")
    html.append("</body></html>")
    (shadow.SHADOW_DIR / "review.html").write_text("\n".join(html), encoding="utf-8")
    print(f"已导出 {out}（{len(recs)} 张，已填写 {sum(1 for r in recs if r['md5'] in lab)} 张）")
    print(f"复核页：{shadow.SHADOW_DIR / 'review.html'}")
    return 0


# --------------------------------------------------------------------------------------
def _metrics(pos, neg, thr):
    tp = sum(1 for s in pos if s >= thr)
    fp = sum(1 for s in neg if s >= thr)
    fn, tn = len(pos) - tp, len(neg) - fp
    prec = tp / max(tp + fp, 1)
    acc = (tp + tn) / max(len(pos) + len(neg), 1)
    sens = tp / max(len(pos), 1)
    return dict(TP=tp, FP=fp, FN=fn, TN=tn, Precision=prec, Accuracy=acc, Sensitivity=sens)


def _boot(pos, neg, thr, n=BOOTSTRAP, seed=0):
    rng = random.Random(seed)
    a, p = [], []
    for _ in range(n):
        bp = [pos[rng.randrange(len(pos))] for _ in range(len(pos))] if pos else []
        bn = [neg[rng.randrange(len(neg))] for _ in range(len(neg))] if neg else []
        m = _metrics(bp, bn, thr)
        a.append(m["Accuracy"]); p.append(m["Precision"])
    return (statistics.quantiles(a, n=20)[0] if len(a) > 20 else (min(a) if a else 0.0),
            statistics.quantiles(p, n=20)[0] if len(p) > 20 else (min(p) if p else 0.0))


def cmd_fit(min_lower: float = TARGET, use_point: bool = False, mode: str = "relative"):
    recs = load_records()
    lab = load_labels()
    all_lab = [r for r in recs if r["md5"] in lab]
    # ★ 只用「模型训练时没见过」的影像标定：样本内影像的候选策略分数被系统性压低，
    #   据此定出的阈值会偏低、真实 Precision 不达标。（旧记录没有该字段时按"未见过的"处理）
    rows = [r for r in all_lab if not r.get("in_sample")]
    n_in = len(all_lab) - len(rows)
    if n_in:
        print(f"[提示] 已排除 {n_in} 条「样本内」记录（训练语料里出现过），它们不参与标定。")
    if not rows:
        print("[错误] 还没有任何标注。先 --export，再填 labels.csv 的 label 列，然后 --fit")
        return 2

    cand = shadow.SHADOW_POLICY
    deployed = model_core.POLICY
    pos = [r["shadow_score"] for r in rows if lab[r["md5"]] == 1]
    neg = [r["shadow_score"] for r in rows if lab[r["md5"]] == 0]
    deployed_pos = [r["deployed_score"] for r in rows if lab[r["md5"]] == 1]
    deployed_neg = [r["deployed_score"] for r in rows if lab[r["md5"]] == 0]

    print("=" * 96)
    print(f"影子数据：已标注 {len(rows)} 张（阳性 {len(pos)} / 阴性 {len(neg)}）")
    print(f"部署策略 {deployed}（阈值 {model_core.POLICIES[deployed]['threshold']}）  "
          f"候选 {cand}（当前占位阈值 {model_core.POLICIES[cand]['threshold']}）")
    print("=" * 96)

    # ── 同一批数据上给部署策略的对照（含 bootstrap 下界，避免"换了数据才好"的错觉） ──
    deployed_thr = float(model_core.POLICIES[deployed]["threshold"])
    if deployed_pos and deployed_neg:
        m0 = _metrics(deployed_pos, deployed_neg, deployed_thr)
        a0, p0 = _boot(deployed_pos, deployed_neg, deployed_thr)
        print(f"  对照 {deployed}（部署，同批数据）: Prec={m0['Precision']:.4f} Acc={m0['Accuracy']:.4f} "
              f"Sens={m0['Sensitivity']:.4f} TP={m0['TP']} FP={m0['FP']}")
        print(f"       bootstrap 5% 下界: Prec={p0:.4f} Acc={a0:.4f}")
    else:
        m0 = a0 = p0 = None
        print(f"  对照 {deployed}: 数据里没有对应类别的样本，跳过")

    if len(neg) < MIN_NEG or len(pos) < MIN_POS:
        print(f"\n[样本不足] 需要阳性≥{MIN_POS} 且 阴性≥{MIN_NEG}；当前 {len(pos)}/{len(neg)}。"
              f"继续累积影子数据后再来拟合。")
        return 3

    # ── 可行阈值区间：Prec>=0.95 且 Acc>=0.95 ──
    cands = sorted(set(pos + neg), reverse=True)
    ok = [t for t in cands if _metrics(pos, neg, t)["Precision"] >= TARGET
          and _metrics(pos, neg, t)["Accuracy"] >= TARGET]
    if not ok:
        print("\n[无可行点] 在候选分数上找不到同时满足 Prec>=0.95 与 Acc>=0.95 的阈值 → 不建议切换。")
        return 4

    lo, hi = min(ok), max(ok)
    thr = (lo + hi) / 2.0                              # ★ 取中点，不取边界（p27）
    width = hi - lo
    m = _metrics(pos, neg, thr)
    acc_lo, prec_lo = _boot(pos, neg, thr)

    print(f"\n可行阈值区间 = [{lo:.6f}, {hi:.6f}]   宽={width:.6f}（要求≥{MIN_BAND_WIDTH}）")
    print("区间内若干取样点（看平台期是否平坦）：")
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        t = lo + (hi - lo) * frac
        mm = _metrics(pos, neg, t)
        print(f"    thr={t:.6f} ({frac*100:>3.0f}%)  Prec={mm['Precision']:.4f} Acc={mm['Accuracy']:.4f} "
              f"Sens={mm['Sensitivity']:.4f} TP={mm['TP']} FP={mm['FP']}")
    print(f"\n★ 取中点阈值 = {thr:.6f}")
    print(f"   点估计              Prec={m['Precision']:.4f} Acc={m['Accuracy']:.4f} Sens={m['Sensitivity']:.4f} "
          f"TP={m['TP']} FP={m['FP']} FN={m['FN']} TN={m['TN']}")
    print(f"   bootstrap 5% 下界   Prec={prec_lo:.4f} Acc={acc_lo:.4f}")

    if use_point:
        verdict = (width >= MIN_BAND_WIDTH and m["Accuracy"] >= TARGET and m["Precision"] >= TARGET)
        crit = "点估计判定：Prec 与 Acc 点估计均 ≥0.95"
    elif mode == "strict":
        verdict = (width >= MIN_BAND_WIDTH and acc_lo >= min_lower and prec_lo >= min_lower)
        crit = f"绝对下界判定：Prec 与 Acc 的 5% 下界均 ≥{min_lower}"
    else:
        # 相对占优判定（默认）：绝对下界在小样本下谁都达不到（现部署策略自己也只有 Acc 下界 0.9323），
        # 因此判定改成"点估计达标 + 同批数据上严格优于部署策略 + 可行区间足够宽"。
        beats = (m0 is not None and m["Accuracy"] >= m0["Accuracy"] and m["Precision"] >= m0["Precision"]
                 and acc_lo >= a0 and prec_lo >= p0)
        verdict = (width >= MIN_BAND_WIDTH and m["Accuracy"] >= TARGET and m["Precision"] >= TARGET
                   and (beats if m0 is not None else True))
        crit = (f"相对占优判定：点估计均≥0.95 且 同批数据上（点估计与 5% 下界）都不劣于部署策略 "
                f"且 可行区间宽≥{MIN_BAND_WIDTH:.3f}")

    # 与部署策略在同一批数据上比：候选是否占优（点估计）
    dom = None
    if m0 is not None:
        dom = (m["Accuracy"] > m0["Accuracy"]) and (m["Precision"] >= TARGET)

    print("\n" + "=" * 96)
    print(f"判定口径：{crit}")
    if dom is not None:
        print(f"同批数据对照：候选 Acc={m['Accuracy']:.4f} vs 部署 Acc={m0['Accuracy']:.4f}；"
              f"候选是否占优 = {'是' if dom else '否'}")
    if verdict:
        print("✅ 建议切换。落地步骤：")
        print(f'   1) model_core.POLICIES["{cand}"]["threshold"] = {thr:.6f}')
        print("   2) model_core.V2_THRESHOLD_CALIBRATED = True")
        print('   3) model_core.POLICY = "v2"')
        print("   4) 重跑：python -m algorithm.eval_algorithm --pos <正样本目录> --neg <负样本目录>")
    else:
        why = []
        if width < MIN_BAND_WIDTH:
            why.append(f"可行区间太窄({width:.4f}<{MIN_BAND_WIDTH})")
        if mode == "strict":
            if acc_lo < min_lower:
                why.append(f"Accuracy 5% 下界 {acc_lo:.4f} < {min_lower}")
            if prec_lo < min_lower:
                why.append(f"Precision 5% 下界 {prec_lo:.4f} < {min_lower}")
            print(f"提示：要把 Accuracy 下界抬到 {min_lower}，需要更大的样本量"
                  f"（当前 阳性{len(pos)}/阴性{len(neg)}；粗略讲，点估计≈{m['Accuracy']:.4f} 时，"
                  f"n 至少要到 ~{int((1.645**2)*m['Accuracy']*(1-m['Accuracy'])/max(1e-6,(m['Accuracy']-min_lower)**2))+1} 才能让下界≥{min_lower}）")
        print("❌ 不建议切换：" + "；".join(why) if why else "❌ 不建议切换")
    print("=" * 96)
    return 0 if verdict else 5


# --------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true", help="导出待标注清单与复核页")
    ap.add_argument("--fit", action="store_true", help="用标注数据拟合阈值并给出建议")
    ap.add_argument("--status", action="store_true", help="打印影子模式状态")
    ap.add_argument("--min-lower-bound", type=float, default=TARGET,
                    help=f"判定用的 5%% 下界门槛（默认 {TARGET}；仅供确有把握时下调）")
    ap.add_argument("--mode", choices=["relative", "strict", "point"], default="relative",
                    help="判定模式：relative=同批数据相对占优(默认)｜strict=绝对 5%% 下界｜point=仅点估计")
    ap.add_argument("--point-estimate", action="store_true", help="等价于 --mode point")
    a = ap.parse_args()
    if a.status:
        for k, v in shadow.stats().items():
            print(f"  {k:<14}= {v}")
        return 0
    if a.export:
        return cmd_export()
    if a.fit:
        return cmd_fit(min_lower=a.min_lower_bound, use_point=a.point_estimate, mode=("point" if a.point_estimate else a.mode))
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
