# -*- coding: utf-8 -*-
"""去标识裁剪（手动 / 自动）接口测试。

自动裁剪不加载真实 YOLO 权重：monkeypatch `algorithm.auto_crop.auto_crop`，
只验证平台侧的编排逻辑（写盘、元数据、审计、权限、旧结果清理）。
"""
import io
import os

import numpy as np
import pytest
from PIL import Image as PILImage


def _mk_patient(client, auth_headers):
    return client.post("/api/patients", json={"name": "T", "gender": "Male", "age": 12},
                       headers=auth_headers).json()["id"]


def _real_jpg(width=300, height=200):
    """生成一张可被 PIL 解码的真 JPEG（300×200），避免用 1×1 假图裁不了。"""
    im = PILImage.new("RGB", (width, height), (30, 60, 90))
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    buf.seek(0)
    return buf, "crop-test.jpg"


def _upload(client, auth_headers, pid, auto_crop=False):
    f, fn = _real_jpg()
    data = {"patient_id": str(pid)}
    if auto_crop:
        data["auto_crop"] = "true"
    resp = client.post("/api/images/upload",
                       files={"file": (fn, f, "image/jpeg")},
                       data=data, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# 手动裁剪
# --------------------------------------------------------------------------- #
def test_manual_crop_ok(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "manual", "box": [10, 10, 290, 190]},
                       headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["applied"] is True
    assert body["box"] == [10, 10, 290, 190]
    # 裁剪后文件应真的是 280×180
    info = client.get(f"/api/images/{img['id']}/info", headers=auth_headers).json()
    assert info["crop_mode"] == "manual"
    assert info["crop_box"] == [10, 10, 290, 190]
    from config import UPLOAD_DIR  # noqa: F401  # 路径断言走接口即可
    img_bytes = client.get(f"/api/images/{img['id']}", headers=auth_headers).content
    with PILImage.open(io.BytesIO(img_bytes)) as im:
        assert im.size == (280, 180)


def test_manual_crop_bad_box(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "manual", "box": [200, 10, 100, 190]},
                       headers=auth_headers)
    assert resp.status_code == 400


def test_manual_crop_requires_box(client, auth_headers):
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "manual"}, headers=auth_headers)
    assert resp.status_code == 400


def test_crop_permission(client, auth_headers, second_doctor_headers):
    """别的医生不能裁剪不属于自己上传的影像。"""
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "manual", "box": [10, 10, 290, 190]},
                       headers=second_doctor_headers)
    assert resp.status_code == 403


def test_crop_drops_stale_detection_result(client, auth_headers):
    """已有检测结果的影像被裁剪后，旧结果应被删除（不再对应存储像素）。"""
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    det = client.post(f"/api/images/{img['id']}/detect", headers=auth_headers)
    assert det.status_code == 200
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "manual", "box": [10, 10, 290, 190]},
                       headers=auth_headers)
    assert resp.status_code == 200
    info = client.get(f"/api/images/{img['id']}/info", headers=auth_headers).json()
    assert info["has_result"] is False


# --------------------------------------------------------------------------- #
# 自动裁剪（mock 模型）
# --------------------------------------------------------------------------- #
@pytest.fixture
def fake_auto_crop(monkeypatch):
    """把 auto_crop 模型替换成确定性的假实现：固定框 (20,15)-(260,185)。"""
    def _fake(src, return_box=False, return_meta=False):
        with PILImage.open(str(src)) as im:
            arr = np.asarray(im.convert("RGB"))
        crop = arr[15:185, 20:260]
        meta = {"box": [20, 15, 260, 185], "size": [arr.shape[1], arr.shape[0]],
                "area": 0.7, "detected": True, "ms": 12.3}
        return (crop, meta)
    from algorithm import auto_crop as auto_crop_module
    monkeypatch.setattr(auto_crop_module, "auto_crop", _fake)
    return _fake


def test_auto_crop_endpoint(client, auth_headers, fake_auto_crop):
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "auto"}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["applied"] is True and body["detected"] is True
    assert body["box"] == [20, 15, 260, 185]
    info = client.get(f"/api/images/{img['id']}/info", headers=auth_headers).json()
    assert info["crop_mode"] == "auto"


def test_auto_crop_not_detected_keeps_original(client, auth_headers, monkeypatch):
    """模型检不到目标 → 保留原图，applied=False。"""
    def _fake(src, return_box=False, return_meta=False):
        with PILImage.open(str(src)) as im:
            arr = np.asarray(im.convert("RGB"))
        meta = {"box": None, "size": [arr.shape[1], arr.shape[0]],
                "area": 1.0, "detected": False, "ms": 5.0}
        return arr, meta
    from algorithm import auto_crop as auto_crop_module
    monkeypatch.setattr(auto_crop_module, "auto_crop", _fake)

    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid)
    resp = client.post(f"/api/images/{img['id']}/crop",
                       json={"mode": "auto"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["applied"] is False and body["detected"] is False
    # 原图未被改动
    img_bytes = client.get(f"/api/images/{img['id']}", headers=auth_headers).content
    with PILImage.open(io.BytesIO(img_bytes)) as im:
        assert im.size == (300, 200)
    info = client.get(f"/api/images/{img['id']}/info", headers=auth_headers).json()
    assert info["crop_mode"] is None


def test_upload_with_auto_crop(client, auth_headers, fake_auto_crop):
    """上传时带 auto_crop=true：保存后立刻去标识，响应里带元信息。"""
    pid = _mk_patient(client, auth_headers)
    img = _upload(client, auth_headers, pid, auto_crop=True)
    assert img["auto_crop_meta"]["applied"] is True
    assert img["crop_mode"] == "auto"
    img_bytes = client.get(f"/api/images/{img['id']}", headers=auth_headers).content
    with PILImage.open(io.BytesIO(img_bytes)) as im:
        assert im.size == (240, 170)          # 300×200 → 假模型框 (20,15)-(260,185)


def test_upload_auto_crop_failure_not_fatal(client, auth_headers, monkeypatch):
    """上传时自动裁剪失败（如 DICOM/依赖缺失）不阻断上传。"""
    pid = _mk_patient(client, auth_headers)
    # 用一个内容合法但后缀为 dcm 的场景太绕；直接让假模型抛错验证降级路径
    def _boom(src, return_box=False, return_meta=False):
        raise RuntimeError("model broken")
    from algorithm import auto_crop as auto_crop_module
    monkeypatch.setattr(auto_crop_module, "auto_crop", _boom)
    img = _upload(client, auth_headers, pid, auto_crop=True)
    assert img["id"]
    assert img["auto_crop_meta"]["applied"] is False
    assert "error" in img["auto_crop_meta"]
