"""Face width proxy + match labels aligned with docs/glasses_tryon_mvp.md."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from try_on import iris_centers_xy

# MediaPipe Face Landmarker: cheek / face contour anchors (stable on frontal faces).
LM_CHEEK_RIGHT = 234
LM_CHEEK_LEFT = 454


@dataclass
class FaceMetrics:
    ipd_px: float
    cheek_span_px: float
    cheek_over_ipd: float
    band: str  # "S" | "M" | "L"
    low_confidence: bool
    low_confidence_reason: str | None


def landmarks_to_metrics(landmarks_xy: np.ndarray, *, min_ipd_px: float = 28.0) -> FaceMetrics:
    """
    cheek_over_ipd: 颧/颊宽度相对瞳距，减弱拍摄距离带来的绝对像素误差（MVP 用分档 + 预警）。
    """
    pr, pl = iris_centers_xy(landmarks_xy)
    ipd = float(np.linalg.norm(pl - pr))
    p234 = landmarks_xy[LM_CHEEK_RIGHT, :2]
    p454 = landmarks_xy[LM_CHEEK_LEFT, :2]
    cheek = float(np.linalg.norm(p454 - p234))
    low_reason: str | None = None
    low = False
    if ipd < min_ipd_px:
        low = True
        low_reason = "瞳距在图中过小，请靠近一些或换更高分辨率照片。"
    if ipd < 1.0:
        low = True
        low_reason = "无法稳定估计瞳距。"

    ratio = cheek / ipd if ipd >= 1.0 else 0.0
    # 分档阈值在示例脸（Lena ~2.10）附近居中，可按业务样本再标定。
    if ratio < 2.00:
        band = "S"
    elif ratio < 2.18:
        band = "M"
    else:
        band = "L"

    return FaceMetrics(
        ipd_px=ipd,
        cheek_span_px=cheek,
        cheek_over_ipd=ratio,
        band=band,
        low_confidence=low,
        low_confidence_reason=low_reason,
    )


def metrics_to_dict(m: FaceMetrics) -> dict[str, Any]:
    return {
        "ipd_px": round(m.ipd_px, 2),
        "cheek_span_px": round(m.cheek_span_px, 2),
        "cheek_over_ipd": round(m.cheek_over_ipd, 4),
        "band": m.band,
        "low_confidence": m.low_confidence,
        "low_confidence_reason": m.low_confidence_reason,
    }


# 与文档一致的可解释枚举
MATCH = "MATCH"
WARN_TOO_WIDE = "WARN_TOO_WIDE"
WARN_TOO_NARROW = "WARN_TOO_NARROW"
LOW_CONFIDENCE = "LOW_CONFIDENCE"


def band_delta(user_band: str, frame_band: str) -> int:
    order = {"S": 0, "M": 1, "L": 2}
    return order.get(frame_band, 1) - order.get(user_band, 1)


def match_status_for_frame(user_band: str, frame_band: str, *, low_confidence: bool) -> tuple[str, str]:
    if low_confidence:
        return LOW_CONFIDENCE, "检测置信度不足，结果仅供示意，建议重新拍摄正面清晰人脸。"

    d = band_delta(user_band, frame_band)
    if d == 0:
        return MATCH, "面宽分档与镜架推荐档位一致，静态示意效果相对更协调。"
    if d < 0:
        return WARN_TOO_NARROW, "镜架相对脸型偏窄，长期佩戴可能夹脸或视觉比例不协调（示意，非验光结论）。"
    return WARN_TOO_WIDE, "镜架相对脸型偏宽，可能下滑或侧向比例偏大（示意，非验光结论）。"


def rank_frames(
    user_band: str,
    frames: list[dict[str, Any]],
    *,
    low_confidence: bool,
) -> list[dict[str, Any]]:
    """Return frames sorted by suitability (same band first), each with match_status + message."""
    scored: list[tuple[int, dict[str, Any]]] = []
    for f in frames:
        status, msg = match_status_for_frame(user_band, str(f.get("band", "M")), low_confidence=low_confidence)
        priority = {"MATCH": 0, "WARN_TOO_NARROW": 1, "WARN_TOO_WIDE": 1, "LOW_CONFIDENCE": 2}[status]
        band_penalty = abs(band_delta(user_band, str(f.get("band", "M"))))
        item = {**f, "match_status": status, "match_message": msg}
        scored.append((priority * 10 + band_penalty, item))
    scored.sort(key=lambda x: x[0])
    return [x[1] for x in scored]
