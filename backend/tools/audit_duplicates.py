"""核实 demo 库里的重复到底是什么：逐对比较尺寸 / 长宽比 / 像素相似度

背景：`eval_labeled.py` 只按**文件字节 MD5** 去重，于是下列三种情况分不开：
  1. 同一张图上传两次（文件名不同、字节相同或近似）→ 应当合并
  2. 同一张图的**原始上传**与**AI 标注输出**（result_NN_<md5>.jpg，画了红框、重新编码）
     → 字节不同，应当合并（否则等于让模型给"我们自己画了框的图"打分）
  3. 真正的两张不同阳片 → 不应合并，否则漏计

本脚本并列打印候选配对证据，人来判（不做自动决定）。

用法（backend 目录下）：
    .\\venv\\Scripts\\python.exe tools\\audit_duplicates.py --pos ..\\uploads
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def fingerprint(f: Path):
    """尺寸 + 缩略图哈希（dhash 64bit）+ 平均亮度：用于跨编码/跨标注的相似判定。"""
    img = Image.open(f).convert("L")
    w, h = img.size
    small = np.asarray(img.resize((8, 8), Image.LANCZOS), dtype=np.float64)
    bits = (small > small.mean()).ravel()
    val = 0
    for b in bits:
        val = (val << 1) | int(b)
    return {"w": w, "h": h, "dhash": val, "mean": float(small.mean()), "size": f.stat().st_size}


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--pos", nargs="+", required=True)
    ap.add_argument("--max-dist", type=int, default=12, help="dhash 距离阈值，超过则不列为候选")
    args = ap.parse_args()

    files = []
    for d in args.pos:
        p = Path(d)
        files += [x for x in sorted(p.rglob("*")) if x.suffix.lower() in EXTS]
    fps = {}
    for f in files:
        try:
            fps[f] = fingerprint(f)
        except Exception:
            pass

    print(f"共 {len(fps)} 张图，逐对比较（dhash 距离 ≤ {args.max_dist} 才列出）")
    print("=" * 108)
    print(f"{'A':<50}{'B':<50}{'dhash':>6}{'尺寸':>12}{'亮度差':>8}")
    print("-" * 108)

    pairs = []
    for a, b in itertools.combinations(fps, 2):
        fa, fb = fps[a], fps[b]
        d = hamming(fa["dhash"], fb["dhash"])
        if d <= args.max_dist:
            pairs.append((d, a, b, fa, fb))
    pairs.sort()

    for d, a, b, fa, fb in pairs:
        same_bytes = hashlib.md5(a.read_bytes()).hexdigest() == hashlib.md5(b.read_bytes()).hexdigest()
        tag = "字节相同" if same_bytes else ("尺寸相同" if (fa["w"], fa["h"]) == (fb["w"], fb["h"]) else "尺寸不同")
        dims = f"{fa['w']}x{fa['h']}/{fb['w']}x{fb['h']}"
        print(f"{a.name[:48]:<50}{b.name[:48]:<50}{d:>6}{dims:>12}"
              f"{abs(fa['mean'] - fb['mean']):>8.1f}  {tag}")

    print("-" * 108)
    same_n = sum(1 for _, a, b, _, _ in pairs
                 if hashlib.md5(a.read_bytes()).hexdigest() == hashlib.md5(b.read_bytes()).hexdigest())
    print(f"候选重复对：{len(pairs)} 对（其中字节完全相同 {same_n} 对）")
    print("判读：dhash ≤6 且尺寸相同 → 几乎确定是同一张（含「原图 vs 标注图」）；")
    print("      dhash ≥9 → 不同影像，不要合并。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
