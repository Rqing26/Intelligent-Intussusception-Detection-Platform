"""影子数据回填（推荐方式）
==============================

**为什么不走"请求内实时影子"**

实时影子（``shadow.SHADOW_ENABLED=True``）虽然只入队、不阻塞，但后台 worker 的
v2 融合推理 = 8 个模型，会和请求抢 CPU。本地 A/B 实测（Ryzen 7 5700U，CPU 推理）：

    影子关闭：请求中位 1057 ms
    影子开启：请求中位 2217 ms      → 拖慢 2.1×
    限速 3/min：仍然 +1156 ms       → 限速只降频率，不降单次争用

因此**默认关闭实时影子**，改用本脚本对**已存盘的影像**做批量回填：
零延迟影响、可随时中断/续跑、也不需要服务在线。

**用法**

    # 回填平台已上传的全部影像（默认目录取自 backend/config.py 的 UPLOAD_DIR）
    python -m algorithm.backfill_shadow

    # 指定目录、限量试跑
    python -m algorithm.backfill_shadow --images D:\\some\\images --limit 20

    # 若整批图已知都是阴性（例如正常样本池），可顺手打标，省掉人工标注
    python -m algorithm.backfill_shadow --images D:\\normal --assume-label 0

    # 看进度 / ETA
    python -m algorithm.backfill_shadow --status

回填记录与实时影子写入**同一个** ``shadow_data/shadow.jsonl``（按图像 md5 去重、可续跑），
因此 ``calibrate_shadow.py`` 不需要任何改动。

建议用 Windows 计划任务 / cron 每晚跑一次；影像只会越攒越多，而标定只需要无偏负样本。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402

from algorithm import model_core, shadow  # noqa: E402

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".dcm")


def default_upload_dir() -> Path:
    try:
        sys.path.insert(0, str(BACKEND))
        from config import UPLOAD_DIR  # type: ignore
        return Path(UPLOAD_DIR)
    except Exception:
        return BACKEND.parent / "uploads"


def load_done() -> set:
    p = shadow.SHADOW_DIR / "shadow.jsonl"
    done = set()
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["md5"])
            except Exception:
                continue
    return done


# --------------------------------------------------------------------------------------
# 「样本内」护栏：影子数据必须是**模型训练时没见过、且未用于评测**的影像，否则标定无意义
# --------------------------------------------------------------------------------------
# 两类都要排除：
#   ① 训练语料 —— 模型见过，候选策略分数被系统性压低，据此定阈值会偏低；
#   ② 留出测试集 —— 模型没见过，但它是评测基准，拿它标定等于测试集调参。
# 可用 --corpus-dirs / --heldout-dirs 覆盖。
# 注意 normal/ 也列入排除：599 张里有 450 张被用作训练负样本（约 75% 受污染），
# 而"按内容 md5 排除"无法区分哪些是训练用的，故整目录保守排除 —— 宁可少采，不可采脏。
DEFAULT_CORPUS_DIRS = ("成功横断面", "失败横断面", "成功纵切面", "失败纵切面", "normal")
DEFAULT_HELDOUT_DIRS = ("test190_new",)


# 近似重复阈值：16x16 灰度描述子的平均绝对差。
# 实测依据（见 p28 文档）：
#   · 同一张图轻量重编码（改 JPEG 质量/格式）  -> 0.00021   ← 必须拦下，但精确 md5 拦不住
#   · 语料内相邻文件（疑似同病例相邻帧）最小     -> 0.00061
#   · 随机不同图                              最小 -> 0.02278
# 取 0.0020：对"重编码变体"有约 10 倍余量，只会剔除近乎逐像素相同的帧。
NEAR_DUP_TOL = 0.0020
NEAR_DUP_SIZE = 16


def image_descriptor(bgr) -> "np.ndarray":
    """16x16 灰度描述子（归一化），用于识别"同一张图换了编码"的近似重复。"""
    import numpy as np
    import cv2
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    return (cv2.resize(g, (NEAR_DUP_SIZE, NEAR_DUP_SIZE),
                       interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0).ravel()


def corpus_md5_index(corpus_dirs=None, heldout_dirs=None) -> tuple:
    """返回 (训练语料 md5 集合, 留出 md5 集合, 训练语料描述子表, 留出描述子表)。

    结果缓存到 shadow_data/corpus_md5.pkl。
    说明：语料里存在"同一张图出现多次"的情况，按**内容** md5 比对，不依赖文件名；
    另存一份下采样描述子，用于识别"换了编码但内容相同"的近似重复 —— 实测精确 md5
    拦不住这种（同一张图改 JPEG 质量后 md5 就变了）。
    """
    import hashlib
    import numpy as np
    cache = shadow.SHADOW_DIR / "corpus_md5.pkl"
    if cache.exists():
        try:
            obj = pickle.load(open(cache, "rb"))
            if len(obj) == 4:                     # 新版：含描述子表
                tr, ho, trd, hod = obj
                return set(tr), set(ho), np.asarray(trd), np.asarray(hod)
        except Exception:
            pass
    from algorithm.pipeline import load_image

    def _scan(names):
        out, descs = set(), []
        for d in names:
            p = Path(d)
            if p.is_absolute():
                cands = [p]
            else:
                # 语料不一定放在平台目录里：依次在平台根、平台的上一级（常见工作区布局）里找
                cands = [BACKEND.parent / d, BACKEND.parent.parent / d]
            root = next((c for c in cands if c.exists() and c.is_dir()), None)
            if root is None:
                continue
            for f in root.rglob("*"):
                if not f.is_file() or f.suffix.lower() not in IMG_EXTS:
                    continue
                try:
                    b = model_core.to_bgr(load_image(f))
                    if b is None:
                        continue
                    out.add(hashlib.md5(np.ascontiguousarray(b).tobytes()).hexdigest())
                    descs.append(image_descriptor(b))
                except Exception:
                    continue
        return out, (np.vstack(descs) if descs else np.zeros((0, NEAR_DUP_SIZE * NEAR_DUP_SIZE), np.float32))

    train, train_d = _scan(corpus_dirs or DEFAULT_CORPUS_DIRS)
    held, held_d = _scan(heldout_dirs if heldout_dirs is not None else DEFAULT_HELDOUT_DIRS)
    try:
        pickle.dump((train, held, train_d, held_d), open(cache, "wb"))
    except Exception:
        pass
    return train, held, train_d, held_d


def load_image_bgr(path: Path):
    from algorithm.pipeline import load_image
    try:
        return model_core.to_bgr(load_image(path))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", nargs="*", default=None, help="要回填的目录或文件（默认平台 UPLOAD_DIR）")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--policy", default=shadow.SHADOW_POLICY)
    ap.add_argument("--assume-label", choices=["0", "1"], default=None,
                    help="若整批图的真值已知（如全是阴性），直接写入 labels.csv")
    ap.add_argument("--corpus-dirs", nargs="*", default=None,
                    help="训练语料目录（用于排除样本内影像）；默认 4 个标注目录")
    ap.add_argument("--heldout-dirs", nargs="*", default=None,
                    help="留出测试集目录（也不能用于标定，否则等于测试集调参）；默认 test190_new")
    ap.add_argument("--keep-in-sample", action="store_true",
                    help="不做样本内排除（不推荐：样本内数据标定出的阈值会偏低）")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    shadow.SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    if shadow.SHADOW_SAVE_IMAGES:
        (shadow.SHADOW_DIR / "images").mkdir(parents=True, exist_ok=True)

    if a.status:
        done = load_done()
        p = shadow.SHADOW_DIR / "shadow.jsonl"
        print(f"影子数据目录 : {shadow.SHADOW_DIR}")
        print(f"已回填(去重) : {len(done)} 张")
        print(f"文件         : {p}  ({p.stat().st_size if p.exists() else 0} 字节)")
        lab = shadow.SHADOW_DIR / "labels.csv"
        if lab.exists():
            n = sum(1 for line in lab.read_text(encoding="utf-8-sig").splitlines()[1:] if line.strip())
            print(f"待标注清单   : {lab}  ({n} 行)")
        return 0

    roots = [Path(x) for x in (a.images or [default_upload_dir()])]
    files = []
    for r in roots:
        if r.is_dir():
            files += [f for f in sorted(r.rglob("*")) if f.is_file() and f.suffix.lower() in IMG_EXTS]
        elif r.exists():
            files.append(r)
    if not files:
        print(f"[提示] 没有找到影像。检查目录：{[str(r) for r in roots]}")
        return 2

    done = load_done()
    todo = []
    t0 = time.time()
    for f in files:
        if a.limit and len(todo) >= a.limit:
            break
        try:
            raw = f.read_bytes()
        except Exception:
            continue
        if hashlib.md5(raw).hexdigest() in done:       # 文件级去重（图片级 md5 在下方判断）
            pass
        todo.append(f)

    print(f"候选 {len(todo)} 张（已回填 {len(done)} 张）；策略 {a.policy}")
    from algorithm import classification  # noqa: F401  触发日志
    model_core._resolve(a.policy, enforce_deploy_guard=False)

    # ★ 样本内护栏：训练语料里出现过的影像不能用于标定（模型见过它们，分数被压低，
    #   据此定出的阈值会偏低）。命中即跳过，并在日志里明确说明。
    if a.keep_in_sample:
        corpus, heldout = set(), set()
        corpus_d = heldout_d = np.zeros((0, NEAR_DUP_SIZE * NEAR_DUP_SIZE), np.float32)
    else:
        corpus, heldout, corpus_d, heldout_d = corpus_md5_index(a.corpus_dirs, a.heldout_dirs)
    if corpus or heldout:
        print(f"排除清单：训练语料 {len(corpus)} 张、留出测试集 {len(heldout)} 张"
              f"（精确 md5 + 近似重复 双重比对，命中者跳过、不计入标定）")
    else:
        print("[提醒] 未找到训练语料/测试集目录，跳过排除 —— 若这些影像是模型见过或用于评测的，"
              "标定结果会失真，请确认数据来自部署后的新影像")

    def near_dup(bgr, descs) -> bool:
        """与排除清单里任何一张"近乎逐像素相同"则视为同一张（换编码也认得出）。"""
        if descs is None or len(descs) == 0:
            return False
        d = image_descriptor(bgr)
        return bool((np.abs(descs - d).mean(axis=1) <= NEAR_DUP_TOL).any())

    n_ok = n_skip = n_fail = n_in = n_ho = n_dup = 0
    labels = {}
    for i, f in enumerate(todo, 1):
        bgr = load_image_bgr(f)
        if bgr is None or min(bgr.shape[:2]) < model_core.MIN_SIDE:
            n_fail += 1
            continue
        key = hashlib.md5(np.ascontiguousarray(bgr).tobytes()).hexdigest()
        if key in done:
            n_skip += 1
            continue
        if key in corpus:
            n_in += 1
            continue                      # 训练语料里见过 → 不采集
        if key in heldout:
            n_ho += 1
            continue                      # 留出测试集 → 不能用于标定（会变成测试集调参）
        # 近似重复：同一张图换了编码/质量后 md5 会变，精确比对拦不住（实测差 0.685/255 就绕过）
        if near_dup(bgr, corpus_d):
            n_dup += 1
            continue
        if near_dup(bgr, heldout_d):
            n_dup += 1
            continue
        try:
            deployed = model_core.score_with(model_core.POLICY, bgr, enforce_deploy_guard=True)
            cand = model_core.score_with(a.policy, bgr, enforce_deploy_guard=False)
        except Exception as exc:
            n_fail += 1
            print(f"  [失败] {f.name}: {exc}")
            continue
        deployed_thr = float(model_core.POLICIES[model_core.POLICY]["threshold"])
        deployed_label = "肠套叠阳性" if deployed["score"] >= deployed_thr else "肠套叠阴性"
        if shadow.SHADOW_SAVE_IMAGES:
            p = shadow.SHADOW_DIR / "images" / f"{key}.jpg"
            if not p.exists():
                import cv2
                ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), shadow.SHADOW_JPEG_QUALITY])
                if ok:
                    buf.tofile(str(p))
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "md5": key, "h": int(bgr.shape[0]),
               "w": int(bgr.shape[1]), "black_ratio": round(model_core.black_ratio(bgr), 5),
               "deployed_score": round(float(deployed["score"]), 8), "deployed_label": deployed_label,
               "shadow_policy": a.policy, "shadow_version": cand["version"],
               "shadow_score": round(float(cand["score"]), 8),
               "shadow_threshold_placeholder": round(float(cand["threshold"]), 8),
               "in_sample": False,          # 已通过样本内护栏
               "image": f"images/{key}.jpg" if shadow.SHADOW_SAVE_IMAGES else None,
               "source": str(f)}
        with open(shadow.SHADOW_DIR / "shadow.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done.add(key)
        if a.assume_label is not None:
            labels[key] = int(a.assume_label)
        n_ok += 1
        if i % 25 == 0 or i == len(todo):
            el = time.time() - t0
            print(f"  {i}/{len(todo)}  成功{n_ok} 跳过{n_skip} 样本内剔除{n_in} "
                  f"测试集剔除{n_ho} 失败{n_fail}  "
                  f"{(el/i):.2f}s/张  ETA {(len(todo)-i)*el/i/60:.1f} min")

    if labels:
        lab_path = shadow.SHADOW_DIR / "labels.csv"
        exist = {}
        if lab_path.exists():
            with open(lab_path, encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    exist[row["md5"]] = row.get("label", "")
        exist.update({k: str(v) for k, v in labels.items()})
        with open(lab_path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh); w.writerow(["md5", "label"])
            for k, v in exist.items():
                w.writerow([k, v])
        print(f"已写入 {len(labels)} 条已知标签 -> {lab_path}")

    print(f"\n完成：新增 {n_ok}，跳过(已存在) {n_skip}，样本内剔除 {n_in}，测试集剔除 {n_ho}，"
          f"近重复剔除 {n_dup}，失败 {n_fail}，用时 {(time.time()-t0)/60:.1f} min")
    if n_in:
        print(f"  ※ {n_in} 张命中训练语料、已跳过：模型见过它们，据此标定会偏低")
    if n_ho:
        print(f"  ※ {n_ho} 张命中留出测试集、已跳过：拿评测集标定等于测试集调参")
    if n_dup:
        print(f"  ※ {n_dup} 张与排除清单里的影像近乎逐像素相同（换了编码/质量，md5 已变）")
    print(f"累计去重 {len(done)} 张。下一步：python -m algorithm.calibrate_shadow --export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
