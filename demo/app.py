#!/usr/bin/env python3
"""
Minimal MVP web demo: upload face → face-width band → frame recommendations → static try-on PNG.

Run from repo root (so ``assets/`` resolves):

  cd glasses_virtual_tryon && source .venv/bin/activate
  python demo/app.py
  # 本机: http://127.0.0.1:5050 ；同网手机: http://<电脑局域网IP>:5050
  # 仅本机监听: MVP_BIND=127.0.0.1 python demo/app.py
  # 上传大小上限（MB）: MVP_MAX_UPLOAD_MB=80 python demo/app.py
"""

from __future__ import annotations

import base64
import json
import os
import sys
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_file
from PIL import Image, ImageOps
from werkzeug.exceptions import RequestEntityTooLarge

# Demo modules live alongside this file.
DEMO_DIR = Path(__file__).resolve().parent
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

import face_match  # noqa: E402
import mvp_assets  # noqa: E402
import try_on  # noqa: E402

PROJECT_ROOT = DEMO_DIR.parent
FRAMES_DIR = PROJECT_ROOT / "assets" / "frames"
DEFAULT_MODEL = PROJECT_ROOT / "assets" / "face_landmarker.task"


def _check_eyewear_on_photo(
    face_bgr: np.ndarray,
    pts: np.ndarray,
    *,
    sensitivity: str = "default",
) -> tuple[bool, str | None]:
    """在 ``demo/`` 目录下加载 ``photo_guard``（避免遗漏顶层 import 导致 NameError）。"""
    from photo_guard import likely_has_eyewear

    return likely_has_eyewear(face_bgr, pts, sensitivity=sensitivity)


app = Flask(
    __name__,
    template_folder=str(DEMO_DIR / "templates"),
    static_folder=str(DEMO_DIR / "static"),
)
# iPhone 原图 / ProRAW / 相册「未压缩」单张易超过 12MB；可用环境变量 MVP_MAX_UPLOAD_MB 调整（默认 40）
_max_mb = max(12, int(os.environ.get("MVP_MAX_UPLOAD_MB", "40")))
app.config["MAX_CONTENT_LENGTH"] = _max_mb * 1024 * 1024


@app.after_request
def _cors_headers(response):
    """Allow uni-app H5 / devtools to call this demo API from another origin."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Tryon-Wrap"
    return response


@app.before_request
def _api_preflight():
    if request.method == "OPTIONS" and request.path.startswith("/api/"):
        return "", 204


@app.errorhandler(RequestEntityTooLarge)
def _handle_payload_too_large(_e: RequestEntityTooLarge):
    """避免 413 返回 HTML 导致前端 res.json() 在 Safari 上报错。"""
    lim_mb = float(app.config.get("MAX_CONTENT_LENGTH", 0)) / (1024.0 * 1024.0)
    msg = (
        f"图片文件超过服务器单张上限（约 {lim_mb:.0f} MB）。"
        "请在相册中选用「较小」副本、或「压缩并发送」后再上传；也可在本机设置环境变量 MVP_MAX_UPLOAD_MB 提高限制。"
    )
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "PAYLOAD_TOO_LARGE", "message": msg}), 413
    return (
        '<!doctype html><meta charset="utf-8"><title>文件过大</title><p>'
        + msg
        + "</p>",
        413,
        {"Content-Type": "text/html; charset=utf-8"},
    )


def _load_catalog() -> list[dict]:
    mvp_assets.ensure_mvp_catalog()
    data = json.loads((FRAMES_DIR / "catalog.json").read_text(encoding="utf-8"))
    return list(data.get("frames", []))


def _frame_by_id(catalog: list[dict], fid: str) -> dict | None:
    for f in catalog:
        if f.get("id") == fid:
            return f
    return None


def _register_heif_opener() -> None:
    try:
        import pillow_heif  # noqa: PLC0415

        pillow_heif.register_heif_opener()
    except ImportError:
        pass


def _pil_bytes_to_bgr(raw: bytes) -> np.ndarray | None:
    """Decode JPEG/PNG/HEIC etc. Apply EXIF orientation (iPhone). Return BGR or None."""
    _register_heif_opener()
    try:
        im = Image.open(BytesIO(raw))
        im = ImageOps.exif_transpose(im)
        if im.mode == "RGBA":
            rgb = Image.new("RGB", im.size, (255, 255, 255))
            rgb.paste(im, mask=im.split()[3])
            im = rgb
        elif im.mode != "RGB":
            im = im.convert("RGB")
        rgb = np.asarray(im, dtype=np.uint8)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            return None
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def _maybe_downscale_bgr(bgr: np.ndarray, max_side: int = 4096) -> np.ndarray:
    h, w = bgr.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return bgr
    s = max_side / float(m)
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    return cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_AREA)


def decode_face_upload(file_storage) -> tuple[np.ndarray | None, str | None, str | None]:
    """
    Returns ``(bgr, error_code, message)``. On success ``error_code`` and ``message`` are None.
    Always JSON-friendly errors for the Web API (no HTML abort for decode failures).
    """
    raw = file_storage.read()
    if not raw:
        return None, "EMPTY", "未收到图片文件，请重新选择。"
    arr = np.frombuffer(raw, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        bgr = _pil_bytes_to_bgr(raw)
    if bgr is None:
        return (
            None,
            "DECODE_FAILED",
            "无法识别此图片格式。iPhone 用户：可在「设置 → 相机 → 格式」中选「兼容性最佳」"
            "（JPEG），或在相册中将照片存储为 JPEG 后再上传；已安装依赖时亦支持 HEIC。",
        )
    return _maybe_downscale_bgr(bgr), None, None


@app.route("/")
def index():
    return render_template("mvp.html")


@app.route("/api/catalog")
def api_catalog():
    return jsonify({"frames": _load_catalog()})


@app.route("/api/frame-preview/<frame_id>")
def api_frame_preview(frame_id: str):
    """返回 catalog 中该款镜架的 PNG（透明线框图），供推荐列表展示。"""
    spec = _frame_by_id(_load_catalog(), frame_id)
    if spec is None:
        abort(404)
    raw = spec.get("image")
    if not isinstance(raw, str) or not raw.strip():
        abort(404)
    name = Path(raw).name
    if Path(raw).parts != (name,):
        abort(404)
    path = (FRAMES_DIR / name).resolve()
    if path.parent != FRAMES_DIR.resolve() or not path.is_file():
        abort(404)
    return send_file(path, mimetype="image/png")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    if "face" not in request.files:
        abort(400, description="Missing form field ``face``.")
    face_bgr, dec_err, dec_msg = decode_face_upload(request.files["face"])
    if face_bgr is None:
        return jsonify({"ok": False, "error": dec_err or "DECODE_FAILED", "message": dec_msg or "解码失败"}), 200
    rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    try_on.ensure_model(DEFAULT_MODEL)
    lm = try_on.build_face_landmarker(DEFAULT_MODEL)
    try:
        pts = try_on.detect_landmarks_rgb(lm, rgb)
    finally:
        lm.close()

    if pts is None:
        return jsonify(
            {
                "ok": False,
                "error": "NO_FACE",
                "message": "未检测到人脸，请上传正面、清晰、无强遮挡的自拍。",
            }
        )

    has_glasses, gmsg = _check_eyewear_on_photo(face_bgr, pts, sensitivity="default")
    if has_glasses:
        return jsonify(
            {
                "ok": False,
                "error": "GLASSES_ON_FACE",
                "message": gmsg
                or "检测到可能已佩戴眼镜或墨镜，请摘下后重新拍摄正面清晰照片。",
            }
        )

    metrics = face_match.landmarks_to_metrics(pts)
    catalog = _load_catalog()
    ranked = face_match.rank_frames(metrics.band, catalog, low_confidence=metrics.low_confidence)

    return jsonify(
        {
            "ok": True,
            "metrics": face_match.metrics_to_dict(metrics),
            "recommendations": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "band": r["band"],
                    "image": r.get("image"),
                    "mm_total_width": r.get("mm_total_width"),
                    "blurb": r.get("blurb"),
                    "match_status": r["match_status"],
                    "match_message": r["match_message"],
                }
                for r in ranked
            ],
        }
    )


@app.route("/api/tryon", methods=["POST"])
def api_tryon():
    if "face" not in request.files or "frame_id" not in request.form:
        abort(400, description="Need ``face`` file and ``frame_id`` form field.")
    frame_id = request.form["frame_id"].strip()
    catalog = _load_catalog()
    spec = _frame_by_id(catalog, frame_id)
    if spec is None:
        abort(404, description="Unknown frame_id.")

    path = FRAMES_DIR / str(spec["image"])
    if not path.is_file():
        abort(500, description="Frame asset missing on server.")

    face_bgr, dec_err, dec_msg = decode_face_upload(request.files["face"])
    if face_bgr is None:
        return jsonify({"ok": False, "error": dec_err or "DECODE_FAILED", "message": dec_msg or "解码失败"}), 422
    glasses = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if glasses is None:
        abort(500, description="Could not read glasses PNG.")

    lms = try_on.detect_face_landmarks_bgr(face_bgr, DEFAULT_MODEL)
    if lms is None:
        return jsonify(
            {
                "ok": False,
                "error": "NO_FACE",
                "message": "未检测到人脸，请上传正面、清晰、无强遮挡的自拍。",
            }
        ), 200

    plf = spec.get("pupil_left_frac")
    prf = spec.get("pupil_right_frac")
    eyf = spec.get("eyeline_frac")
    nbb = spec.get("nose_bridge_blend")

    try:
        out_bgr = try_on.compose_try_on_bgr_from_landmarks(
            face_bgr,
            glasses,
            lms,
            pupil_left_frac=float(plf) if plf is not None else None,
            pupil_right_frac=float(prf) if prf is not None else None,
            eyeline_frac=float(eyf) if eyf is not None else None,
            nose_bridge_blend=float(nbb) if nbb is not None else None,
        )
    except (RuntimeError, ValueError) as e:
        return jsonify({"ok": False, "error": "TRYON_FAILED", "message": str(e)}), 422

    ok, buf = cv2.imencode(".png", out_bgr)
    if not ok:
        abort(500, description="Encode failed.")
    png_bytes = buf.tobytes()
    wrap = request.args.get("wrap") == "1" or request.headers.get("X-Tryon-Wrap") == "1"
    if wrap:
        return jsonify(
            {
                "ok": True,
                "mime": "image/png",
                "image_base64": base64.standard_b64encode(png_bytes).decode("ascii"),
            }
        )
    return send_file(
        BytesIO(png_bytes),
        mimetype="image/png",
        as_attachment=False,
        download_name="try_on.png",
    )


def main() -> None:
    mvp_assets.ensure_mvp_catalog()
    try_on.ensure_model(DEFAULT_MODEL)
    # 默认 0.0.0.0 便于同 WiFi 手机访问；不信任局域网时用 MVP_BIND=127.0.0.1
    host = os.environ.get("MVP_BIND", "0.0.0.0")
    port = int(os.environ.get("MVP_PORT", "5050"))
    # 单进程即可承载本地 Demo；生产需换 WSGI 与多进程。
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
