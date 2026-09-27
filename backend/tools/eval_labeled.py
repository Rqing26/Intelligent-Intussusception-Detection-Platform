"""带标签数据的完整评测：准确率 / ROC-AUC / 最佳阈值 / 置信度校准

回答两个问题：
  1. **准确率到底多少**？ —— 混淆矩阵 + 敏感性/特异性/PPV/NPV/F1 + ROC-AUC（含 bootstrap 置信区间）
  2. **置信度怎么搞**？ —— 可靠性曲线（分数分箱 → 实际阳性率）对比现在的标定表，
     判断"证据分能否当概率用""当前阈值是否合理""标定表要不要重做"

与算法侧 `eval_algorithm.py` 的区别：
  · 输入卫生：按**影像**去重（同一张图可能被上传多次、文件名各异），并剔除
    **AI 标注输出图**（uploads/results/ 下我们自己画了框的图）与**整屏截图**
    —— 这两类混进来会让指标同时虚高与虚低（详见 tools/eval_confidence.py 的 collect）
  · 输出 ROC-AUC 与阈值扫描（官方脚本只给单点指标）
  · 给出可靠性曲线，直接回答"置信度"的可用性
  · 所有指标带 bootstrap 95% 置信区间（样本量小，点估计不可信）
  · 保存逐图分数 CSV，便于写进材料/论文

⚠️ 置信度校准的进一步诊断（Wilson 区间 / ECE / 「分数近似二值」的证据）在
   `tools/eval_confidence.py`，两个脚本共用同一套输入卫生规则。

用法（backend 目录下）：
    .\\venv\\Scripts\\python.exe tools\\eval_labeled.py --pos ..\\uploads --neg "E:\\正常肠道图像\\正常肠道图像"
    .\\venv\\Scripts\\python.exe tools\\eval_labeled.py --pos A --pos B --neg C --csv eval.csv
"""
import argparse
import csv
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))   # 同目录脚本互 import
os.chdir(BACKEND_DIR)

import numpy as np  # noqa: E402

from algorithm import model_core  # noqa: E402
from algorithm.pipeline import load_image  # noqa: E402
from eval_confidence import collect  # noqa: E402  复用输入卫生规则，避免两套逻辑漂移

RNG = np.random.default_rng(20260927)


def score_of(path):
    """按生产路径打分：多帧取分数最高的帧；返回 (证据分, 是否被判「图像质量不佳」)。"""
    frames = model_core.to_bgr_frames(load_image(path))
    best = -1.0
    best_frame = None
    for fr in frames:
        s = float(model_core.score_image(fr)["score"])
        if s > best:
            best, best_frame = s, fr
    # 质量不佳 = 规则判定（近全黑 + 模型无响应），此时不给阳性
    thr = float(model_core.POLICIES[model_core.POLICY]["threshold"])
    cls, _, _, _ = model_core.decide(best, thr, best_frame)
    return best, cls == "图像质量不佳"


def _auc(scores, labels):
    """ROC-AUC（Mann-Whitney U，处理并列取平均秩）。"""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)
    pos, neg = scores[labels == 1], scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    sorted_scores = scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    rank_sum = ranks[labels == 1].sum()
    return float((rank_sum - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def metrics_at(scores, labels, thr, poor):
    """给定阈值下的混淆矩阵与指标。poor=规则判为质量不佳的图（不计阳性）。"""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)
    poor = np.asarray(poor, dtype=bool)
    pred = (scores >= thr) & (~poor)

    tp = int(((pred == 1) & (labels == 1)).sum())
    fp = int(((pred == 1) & (labels == 0)).sum())
    fn = int(((pred == 0) & (labels == 1)).sum())
    tn = int(((pred == 0) & (labels == 0)).sum())

    def safe(a, b):
        return a / b if b else float("nan")

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "sensitivity": safe(tp, tp + fn),
        "specificity": safe(tn, tn + fp),
        "ppv": safe(tp, tp + fp),
        "npv": safe(tn, tn + fn),
        "accuracy": safe(tp + tn, tp + fp + fn + tn),
        "f1": safe(2 * tp, 2 * tp + fp + fn),
    }


def bootstrap(scores, labels, poor, thr, n=2000):
    """分层 bootstrap：分别重采样正/负样本，给出各指标的 95% 区间。"""
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)
    poor = np.asarray(poor, dtype=bool)
    pi = np.where(labels == 1)[0]
    ni = np.where(labels == 0)[0]
    keys = ["sensitivity", "specificity", "ppv", "npv", "accuracy", "f1"]
    acc = {k: [] for k in keys}
    aucs = []
    for _ in range(n):
        idx = np.concatenate([RNG.choice(pi, len(pi), replace=True),
                              RNG.choice(ni, len(ni), replace=True)])
        m = metrics_at(scores[idx], labels[idx], thr, poor[idx])
        for k in keys:
            acc[k].append(m[k])
        aucs.append(_auc(scores[idx], labels[idx]))
    out = {}
    for k in keys:
        v = np.array([x for x in acc[k] if not np.isnan(x)])
        out[k] = (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)
    a = np.array([x for x in aucs if not np.isnan(x)])
    out["auc"] = (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))) if len(a) else (np.nan, np.nan)
    return out


def best_threshold(scores, labels, poor):
    """Youden 指数最大点（敏感性 + 特异性 - 1）。"""
    scores = np.asarray(scores, dtype=float)
    cands = np.unique(np.concatenate([scores, [0.0]]))
    best, best_j = None, -2.0
    for t in cands:
        m = metrics_at(scores, labels, t, poor)
        if np.isnan(m["sensitivity"]) or np.isnan(m["specificity"]):
            continue
        j = m["sensitivity"] + m["specificity"] - 1
        if j > best_j:
            best, best_j = (t, m, j), j
    return best


def pct(v):
    return "—" if v is None or np.isnan(v) else f"{v * 100:.1f}%"


def main() -> int:
    try:                                   # Windows 控制台默认 GBK，中文会乱码
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--pos", nargs="+", required=True, help="正样本目录（可多个）")
    ap.add_argument("--neg", nargs="+", required=True, help="负样本目录（可多个）")
    ap.add_argument("--csv", default=None, help="把逐图分数写到 CSV")
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap 次数")
    ap.add_argument("--exclude", nargs="*", default=[], help="额外排除的文件名/相对路径 glob")
    ap.add_argument("--exclude-dir", nargs="*", default=["results"], help="排除的目录名（默认 results）")
    args = ap.parse_args()

    pos, pos_skip = collect(args.pos, args.exclude, args.exclude_dir)
    neg, neg_skip = collect(args.neg, args.exclude, args.exclude_dir)
    for tag, sk in (("正样本", pos_skip), ("负样本", neg_skip)):
        if sk:
            from collections import Counter
            c = Counter(why for _, why in sk)
            print(f"{tag}剔除 {len(sk)} 张：{dict(c)}")

    thr = float(model_core.POLICIES[model_core.POLICY]["threshold"])
    print("=" * 78)
    print(f"策略 {model_core.POLICY} v{model_core.POLICIES[model_core.POLICY]['version']}  "
          f"部署阈值={thr}  融合={model_core.POLICIES[model_core.POLICY]['fusion']}")
    print(f"正样本 {len(pos)} 张 / 负样本 {len(neg)} 张（剔除标注图·截图·重复后）")
    print("=" * 78)

    rows = []
    for label, group in ((1, pos), (0, neg)):
        for path in group:
            s, poor = score_of(path)
            rows.append({"path": str(path), "name": path.name, "label": label,
                         "score": round(s, 6), "poor_quality": int(poor)})

    scores = [r["score"] for r in rows]
    labels = [r["label"] for r in rows]
    poor = [r["poor_quality"] for r in rows]

    # ---- 1) 部署阈值下的指标 ----
    m = metrics_at(scores, labels, thr, poor)
    ci = bootstrap(scores, labels, poor, thr, args.boot)
    auc = _auc(scores, labels)

    print(f"\n【1】部署阈值 {thr} 下的表现")
    print(f"  混淆矩阵：TP={m['tp']}  FP={m['fp']}  FN={m['fn']}  TN={m['tn']}"
          f"（规则判「图像质量不佳」{sum(poor)} 张）")
    print(f"  {'指标':<14}{'点估计':>10}{'95% 置信区间':>22}")
    for k, name in [("sensitivity", "敏感性(召回)"), ("specificity", "特异性"),
                    ("ppv", "精确率 PPV"), ("npv", "NPV"), ("accuracy", "准确率"), ("f1", "F1")]:
        print(f"  {name:<14}{pct(m[k]):>10}   [{pct(ci[k][0])}, {pct(ci[k][1])}]".rjust(0))
    print(f"  {'ROC-AUC':<14}{auc:>10.4f}   [{ci['auc'][0]:.4f}, {ci['auc'][1]:.4f}]")

    # ---- 2) 最佳阈值 ----
    bt = best_threshold(scores, labels, poor)
    if bt:
        t, bm, j = bt
        print(f"\n【2】Youden 最佳阈值 = {t:.6f}（当前部署 {thr}）")
        print(f"  敏感性={pct(bm['sensitivity'])}  特异性={pct(bm['specificity'])}  "
              f"准确率={pct(bm['accuracy'])}  精确率={pct(bm['ppv'])}  Youden J={j:.3f}")
        print(f"  对比：部署阈值下 敏感性={pct(m['sensitivity'])}  特异性={pct(m['specificity'])}")

    # ---- 3) 可靠性曲线（置信度能不能用）----
    print("\n【3】证据分 → 实际阳性率（可靠性曲线）与现有标定表对比")
    print(f"  {'分箱':<16}{'样本数':>7}{'实际阳性率':>12}{'现有标定表值':>14}")
    edges = [0.0, 0.001, 0.005, 0.02, 0.05, 0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 1.01]
    for a, b in zip(edges[:-1], edges[1:]):
        sel = [(s, l) for s, l in zip(scores, labels) if a <= s < b]
        if not sel:
            continue
        rate = sum(l for _, l in sel) / len(sel)
        table_val = model_core.calibrate_positive((a + min(b, 1.0)) / 2)
        print(f"  [{a:<5.3f},{b:<5.3f}){len(sel):>7}{rate * 100:>11.1f}%{table_val * 100:>13.1f}%")
    print("\n  读法：若「实际阳性率」与该分箱的标定值差很多，说明现有标定表需要重做；")
    print("        若各分箱阳性率都接近 100% 且分数区间很窄，说明分数对阴阳性区分度有限。")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["name", "label", "score", "poor_quality", "path"])
            w.writeheader()
            w.writerows(rows)
        print(f"\n逐图分数已保存：{args.csv}")

    print("\n⚠️ 注意事项（指标解读的前提）")
    print("  · 样本量小（%d 正 / %d 负），置信区间较宽，点估计不宜作为泛化性能宣传" % (len(pos), len(neg)))
    print("  · 若这些图片曾参与模型训练/调参，则属于数据泄漏，指标会显著虚高")
    print("  · 正负样本来源不同（采集设备/截图方式不同），模型可能学到来源差异而非病理差异")
    print("    —— 本机实测：阴性参考集与 demo 阳性集来自不同来源，标定表跨来源失效（见 eval_confidence.py）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
