# -*- coding: utf-8 -*-
"""auto_crop —— B 超整帧「去用户信息」自动裁剪的唯一接口。

    from auto_crop import auto_crop
    crop = auto_crop("图片.jpg")                 # → BGR ndarray（只保留中间超声图像区）
    crop, box = auto_crop("图片.jpg", return_box=True)

    python auto_crop.py --input <图片或目录> --out <输出目录>

设计取舍（都已由实测裁定，接口层不再暴露开关）：

* **只保留方案 B（YOLOv8n）**：用户目视确认其裁剪行为即为期望口径；
  在排除教师退化样本的公平子集上 IoU 0.935 / acc@0.8 0.924，独立留出 65 张 IoU 0.923。
* **不做「过裁兜底」**：早期把面积≈0.09 误判为过裁，复核发现那些图内容本来就小
  （模型与教师框 IoU 0.92–0.98），兜底反而会把正确的小裁剪放大并把 UI 带回来。
* **不做「版式补裁」**：两种规则解都不成立（一个退化成≈整幅＝指标套利，一个会撑到画面边缘）。
* 已裁剪过的 ROI 直接幂等（实测 IoU 0.994），调用方无需判断输入类型。
* 检不到目标时返回**原图**并在元信息里标 `detected=False`，不猜。

依赖：ultralytics、opencv-python、numpy（权重见 `_WEIGHTS`）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
_ROOT = Path(__file__).resolve().parent
# 交付权重名：autocrop-v1.pt（不带架构名，沿用平台 <任务>-v<版本>.pt 约定）。按序回退，使同一个文件在两种布局下都能直接运行：
#   ① 与 auto_crop.py 同目录（独立分发）      → autocrop-v1.pt
#   ② 平台后端算法目录 + weights/ 子目录       → weights/autocrop-v1.pt
#   ③ 本仓库训练/实验产物的原始位置（便于在实验环境里直接跑）
_WEIGHTS_CANDIDATES = [
    _ROOT / "autocrop-v1.pt",
    _ROOT / "weights" / "autocrop-v1.pt",
    _ROOT / "crop_runs" / "B_yolo" / "train" / "weights" / "best.pt",
]
_IMGSZ = 320          # 与权重训练时一致
_CONF = 0.01
_IOU = 0.7
_IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

_MODEL = None


def weights_path() -> Path:
    """返回实际使用的权重路径（按候选顺序回退）。"""
    for p in _WEIGHTS_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "找不到权重，请把 autocrop-v1.pt 与 auto_crop.py 放在同一目录。已尝试："
        + " / ".join(str(p) for p in _WEIGHTS_CANDIDATES))


def _model():
    """惰性加载并缓存模型（进程内只加载一次）。"""
    global _MODEL
    if _MODEL is None:
        from ultralytics import YOLO
        _MODEL = YOLO(str(weights_path()))
    return _MODEL


# --------------------------------------------------------------------------- #
# 图像读写（兼容中文/非 ASCII 路径）
# --------------------------------------------------------------------------- #
def _imread(src) -> np.ndarray:
    """str/Path → BGR ndarray；ndarray/PIL 原样转换。"""
    if isinstance(src, np.ndarray):
        im = src
        if im.ndim == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        return np.ascontiguousarray(im[:, :, :3])
    if hasattr(src, "convert"):                       # PIL.Image
        return cv2.cvtColor(np.asarray(src.convert("RGB")), cv2.COLOR_RGB2BGR)
    buf = np.fromfile(str(src), dtype=np.uint8)
    im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if im is None:
        raise ValueError(f"无法读取图片：{src}")
    return im


def _imwrite(dst, im: np.ndarray, quality: int = 95) -> None:
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    ext = dst.suffix.lower() or ".jpg"
    params = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)] if ext in (".jpg", ".jpeg") else []
    ok, buf = cv2.imencode(ext, im, params)
    if not ok:
        raise ValueError(f"无法编码：{dst}")
    buf.tofile(str(dst))


# --------------------------------------------------------------------------- #
# 唯一接口
# --------------------------------------------------------------------------- #
def auto_crop(src, return_box: bool = False, return_meta: bool = False):
    """去掉 B 超整帧截图中的用户信息（顶栏/参数栏/刻度条），只保留中间的超声图像区。

    参数
    ----
    src : str | Path | np.ndarray(BGR) | PIL.Image
        输入图片。
    return_box : bool
        同时返回裁剪框 `[x0, y0, x1, y1]`（原图坐标，x1/y1 为开区间）。
    return_meta : bool
        额外返回元信息 dict：`{"box", "size", "area", "detected", "ms"}`。

    返回
    ----
    crop : np.ndarray(BGR)
        裁剪结果；检不到目标时为**原图**（`meta["detected"] is False`）。
    box / meta : 仅在对应开关为 True 时作为额外返回值。
    """
    import time
    t0 = time.time()
    im = _imread(src)
    H, W = im.shape[:2]

    res = _model().predict(im, imgsz=_IMGSZ, conf=_CONF, iou=_IOU, verbose=False, max_det=10)[0]
    detected = res.boxes is not None and len(res.boxes) > 0
    if detected:
        xyxy = res.boxes.xyxy.cpu().numpy()
        conf = res.boxes.conf.cpu().numpy()
        box = [float(v) for v in xyxy[int(np.argmax(conf))]]
    else:
        box = [0.0, 0.0, float(W), float(H)]

    x0 = max(0, min(int(round(box[0])), W - 1))
    y0 = max(0, min(int(round(box[1])), H - 1))
    x1 = max(x0 + 1, min(int(round(box[2])), W))
    y1 = max(y0 + 1, min(int(round(box[3])), H))
    crop = im[y0:y1, x0:x1]
    if crop.size == 0:                                # 兜底：不退化成空图
        crop, x0, y0, x1, y1, detected = im, 0, 0, W, H, False

    out = [crop]
    if return_box:
        out.append([x0, y0, x1, y1])
    if return_meta:
        out.append({"box": [x0, y0, x1, y1], "size": [W, H],
                    "area": round((x1 - x0) * (y1 - y0) / max(1, W * H), 4),
                    "detected": bool(detected), "ms": round((time.time() - t0) * 1000, 1)})
    return out[0] if len(out) == 1 else tuple(out)


def crop_file(src, dst, quality: int = 95, return_meta: bool = False):
    """裁剪单张图片并写盘。返回元信息 dict。"""
    crop, meta = auto_crop(src, return_meta=True)
    _imwrite(dst, crop, quality=quality)
    meta["src"], meta["dst"] = str(src), str(dst)
    return meta if return_meta else meta


def crop_dir(src_dir, dst_dir, recursive: bool = False, quality: int = 95,
             preview: bool = False, verbose: bool = True) -> dict:
    """批量裁剪目录。返回汇总 dict（含逐张元信息）。"""
    import json
    import time
    src_dir, dst_dir = Path(src_dir), Path(dst_dir)
    it = src_dir.rglob("*") if recursive else src_dir.glob("*")
    files = sorted(p for p in it if p.is_file() and p.suffix.lower() in _IMG_EXT)
    if not files:
        raise FileNotFoundError(f"目录下没有图片：{src_dir}")

    (dst_dir / "images").mkdir(parents=True, exist_ok=True)
    if preview:
        (dst_dir / "preview").mkdir(parents=True, exist_ok=True)

    t0, records, failed = time.time(), {}, []
    for i, p in enumerate(files, 1):
        try:
            im = _imread(p)
            crop, meta = auto_crop(im, return_meta=True)
            _imwrite(dst_dir / "images" / (p.stem + ".jpg"), crop, quality=quality)
            if preview:
                vis = im.copy()
                b = meta["box"]
                cv2.rectangle(vis, (b[0], b[1]), (b[2] - 1, b[3] - 1), (0, 0, 255), 2)
                h = 330
                v = cv2.resize(vis, (int(vis.shape[1] * h / vis.shape[0]), h))
                c = cv2.resize(crop, (int(crop.shape[1] * h / crop.shape[0]), h))
                sheet = np.zeros((h, v.shape[1] + c.shape[1] + 8, 3), np.uint8)
                sheet[:, :v.shape[1]] = v
                sheet[:, v.shape[1] + 8:v.shape[1] + 8 + c.shape[1]] = c
                _imwrite(dst_dir / "preview" / (p.stem + ".png"), sheet)
            records[str(p)] = {"box": meta["box"], "size": meta["size"],
                               "area": meta["area"], "detected": meta["detected"]}
        except Exception as e:                        # 单张失败不影响整批
            failed.append({"file": str(p), "error": f"{type(e).__name__}: {e}"})
        if verbose and (i % 50 == 0 or i == len(files)):
            print(f"[auto_crop] {i}/{len(files)}  {time.time()-t0:.1f}s", flush=True)

    sec = time.time() - t0
    summary = {"input": str(src_dir), "output": str(dst_dir), "n": len(records),
               "failed": failed, "seconds": round(sec, 1),
               "ms_per_image": round(1000 * sec / max(1, len(records)), 1),
               "n_not_detected": sum(1 for r in records.values() if not r["detected"]),
               "records": records}
    with open(dst_dir / "boxes.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    if verbose:
        print(f"[auto_crop] 完成 {len(records)}/{len(files)} 张，用时 {sec:.1f}s "
              f"({summary['ms_per_image']} ms/张) → {dst_dir}")
    return summary


# --------------------------------------------------------------------------- #
# CLI（同一个接口的命令行形式）
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="B 超整帧自动裁剪：去掉用户信息，只保留中间的超声图像区")
    ap.add_argument("--input", required=True, help="图片文件或目录")
    ap.add_argument("--out", required=True, help="输出文件或目录")
    ap.add_argument("--recursive", action="store_true", help="目录输入时递归子目录")
    ap.add_argument("--quality", type=int, default=95, help="JPEG 质量（默认 95）")
    ap.add_argument("--preview", action="store_true", help="额外输出 原图+裁剪 对照图")
    ap.add_argument("--boxes-only", action="store_true", help="只算框不写裁剪图（仅目录输入）")
    a = ap.parse_args(argv)

    src = Path(a.input)
    if src.is_file():
        meta = crop_file(src, a.out, quality=a.quality, return_meta=True)
        print(f"[auto_crop] {src.name} → {a.out}  box={meta['box']} area={meta['area']} "
              f"detected={meta['detected']} {meta['ms']}ms")
        return 0
    if not src.is_dir():
        print(f"[auto_crop] 输入不存在：{src}")
        return 1
    if a.boxes_only:
        it = src.rglob("*") if a.recursive else src.glob("*")
        files = sorted(p for p in it if p.is_file() and p.suffix.lower() in _IMG_EXT)
        import json
        out = {}
        for p in files:
            _, meta = auto_crop(p, return_meta=True)
            out[str(p)] = meta
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump({"n": len(out), "boxes": out}, fh, ensure_ascii=False, indent=1)
        print(f"[auto_crop] 只算框：{len(out)} 张 → {a.out}")
        return 0
    crop_dir(src, a.out, recursive=a.recursive, quality=a.quality, preview=a.preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())

