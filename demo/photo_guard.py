"""
Heuristic: spectacles add dense edges in the periorbital band and across the nose bridge.

When the head is **tilted or turned**, the fixed image ROIs misalign with anatomy and edge
statistics spike asymmetrically — that caused false "already wearing glasses" alerts.
We estimate a mild **pose stress** factor (roll + inter-eye / nose asymmetry) and **raise
thresholds** as stress increases; near-frontal photos keep the base (stricter) bar.
"""

from __future__ import annotations

import cv2
import numpy as np

_EYE_BOX_IDX = (33, 133, 263, 362, 168, 6)
_CHEEK_IDX = (234, 454)
_CHEEK_FLOOR = 0.006

# Base thresholds (near-frontal, stress ≈ 1.0)
_HARD_EYE_VS_CHEEK = 2.02
_HARD_MIN_EYE_D = 0.0265
_HARD_BRIDGE_VS_CHEEK = 1.38

_SOFT_CANNY = (24, 55)
_SOFT_EYE_VS_CHEEK = 1.45
_SOFT_MIN_EYE_D = 0.042
_SOFT_BRIDGE_VS_CHEEK = 1.25

_GRAD_VS_CHEEK = 1.36
_GRAD_MIN_EYE = 13.2
_LAP_VS_CHEEK = 2.0
_LAP_MIN_EYE = 50.0
_FUSION_BRIDGE_VS_CHEEK = 1.2
_FUSION_MIN_HARD_EYE_D = 0.014

# Pose: beyond these, require stronger edge evidence
_ROLL_START_DEG = 6.0
_ROLL_STRESS_PER_DEG = 0.011
_YAW_ASYM_START = 0.11
_YAW_STRESS_COEF = 0.42
_STRESS_CAP = 1.16


def _head_roll_deg(xy: np.ndarray) -> float:
    """|deg| from horizontal of the inter-eye (outer canthi) line; proxy for in-plane head tilt."""
    pr, pl = xy[33, :2], xy[263, :2]
    if pr[0] > pl[0]:
        pr, pl = pl, pr
    vec = pl - pr
    return abs(float(np.degrees(np.arctan2(vec[1], vec[0]))))


def _yaw_asymmetry(xy: np.ndarray) -> float:
    """Horizontal offset of nose tip vs eye midpoint, normalized by inter-eye distance."""
    if xy.shape[0] <= 1:
        return 0.0
    pr, pl = xy[33, :2], xy[263, :2]
    if pr[0] > pl[0]:
        pr, pl = pl, pr
    mid = (pr + pl) / 2.0
    nose = xy[1, :2]
    inter = float(np.linalg.norm(pl - pr)) + 1e-6
    return abs(float(nose[0] - mid[0])) / inter


def _pose_stress(xy: np.ndarray) -> float:
    s = 1.0
    roll = _head_roll_deg(xy)
    if roll > _ROLL_START_DEG:
        s += min(0.10, (roll - _ROLL_START_DEG) * _ROLL_STRESS_PER_DEG)
    yaw_n = _yaw_asymmetry(xy)
    if yaw_n > _YAW_ASYM_START:
        s += min(0.08, (yaw_n - _YAW_ASYM_START) * _YAW_STRESS_COEF)
    return float(min(s, _STRESS_CAP))


def _mean_abs_sobel(gray_u8: np.ndarray) -> float:
    gx = cv2.Sobel(gray_u8, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_u8, cv2.CV_32F, 0, 1, ksize=3)
    return float(np.mean(np.abs(gx)) + np.mean(np.abs(gy)))


def _laplacian_var(gray_u8: np.ndarray) -> float:
    lap = cv2.Laplacian(gray_u8, cv2.CV_32F)
    return float(np.var(lap))


def _canny_density(gray_u8: np.ndarray, t1: int, t2: int) -> float:
    e = cv2.Canny(gray_u8, t1, t2)
    return float(np.mean(e > 0))


def likely_has_eyewear(face_bgr: np.ndarray, landmarks_xy: np.ndarray) -> tuple[bool, str | None]:
    """
    Return (True, user_message) if the image likely already shows glasses/sunglasses on the face.
    """
    if face_bgr is None or face_bgr.size == 0 or landmarks_xy is None:
        return False, None
    h, w = face_bgr.shape[:2]
    if h < 32 or w < 32:
        return False, None

    xy = landmarks_xy[:, :2]
    n = xy.shape[0]
    if n <= max(_EYE_BOX_IDX + _CHEEK_IDX):
        return False, None

    stress = _pose_stress(xy)
    abs_boost = 1.0 + 0.38 * (stress - 1.0)

    face_h = float(np.max(xy[:, 1]) - np.min(xy[:, 1]) + 1.0)

    pad_x = 0.06 * w
    pad_y = 0.05 * h
    ex = xy[list(_EYE_BOX_IDX), 0]
    ey = xy[list(_EYE_BOX_IDX), 1]
    x1 = int(max(0, np.floor(ex.min() - pad_x)))
    x2 = int(min(w, np.ceil(ex.max() + pad_x)))
    y1 = int(max(0, np.floor(ey.min() - pad_y)))
    y2 = int(min(h, np.ceil(ey.max() + pad_y * 1.85)))
    if x2 <= x1 + 4 or y2 <= y1 + 4:
        return False, None

    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    eye_gray = gray[y1:y2, x1:x2]
    eye_d = _canny_density(eye_gray, 35, 90)
    eye_d_soft = _canny_density(eye_gray, _SOFT_CANNY[0], _SOFT_CANNY[1])
    eye_grad = _mean_abs_sobel(eye_gray)
    eye_lap = _laplacian_var(eye_gray)

    half = max(6, int(0.055 * min(h, w)))
    cheek_ds: list[float] = []
    cheek_grads: list[float] = []
    cheek_laps: list[float] = []
    for idx in _CHEEK_IDX:
        if idx >= n:
            continue
        cx, cy = int(xy[idx, 0]), int(xy[idx, 1])
        cy = int(min(h - half - 1, cy + int(0.045 * face_h)))
        cx1, cy1 = max(0, cx - half), max(0, cy - half)
        cx2, cy2 = min(w, cx + half), min(h, cy + half)
        if cx2 <= cx1 + 2 or cy2 <= cy1 + 2:
            continue
        ix1, iy1 = max(cx1, x1), max(cy1, y1)
        ix2, iy2 = min(cx2, x2), min(cy2, y2)
        if ix2 > ix1 and iy2 > iy1:
            inter = (ix2 - ix1) * (iy2 - iy1)
            a_eye = (x2 - x1) * (y2 - y1)
            a_ch = (cx2 - cx1) * (cy2 - cy1)
            if inter / min(a_eye, a_ch) > 0.32:
                cy1 = min(h - 1, y2 + int(0.025 * face_h))
                cy2 = min(h, cy1 + 2 * half)
                if cy2 <= cy1 + 2:
                    continue
        pg = gray[cy1:cy2, cx1:cx2]
        if pg.size:
            cheek_ds.append(_canny_density(pg, 35, 90))
            cheek_grads.append(_mean_abs_sobel(pg))
            cheek_laps.append(_laplacian_var(pg))

    if not cheek_ds:
        return False, None

    cheek_d = max(_CHEEK_FLOOR, float(np.mean(cheek_ds)))
    cheek_g = max(2.8, float(np.mean(cheek_grads)))
    cheek_l = max(10.0, float(np.mean(cheek_laps)))

    xi1, xi2 = int(xy[133, 0]), int(xy[362, 0])
    bx1, bx2 = min(xi1, xi2), max(xi1, xi2)
    bw = bx2 - bx1
    if bw < 10:
        return False, None
    cx1 = int(bx1 + 0.28 * bw)
    cx2 = int(bx1 + 0.72 * bw)
    cx1, cx2 = max(0, cx1), min(w, cx2)
    if cx2 <= cx1 + 2:
        return False, None
    bridge_gray = gray[y1:y2, cx1:cx2]
    bridge_d = _canny_density(bridge_gray, 35, 90)
    bridge_d_soft = _canny_density(bridge_gray, _SOFT_CANNY[0], _SOFT_CANNY[1])

    ratio = eye_d / cheek_d
    br_ratio = bridge_d / cheek_d
    ratio_soft = eye_d_soft / cheek_d
    br_soft_ratio = bridge_d_soft / cheek_d

    msg = (
        "检测到照片中面部可能已佩戴眼镜或墨镜（镜框/镜片边缘特征明显）。"
        "为准确分析瞳距与试戴效果，请摘下眼镜、勿戴墨镜后重新拍摄或上传正面人脸照片。"
    )

    h_eye = _HARD_EYE_VS_CHEEK * stress
    h_min = _HARD_MIN_EYE_D * abs_boost
    h_br = _HARD_BRIDGE_VS_CHEEK * (1.0 + 0.22 * (stress - 1.0))

    if ratio >= h_eye and eye_d >= h_min and br_ratio >= h_br:
        return True, msg

    s_eye = _SOFT_EYE_VS_CHEEK * stress
    s_min = _SOFT_MIN_EYE_D * abs_boost
    s_br = _SOFT_BRIDGE_VS_CHEEK * (1.0 + 0.2 * (stress - 1.0))
    if (
        ratio_soft >= s_eye
        and eye_d_soft >= s_min
        and br_soft_ratio >= s_br
        and eye_d >= 0.015 * abs_boost
    ):
        return True, msg

    g_rat = _GRAD_VS_CHEEK * stress
    g_min = _GRAD_MIN_EYE * (1.0 + 0.25 * (stress - 1.0))
    l_rat = _LAP_VS_CHEEK * stress
    l_min = _LAP_MIN_EYE * (1.0 + 0.2 * (stress - 1.0))
    f_br = _FUSION_BRIDGE_VS_CHEEK * (1.0 + 0.18 * (stress - 1.0))
    f_eye = _FUSION_MIN_HARD_EYE_D * abs_boost

    if (
        eye_grad >= g_min
        and eye_grad / cheek_g >= g_rat
        and eye_lap >= l_min
        and eye_lap / cheek_l >= l_rat
        and br_ratio >= f_br
        and eye_d >= f_eye
    ):
        return True, msg

    return False, None
