"""准确率置信度：证据分 → 可信度（pseudo-calibration），并回答「现有标定表能不能用」

背景
----
`model_core` 里有一张标定表 CALIB_POS / CALIB_NEG，是在算法侧的 **190 正 / 149 负留出集**
上拟合的（判界处精度 0.9485）。平台侧拿到的 evidence score 直接查这张表 → 显示成"置信度"。
于是在本机这份 20 张阴性参考集 + 28 张阳性 demo 图上，问题变成两件事：

  1. **准确率是多少**：点估计 + Wilson 95% 区间（小样本必须给区间，点估计不能宣传）
  2. **置信度能不能信**：把「证据分」按经验阳性率重新分箱，与现有标定表逐点对比，
     算 ECE（期望校准误差），判断标定表在这份数据上是否失效

本工具**不改任何部署常量**，只输出诊断 + 建议表（要改的话请先看输出的样本量警告）。

关键结论（读法）
----------------
* 证据分为 0 的样本占绝大多数（阴性全 0、部分阳性也 0）→ 分数几乎是**二值**的，
  因此"置信度"在这份数据上只能取值在「0 分档」与「>0 档」两个水平，谈不上精细概率。
* 现有标定表 >0 分档给 0.96~0.99，若本次实测阳性率明显低于它，说明存在**分布偏移**
  （不同设备/来源），标定表不能跨域外推 —— 这比"准确率 82% 还是 96%"更值得写进材料。

用法（backend 目录下）
    .\\venv\\Scripts\\python.exe tools\\eval_confidence.py ^
        --pos ..\\uploads --neg "E:\\正常肠道图像\\正常肠道图像" --exclude "result_*"
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from algorithm import model_core  # noqa: E402
from algorithm.pipeline import load_image  # noqa: E402

EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


# ─────────────────────────────────────────────────────────── 数据收集
def is_annotated(f: Path) -> bool:
    """判「这是 AI 标注输出图」：文件名前缀 `result_NN_`，或画面里有成片高饱和红像素。

    这类图是平台**输出**，拿它当评测输入等于让模型给"我们画了框的图"打分：
    实测同一张阳片，原图证据分 0.90，其标注图压到 0.00~0.74 —— 纯自指的假失败。
    像素判据覆盖"标注图被改过名/搬到别处"的情况；红像素既可能在红框上，
    也可能在标题文本框里，故对「四边带」与「四角块」都做统计。
    """
    if re.match(r"^result_\d+_", f.name):
        return True
    try:
        a = np.asarray(Image.open(f).convert("RGB"), dtype=np.int16)
    except Exception:
        return False
    if a.ndim != 3 or a.shape[2] < 3:
        return False
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 130) & (r - g > 50) & (r - b > 50)
    # BGR 蓝框兜底（cv2 里 ANNOT_COLOR=(0,0,255) 是红色，但别的实现可能用蓝色）
    blue = (b > 130) & (b - r > 50) & (b - g > 50)
    mark = red | blue
    if mark.sum() < 5:
        return False
    h, w = mark.shape
    band = max(2, (int(round(max(h, w) / 300)) or 1) * 3)
    edge = np.zeros_like(mark)
    edge[:band] = edge[-band:] = True
    edge[:, :band] = edge[:, -band:] = True
    ch, cw = max(4, h // 8), max(4, w // 8)
    corners = np.zeros_like(mark)
    corners[:ch, :cw] = corners[:ch, -cw:] = True
    corners[-ch:, :cw] = corners[-ch:, -cw:] = True
    return bool(mark[edge].sum() >= 0.10 * mark.sum() or mark[corners].sum() >= 0.15 * mark.sum())


def is_screenshot(f: Path) -> bool:
    """判「整屏截图」：竖屏、分辨率远超超声帧、长宽比 >1.3。

    超声单帧实测 576×768（横屏）或 155×162；手机整屏截图 941×1672 竖屏。
    截图上有状态栏/按钮，模型会被 UI 元素触发（实测一张截图拿到 0.314 证据分 → 报阳性 98.3%）。
    """
    try:
        w, h = Image.open(f).size
    except Exception:
        return False
    return h > w * 1.3 and h >= 1000


def _dhash(gray: np.ndarray) -> int:
    small = np.asarray(Image.fromarray(gray).resize((8, 8), Image.LANCZOS), dtype=np.float64)
    val = 0
    for b in (small > small.mean()).ravel():
        val = (val << 1) | int(b)
    return val


def _interior(gray: np.ndarray, frac: float = 0.92) -> np.ndarray:
    """按亮度重心裁掉四边（标注框/状态条都在边上），返回内部区域。"""
    ys, xs = np.where(gray > max(20.0, gray.mean() * 0.5))
    if len(ys) < 10:
        ys, xs = np.where(gray > 0)
    if len(ys) < 10:
        return gray
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    mh, mw = max(1, int((y1 - y0) * (1 - frac) / 2)), max(1, int((x1 - x0) * (1 - frac) / 2))
    cut = gray[y0 + mh:y1 - mh, x0 + mw:x1 - mw]
    return cut if cut.size > 64 else gray


def fingerprint(f: Path) -> dict | None:
    """尺寸 + 全图 dhash + 内部区域 dhash（用于跨"重新编码/画框"识别同一张影像）。"""
    try:
        im = Image.open(f).convert("L")
    except Exception:
        return None
    a = np.asarray(im)
    return {"w": im.size[0], "h": im.size[1], "bytes": f.stat().st_size,
            "d_full": _dhash(a), "d_in": _dhash(_interior(a))}


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def collect(dirs, exclude_patterns=(), exclude_dirs=("results",), audit: bool = False):
    """递归收集**可用于评测**的图片，返回 (保留, 剔除明细)。

    剔除五类（全部打印理由，不静默丢）：
      · 目录/文件名命中 --exclude
      · AI 标注输出图（uploads/results/ 或像素判据命中）
      · 整屏截图（非医学影像输入）
      · 同一影像重复提交：文件名主体相同 / 内容 MD5 相同
      · **标注输出图与根目录原图是同一张**（文件名主体不同、字节也不同，只能靠
        「尺寸相同 + 文件大小接近 + 内部区域 dhash 近似」配对）；只认最接近的一对，
        避免把巧合相似的两张真影像合并掉
    """
    import fnmatch
    import re

    ex_dirs = {str(d).strip("/\\").lower() for d in exclude_dirs}
    cand: list[Path] = []
    skipped: list[tuple[Path, str]] = []

    for d in dirs:
        p = Path(d)
        if not p.exists():
            print(f"  [警告] 目录不存在，跳过：{d}")
            continue
        files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.suffix.lower() in EXTS)
        for f in files:
            rel = str(f.relative_to(p)) if p.is_dir() else f.name
            if any(part.lower() in ex_dirs for part in f.parts):
                skipped.append((f, "标注输出目录"))
                continue
            if any(fnmatch.fnmatch(f.name, pat) or fnmatch.fnmatch(rel, pat) for pat in exclude_patterns):
                skipped.append((f, "文件名规则"))
                continue
            cand.append(f)

    def subject(f: Path) -> str:
        """文件名主体：result_NN_<uuid>.jpg 取 <uuid>，普通上传取词干。"""
        m = re.match(r"^result_\d+_([0-9a-f]{32})\.[A-Za-z]+$", f.name)
        return m.group(1) if m else f.stem

    fps = {f: fingerprint(f) for f in cand}
    cand = [f for f in cand if fps.get(f)]

    raw = [f for f in cand if not is_annotated(f)]
    annotated = [f for f in cand if f not in raw]

    # ── 标注图 × 原图 配对（每张标注图最多消掉一张原图，取证据最强的一对）
    # 实测（tools/check_pairs.py）：标注图尺寸与原图完全相同，字节数为原图的 0.70~1.13
    # （画框 + 重新编码），全图 dhash 距离 0~5、内部区域 dhash 距离 3~14。
    # 故判据取「同尺寸 + 字节比 0.60~1.70 + min(全图, 内部) dhash ≤ 8」。
    pair_scores = []
    for a in annotated:
        fa = fps[a]
        for r in raw:
            fr = fps[r]
            if (fa["w"], fa["h"]) != (fr["w"], fr["h"]):
                continue
            ratio = fa["bytes"] / fr["bytes"]
            if not (0.60 <= ratio <= 1.70):
                continue
            dist = min(_hamming(fa["d_full"], fr["d_full"]), _hamming(fa["d_in"], fr["d_full"]))
            if dist <= 8:
                pair_scores.append((dist, abs(ratio - 1.0), a, r))
    pair_scores.sort()
    used_ann: set[Path] = set()
    matched_raw: dict[Path, Path] = {}
    for dist, ratio, a, r in pair_scores:
        if a in used_ann or r in matched_raw:
            continue
        used_ann.add(a)
        matched_raw[r] = a

    groups: dict[str, list[Path]] = {}
    for f in raw:
        groups.setdefault(subject(f), []).append(f)

    def rank(f: Path):
        return (len(f.parts), len(f.name))

    kept: list[Path] = []
    for _, files in sorted(groups.items()):
        files.sort(key=rank)
        keep = files[0]
        for f in files[1:]:
            skipped.append((f, "同一影像重复提交"))
        if keep in matched_raw:
            # 该原图与某张标注图配对 → 留原图（字节真实的输入），标注图一并剔除
            skipped.append((matched_raw[keep], "标注输出图(与已保留原图同源)"))
        if is_screenshot(keep):
            skipped.append((keep, "整屏截图"))
            continue
        kept.append(keep)

    for a in annotated:
        if a not in used_ann:
            skipped.append((a, "标注输出图"))

    # 内容 MD5 兜底（不同文件名、字节完全相同的再传）
    seen, final = set(), []
    for f in kept:
        try:
            h = hashlib.md5(f.read_bytes()).hexdigest()
        except OSError:
            continue
        if h in seen:
            skipped.append((f, "字节重复"))
            continue
        seen.add(h)
        final.append(f)

    if audit:
        ann_to_raw = {a: r for r, a in matched_raw.items()}
        for a in sorted(used_ann):
            r = ann_to_raw.get(a)
            print(f"    [配对] 标注图 {a.name}  ←→  原图 {r.name if r else '?'}")
    return final, skipped


# ─────────────────────────────────────────────────────────── 跨集合近似重复
def dedup_pools(pos: list[Path], neg: list[Path], max_dhash: int = 6, audit: bool = False):
    """合并「正/负两个集合内部」与「跨集合」的近重复影像，返回 (pos, neg, 冲突明细)。

    为什么必须做：本机实测阴性参考集是**同一段 cine 的连续帧**（多张图字节几乎相同、
    dhash 距离 0~6），而且其中若干帧**同时以阳性身份出现在 demo 库里**
    （例如阳性 2c93e9a2…jpg 与阴性 18.jpg 字节完全相同）。
    这类数据会同时造成两种错：
      · 重复计数 → 置信区间假性变窄
      · 同一像素被标成两个相反标签 → 指标失去意义（模型不可能同时判对）

    处理规则（保守，不平白丢样本）：
      · 同一标签内的近重复 → 只保留一张（优先"已检出"的那张，便于看漏检）
      · **跨标签**的近重复 → 整组剔除（数据自相矛盾，留着只会让指标不可解释），
        并在冲突明细里列出，交由人工核对标签
    """
    fps = {}
    for f in list(pos) + list(neg):
        fp = fingerprint(f)
        if fp:
            fps[f] = fp

    parent = {f: f for f in fps}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    files = sorted(fps)
    for i, a in enumerate(files):
        fa = fps[a]
        for b in files[i + 1:]:
            fb = fps[b]
            if (fa["w"], fa["h"]) != (fb["w"], fb["h"]):
                continue
            if abs(fa["bytes"] - fb["bytes"]) > max(2048, 0.03 * max(fa["bytes"], fb["bytes"])):
                continue
            if _hamming(fa["d_full"], fb["d_full"]) <= max_dhash:
                union(a, b)

    groups: dict[Path, list[Path]] = {}
    for f in files:
        groups.setdefault(find(f), []).append(f)

    pos_set = set(pos)
    out_pos, out_neg, conflicts = [], [], []
    for members in groups.values():
        labels = {1 if m in pos_set else 0 for m in members}
        if len(labels) > 1:
            conflicts.append(sorted(members))
            continue
        keep = members[0] if len(members) == 1 else sorted(members, key=lambda f: (len(f.name), str(f)))[0]
        (out_pos if 1 in labels else out_neg).append(keep)

    if audit and conflicts:
        print(f"\n⚠️ 发现 {len(conflicts)} 组「同一影像被同时标为阳性与阴性」→ 已整组剔除：")
        for grp in conflicts:
            print("    " + "  |  ".join(f"{p.name}" for p in grp))
    if audit:
        for f in sorted(out_pos):
            same = [g for g in groups.values() if f in g and len(g) > 1]
            if same:
                print(f"    [合并-阳性] 保留 {f.name}（同源 {len(same[0]) - 1} 张）")
    return sorted(out_pos), sorted(out_neg), conflicts


# ─────────────────────────────────────────────────────────── 打分
def score_one(path: Path):
    """按生产路径打分：多帧取最佳帧；同时取证据分与 box_conf（原始框置信度）。"""
    frames = model_core.to_bgr_frames(load_image(path))
    best = None
    for fr in frames:
        out = model_core.score_image(fr)
        if best is None or out["score"] > best[1]["score"]:
            best = (fr, out)
    if best is None:
        return None
    frame, out = best
    black = model_core.black_ratio(frame)
    cls, conf, _, _ = model_core.decide(out["score"], out["threshold"], frame)
    return {
        "score": float(out["score"]),
        "box_conf": float(out["box_conf"]),
        "black": float(black),
        "decision": cls,
        "display_conf": float(conf),
        "box_conf_any": float(out["box_conf"]) > 0.0,
    }


# ─────────────────────────────────────────────────────────── 统计
def wilson(k: int, n: int, z: float = 1.96):
    """二项比例的 Wilson 95% 区间（小样本比正态近似稳，也不会越界）。"""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fmt_pct(v):
    return "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v * 100:.1f}%"


def ci_str(k, n):
    lo, hi = wilson(k, n)
    return f"[{fmt_pct(lo)}, {fmt_pct(hi)}]"


def metrics(rows, thr):
    tp = sum(1 for r in rows if r["label"] == 1 and r["pred_at"](thr))
    fp = sum(1 for r in rows if r["label"] == 0 and r["pred_at"](thr))
    fn = sum(1 for r in rows if r["label"] == 1 and not r["pred_at"](thr))
    tn = sum(1 for r in rows if r["label"] == 0 and not r["pred_at"](thr))
    return tp, fp, fn, tn


def auc(scores, labels):
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    pos, neg = scores[labels == 1], scores[labels == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    s = scores[order]
    ranks = np.empty(len(s), float)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return float((ranks[labels == 1].sum() - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def main() -> int:
    try:                                   # Windows 控制台默认 GBK，中文会乱码
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--pos", nargs="+", required=True)
    ap.add_argument("--neg", nargs="+", required=True)
    ap.add_argument("--exclude", nargs="*", default=[], help="排除的文件名/相对路径 glob，如 result_*")
    ap.add_argument("--exclude-dir", nargs="*", default=["results"], help="排除的目录名，默认 results")
    ap.add_argument("--csv", default="eval_confidence.csv")
    ap.add_argument("--min-bin", type=int, default=5, help="分箱最小样本数，低于则并入相邻档")
    ap.add_argument("--audit", action="store_true", help="打印「标注图 ←→ 原图」配对明细，便于人工复核")
    ap.add_argument("--dup-dhash", type=int, default=6,
                    help="同一标签内 dhash ≤ 此值的近重复只留一张；正负冲突组整组剔除（0=关闭）")
    args = ap.parse_args()

    print("=" * 92)
    print("证据分 → 置信度 诊断（不改部署常量，只出结论与建议表）")
    print("=" * 92)

    pos, pos_skip = collect(args.pos, args.exclude, args.exclude_dir, audit=args.audit)
    neg, neg_skip = collect(args.neg, args.exclude, args.exclude_dir, audit=args.audit)
    for tag, sk in (("正样本", pos_skip), ("负样本", neg_skip)):
        if sk:
            from collections import Counter
            c = Counter(why for _, why in sk)
            print(f"{tag}排除 {len(sk)} 张：{dict(c)}")

    # 跨集合近似重复 / 正负标签冲突
    conflicts = []
    if args.dup_dhash > 0:
        before = (len(pos), len(neg))
        pos, neg, conflicts = dedup_pools(pos, neg, args.dup_dhash, audit=args.audit)
        if before != (len(pos), len(neg)):
            print(f"近重复合并（dhash ≤ {args.dup_dhash}）：阳性 {before[0]}→{len(pos)} 张，"
                  f"阴性 {before[1]}→{len(neg)} 张")

    thr = float(model_core.POLICIES[model_core.POLICY]["threshold"])
    print(f"\n策略 {model_core.POLICY} v{model_core.POLICIES[model_core.POLICY]['version']}"
          f"  部署阈值={thr}  融合={model_core.POLICIES[model_core.POLICY]['fusion']}")
    print(f"评测集：阳性 {len(pos)} 张 / 阴性 {len(neg)} 张（剔除标注图·截图·重复后）")

    rows = []
    for label, group in ((1, pos), (0, neg)):
        for p in group:
            d = score_one(p)
            if d is None:
                continue
            d.update({"label": label, "name": p.name, "path": str(p),
                      "pred_at": (lambda t, s=d["score"]: s >= t)})
            rows.append(d)

    npos = sum(1 for r in rows if r["label"] == 1)
    nneg = sum(1 for r in rows if r["label"] == 0)

    # ── 1) 准确率（点估计 + Wilson 区间） ──────────────────────────────
    tp, fp, fn, tn = metrics(rows, thr)
    print("\n【1】部署阈值下的准确率")
    print(f"  混淆矩阵 TP={tp} FP={fp} FN={fn} TN={tn}")
    sens = (tp, tp + fn)
    spec = (tn, tn + fp)
    ppv = (tp, tp + fp)
    npv = (tn, tn + fn)
    acc = (tp + tn, tp + fp + fn + tn)
    print(f"  {'指标':<16}{'点估计':>9}   {'Wilson 95%':<20}")
    for name, (k, n) in [("敏感性(召回)", sens), ("特异性", spec), ("精确率 PPV", ppv),
                         ("NPV", npv), ("准确率", acc)]:
        print(f"  {name:<16}{fmt_pct(k / n if n else float('nan')):>9}   {ci_str(k, n):<20}")
    a = auc([r["score"] for r in rows], [r["label"] for r in rows])
    print(f"  {'ROC-AUC':<16}{a:>9.4f}   （20 张阴性→0.0，故 AUC 对负样本噪声极敏感）")

    # ── 2) 分数是不是"二值"的 ─────────────────────────────────────────
    pos_zero = sum(1 for r in rows if r["label"] == 1 and r["score"] == 0.0)
    neg_zero = sum(1 for r in rows if r["label"] == 0 and r["score"] == 0.0)
    pos_anybox = sum(1 for r in rows if r["label"] == 1 and r["box_conf_any"])
    neg_anybox = sum(1 for r in rows if r["label"] == 0 and r["box_conf_any"])
    print("\n【2】证据分的分布形态（决定「置信度」能有多细）")
    print(f"  阳性 证据分==0：{pos_zero}/{npos}   阴性 证据分==0：{neg_zero}/{nneg}")
    print(f"  阳性 至少检出一个框(box_conf>0)：{pos_anybox}/{npos}"
          f"   阴性：{neg_anybox}/{nneg}")
    print("  读法：若阴性几乎全 0、阳性也有相当比例 0，则分数是近似二值的；")
    print("        此时「置信度」只有「有没有检出」两档，任何小数位都是假精度。")

    # ── 3) 经验可靠性曲线 vs 现有标定表 ───────────────────────────────
    print("\n【3】经验阳性率 vs 现有标定表（可靠性曲线）")
    print(f"  {'证据分区间':<20}{'n':>4}{'实测阳性率':>12}{'Wilson 95%':<18}{'标定表':>9}{'差':>8}")
    edges = [0.0, 1e-9, 0.014451, 0.05, 0.2, 0.5, 1.01]
    ece_num, ece_den = 0.0, 0
    for lo, hi in zip(edges[:-1], edges[1:]):
        if lo == 0.0 and hi == 1e-9:
            sel = [r for r in rows if r["score"] == 0.0]
        else:
            sel = [r for r in rows if lo <= r["score"] < hi]
        if not sel:
            continue
        k = sum(r["label"] for r in sel)
        rate = k / len(sel)
        mid = (lo + hi) / 2
        table = model_core.calibrate_positive(max(mid, thr))
        gap = rate - table
        print(f"  [{lo:<8.6g},{hi:<8.6g}){len(sel):>4}{fmt_pct(rate):>12}   {ci_str(k, len(sel)):<18}"
              f"{fmt_pct(table):>9}{gap * 100:>7.1f}pp")
        ece_num += abs(gap) * len(sel)
        ece_den += len(sel)
    print(f"  ECE（加权 |实测-标定|）= {ece_num / ece_den * 100:.1f}pp  "
          f"（>10pp 就说明标定表在这份数据上不成立）")

    # ── 4) 阴性侧：0 分档的 NPV ───────────────────────────────────────
    neg0 = [r for r in rows if r["label"] == 0 and r["score"] < thr]
    pos0 = [r for r in rows if r["label"] == 1 and r["score"] < thr]
    print("\n【4】「判阴性」这一侧的可信度")
    print(f"  分数<阈值共 {len(neg0) + len(pos0)} 张：其中真阴性 {len(neg0)}，假阴性 {len(pos0)}")
    print(f"  阴性预测值 NPV = {fmt_pct(len(neg0) / max(len(neg0) + len(pos0), 1))} "
          f"{ci_str(len(neg0), max(len(neg0) + len(pos0), 1))}"
          f"   ← 现有标定表在 0 分处给 {fmt_pct(model_core.calibrate_negative(0.0))}")

    # ── 5) 建议表（基于本次数据的分档经验精度） ───────────────────────
    print("\n【5】建议（基于本次数据；样本量 ≤ 3 位数的档位只能当占位）")
    ppv_v = ppv[0] / ppv[1] if ppv[1] else float("nan")
    npv_v = npv[0] / npv[1] if npv[1] else float("nan")
    print(f"  · 判阳性时的可信度 ≈ 精确率 {fmt_pct(ppv_v)} {ci_str(*ppv)}："
          f"报告里写「参考精度」应取这个数，而不是标定表的 0.9485")
    print(f"  · 判阴性时的可信度 ≈ NPV {fmt_pct(npv_v)} {ci_str(*npv)}")
    print("  · 想给出更细的分档，必须补正/负样本：每档至少 30~50 张，否则不要展示小数位")
    print("  · 跨来源（不同设备/截图方式）时标定会漂移：本工具建议每个来源各跑一次，看 ECE")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["name", "label", "score", "box_conf", "black_ratio", "decision",
                        "display_conf", "path"])
            for r in rows:
                w.writerow([r["name"], r["label"], f"{r['score']:.6f}", f"{r['box_conf']:.4f}",
                            f"{r['black']:.4f}", r["decision"], f"{r['display_conf']:.4f}", r["path"]])
        print(f"\n逐图明细已保存：{args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
