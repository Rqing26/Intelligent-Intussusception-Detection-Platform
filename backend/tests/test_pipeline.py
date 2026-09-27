"""适配层（pipeline）测试：锁住 A/B 与平台的集成契约。

覆盖：
  1. 两个模块未就绪 → 自动回退 Mock（平台随时可用）
  2. 两个模块就绪 → 走真实流水线并正确组装 DetectionResult
  3. detect 返回 None → 按"全图送分类"处理
  4. 队友返回非法分类 → validate_result 兜底纠正
  5. 双模型溯源：A/B 的模型名、版本、分段耗时、检测置信度、病灶框
  6. 入口优先级：A/B 流水线 > team_model 融合模型 > Mock
"""
from pathlib import Path

import pytest

from algorithm import pipeline, detection, classification
from algorithm.contracts import ROI, ClassificationOutcome


@pytest.fixture
def no_team_model(monkeypatch):
    """屏蔽队友融合模型，保证测试只验证 Mock / A/B 两条路径。"""
    monkeypatch.setattr(pipeline, "is_team_model_ready", lambda: False)


def test_fallback_to_mock_when_not_ready(monkeypatch, no_team_model):
    """模块未就绪时，应回退到 Mock 且结果合法。"""
    monkeypatch.setattr(detection, "READY", False)
    monkeypatch.setattr(classification, "READY", False)
    assert pipeline.is_real_ready() is False

    result = pipeline.detect_intussusception(Path("not-used.jpg"))
    assert result.classification in {"肠套叠阳性", "肠套叠阴性", "图像质量不佳"}
    assert 0.0 <= float(result.confidence) <= 1.0


def test_real_pipeline_when_ready(monkeypatch):
    """两模块就绪时走真实流水线，并正确组装结果。"""
    monkeypatch.setattr(pipeline, "load_image", lambda p: "IMG")
    monkeypatch.setattr(detection, "READY", True)
    monkeypatch.setattr(classification, "READY", True)
    monkeypatch.setattr(detection, "detect", lambda img: ROI(image="ROI", box=(1, 2, 3, 4), score=0.9))
    monkeypatch.setattr(
        classification, "classify",
        lambda roi: ClassificationOutcome(
            classification="肠套叠阳性",
            confidence=0.88,
            severity="中度",
            treatment_success_rate=0.9,
            class_probabilities={"肠套叠阳性": 0.88, "肠套叠阴性": 0.07, "图像质量不佳": 0.05},
        ),
    )
    assert pipeline.is_real_ready() is True

    result = pipeline.detect_intussusception(Path("x.jpg"))
    assert result.classification == "肠套叠阳性"
    assert result.confidence == 0.88
    assert result.severity == "中度"
    assert result.treatment_success_rate == 0.9
    assert result.model_name == "team-pipeline"


def test_detect_none_means_full_image(monkeypatch):
    """detect 返回 None 时，适配层应把整张原图交给分类。"""
    monkeypatch.setattr(pipeline, "load_image", lambda p: "FULL_IMG")
    monkeypatch.setattr(detection, "READY", True)
    monkeypatch.setattr(classification, "READY", True)
    monkeypatch.setattr(detection, "detect", lambda img: None)

    captured = {}

    def fake_classify(roi):
        captured["roi"] = roi
        return ClassificationOutcome(classification="肠套叠阴性", confidence=0.7)

    monkeypatch.setattr(classification, "classify", fake_classify)

    result = pipeline.detect_intussusception(Path("x.jpg"))
    assert captured["roi"].image == "FULL_IMG"     # 收到的是全图
    assert captured["roi"].box is None
    assert result.classification == "肠套叠阴性"


def test_invalid_classification_is_corrected(monkeypatch):
    """队友返回非法分类时，validate_result 应兜底为「图像质量不佳」。"""
    monkeypatch.setattr(pipeline, "load_image", lambda p: "IMG")
    monkeypatch.setattr(detection, "READY", True)
    monkeypatch.setattr(classification, "READY", True)
    monkeypatch.setattr(detection, "detect", lambda img: ROI(image="ROI"))
    monkeypatch.setattr(
        classification, "classify",
        lambda roi: ClassificationOutcome(classification="随便写的分类", confidence=1.5),
    )

    result = pipeline.detect_intussusception(Path("x.jpg"))
    assert result.classification == "图像质量不佳"   # 非法分类被纠正
    assert result.confidence == 1.0                 # 越界置信度被收敛


def test_mock_leaves_model_slots_empty(monkeypatch, no_team_model):
    """Mock 是整条流水线的占位实现，不应伪造检测/分类模型名。"""
    monkeypatch.setattr(detection, "READY", False)
    monkeypatch.setattr(classification, "READY", False)

    result = pipeline.detect_intussusception(Path("not-used.jpg"))
    assert result.model_name == "Mock"
    assert result.detection_model_name == ""
    assert result.classification_model_name == ""
    assert result.detection_ms is None
    assert result.classification_ms is None


def test_real_pipeline_records_both_models(monkeypatch):
    """就绪时应分别记录 A/B 的模型名、版本、耗时，以及检测原始输出。"""
    monkeypatch.setattr(pipeline, "load_image", lambda p: "IMG")
    monkeypatch.setattr(detection, "READY", True)
    monkeypatch.setattr(classification, "READY", True)
    monkeypatch.setattr(detection, "NAME", "DetA")
    monkeypatch.setattr(detection, "VERSION", "1.2.3")
    monkeypatch.setattr(classification, "NAME", "ClsB")
    monkeypatch.setattr(classification, "VERSION", "2.0")
    monkeypatch.setattr(detection, "detect", lambda img: ROI(image="ROI", box=(10, 20, 30, 40), score=0.93))
    monkeypatch.setattr(
        classification, "classify",
        lambda roi: ClassificationOutcome(classification="肠套叠阳性", confidence=0.88),
    )

    result = pipeline.detect_intussusception(Path("x.jpg"))
    assert result.detection_model_name == "DetA"
    assert result.detection_model_version == "1.2.3"
    assert result.classification_model_name == "ClsB"
    assert result.classification_model_version == "2.0"
    assert result.detection_score == 0.93
    assert result.roi_box == (10, 20, 30, 40)
    assert result.detection_ms is not None and result.detection_ms >= 0
    assert result.classification_ms is not None and result.classification_ms >= 0
    assert result.model_name == "team-pipeline"      # 整体标签保留


def test_detection_model_recorded_even_when_no_roi(monkeypatch):
    """detect 返回 None（未检出病灶）时，仍要记下是哪个检测模型跑过。"""
    monkeypatch.setattr(pipeline, "load_image", lambda p: "FULL_IMG")
    monkeypatch.setattr(detection, "READY", True)
    monkeypatch.setattr(classification, "READY", True)
    monkeypatch.setattr(detection, "NAME", "DetA")
    monkeypatch.setattr(detection, "detect", lambda img: None)
    monkeypatch.setattr(
        classification, "classify",
        lambda roi: ClassificationOutcome(classification="肠套叠阴性", confidence=0.7),
    )

    result = pipeline.detect_intussusception(Path("x.jpg"))
    assert result.detection_model_name == "DetA"
    assert result.detection_score is None
    assert result.roi_box is None


def test_validate_result_sanitizes_model_metadata():
    """脏的模型元数据不应进入数据库：超长截断、非法耗时/框丢弃、置信度收敛。"""
    from algorithm.interface import DetectionResult, validate_result

    dirty = DetectionResult(
        classification="肠套叠阳性",
        confidence=0.9,
        detection_model_name="  " + "X" * 200 + "  ",
        detection_model_version="V" * 80,
        detection_ms=-5,
        classification_ms="abc",
        detection_score=1.7,
        roi_box=(1, 2, 3),
    )
    clean = validate_result(dirty)
    assert clean.detection_model_name == "X" * 100          # 限长到列宽
    assert clean.detection_model_version == "V" * 50
    assert clean.detection_ms is None                       # 负数耗时丢弃
    assert clean.classification_ms is None                  # 非数字耗时丢弃
    assert clean.detection_score == 1.0                     # 越界收敛
    assert clean.roi_box is None                            # 长度不对的框丢弃

    normalized = validate_result(DetectionResult(
        classification="肠套叠阳性", confidence=0.9,
        detection_ms=12.3456, roi_box=[1.9, 2.1, 3, 4],
    ))
    assert normalized.detection_ms == 12.35                 # 保留 2 位小数
    assert normalized.roi_box == (1, 2, 3, 4)

    negative_box = validate_result(DetectionResult(
        classification="肠套叠阳性", confidence=0.9, roi_box="not-a-box",
    ))
    assert negative_box.roi_box is None


# ---------------- 入口优先级：A/B 流水线 > team_model > Mock ----------------

def test_team_model_used_when_ab_not_ready(monkeypatch):
    """A/B 未就绪但融合模型可用时，应走 team_model。"""
    from algorithm import team_model
    from algorithm.interface import DetectionResult

    monkeypatch.setattr(detection, "READY", False)
    monkeypatch.setattr(classification, "READY", False)
    monkeypatch.setattr(pipeline, "is_team_model_ready", lambda: True)

    called = {}

    def fake_team_detect(path):
        called["path"] = path
        return DetectionResult(
            classification="肠套叠阳性",
            confidence=0.77,
            model_name=team_model.NAME,
            model_version=team_model.VERSION,
            classification_model_name=team_model.NAME,
            classification_model_version=team_model.VERSION,
            classification_ms=1234.5,
        )

    monkeypatch.setattr(team_model, "detect_intussusception", fake_team_detect)

    result = pipeline.detect_intussusception(Path("image.jpg"))
    assert called["path"] == Path("image.jpg")
    assert result.classification_model_name == team_model.NAME
    assert result.classification_ms == 1234.5
    assert result.detection_model_name == ""       # 该模型没有检测环节


def test_ab_pipeline_wins_over_team_model(monkeypatch):
    """A/B 就绪时优先级高于融合模型。"""
    monkeypatch.setattr(pipeline, "load_image", lambda p: "IMG")
    monkeypatch.setattr(detection, "READY", True)
    monkeypatch.setattr(classification, "READY", True)
    monkeypatch.setattr(detection, "NAME", "DetA")
    monkeypatch.setattr(pipeline, "is_team_model_ready", lambda: True)
    monkeypatch.setattr(detection, "detect", lambda img: ROI(image="ROI"))
    monkeypatch.setattr(
        classification, "classify",
        lambda roi: ClassificationOutcome(classification="肠套叠阴性", confidence=0.6),
    )

    result = pipeline.detect_intussusception(Path("x.jpg"))
    assert result.model_name == "team-pipeline"
    assert result.detection_model_name == "DetA"


def test_team_model_import_failure_is_safe(monkeypatch):
    """team_model 不可用（缺依赖/权重）时，is_team_model_ready 返回 False 而不是抛错。"""
    from algorithm import team_model

    monkeypatch.setattr(team_model, "is_available", lambda: False)
    assert pipeline.is_team_model_ready() is False

    # is_available 缺失时退回读 READY
    monkeypatch.delattr(team_model, "is_available")
    monkeypatch.setattr(team_model, "READY", False)
    assert pipeline.is_team_model_ready() is False


def test_team_model_reports_unavailable_reason_without_weights(monkeypatch, tmp_path):
    """权重缺失时给出可读的不可用原因（便于交付排查）。"""
    from algorithm import team_model

    # 依赖是否装好与本用例无关，这里只看"权重缺失"这条分支
    monkeypatch.setattr(team_model, "_DEPS_ERROR", None)
    monkeypatch.setattr(team_model, "WEIGHTS_DIR", tmp_path)
    assert team_model.is_available() is False
    reason = team_model.unavailable_reason()
    assert "权重" in reason and str(tmp_path) in reason


# ---------------- 融合模型的分类判定（可脱离权重/torch 单测） ----------------

def test_classification_is_placeholder_pending_diagnosis_model(monkeypatch):
    """默认（诊断分类模型未接入）：classification 是占位值，不随预后结果变化。

    本文件里的模型是**预后模型**（输出灌肠复位成功/失败），
    不具备诊断"有无肠套叠"的能力，因此不能拿它反推阳性/阴性。
    """
    from algorithm import team_model

    monkeypatch.setattr(team_model, "CLASSIFY_MODE", "placeholder")
    assert team_model.decide_classification(1) == "肠套叠阳性"
    assert team_model.decide_classification(0) == "肠套叠阳性"   # 预后"失败"也不改分类


def test_prognosis_mode_is_opt_in(monkeypatch):
    """prognosis 模式：按预后成功率外推（语义不严谨，仅显式开启时生效）。"""
    from algorithm import team_model

    monkeypatch.setattr(team_model, "CLASSIFY_MODE", "prognosis")
    assert team_model.decide_classification(1) == "肠套叠阳性"
    assert team_model.decide_classification(0) == "肠套叠阴性"


def test_negative_classification_drops_treatment_success_rate():
    """阴性结果不应带严重度/成功率（平台契约：这两项仅阳性有意义）。

    占位模式下不会产生阴性，但诊断分类模型接入后必须成立，属前瞻性保护。
    """
    from algorithm.interface import DetectionResult, validate_result

    negative = validate_result(DetectionResult(
        classification="肠套叠阴性",
        confidence=0.8,
        severity="轻度",                 # 模型侧误填，平台应清掉
        treatment_success_rate=0.97,
        treatment_advice="",             # 留空 → 平台补阴性默认建议
    ))
    assert negative.severity is None
    assert negative.treatment_success_rate is None
    assert "未见肠套叠" in negative.treatment_advice
