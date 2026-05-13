#!/usr/bin/env python3
"""
Minimal MVP web demo: upload face → face-width band → frame recommendations → static try-on PNG.

Run from repo root (so ``assets/`` resolves):

  cd glasses_virtual_tryon && source .venv/bin/activate
  python demo/app.py
  # open http://127.0.0.1:5050
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_file

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

app = Flask(
    __name__,
    template_folder=str(DEMO_DIR / "templates"),
    static_folder=str(DEMO_DIR / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024


def _load_catalog() -> list[dict]:
    mvp_assets.ensure_mvp_catalog()
    data = json.loads((FRAMES_DIR / "catalog.json").read_text(encoding="utf-8"))
    return list(data.get("frames", []))


def _frame_by_id(catalog: list[dict], fid: str) -> dict | None:
    for f in catalog:
        if f.get("id") == fid:
            return f
    return None


def _decode_upload_face(file_storage) -> np.ndarray:
    raw = file_storage.read()
    if not raw:
        abort(400, description="Empty file.")
    arr = np.frombuffer(raw, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        abort(400, description="Could not decode image; use JPG or PNG.")
    return bgr


@app.route("/")
def index():
    return render_template("mvp.html")


@app.route("/api/catalog")
def api_catalog():
    return jsonify({"frames": _load_catalog()})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    if "face" not in request.files:
        abort(400, description="Missing form field ``face``.")
    face_bgr = _decode_upload_face(request.files["face"])
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

    face_bgr = _decode_upload_face(request.files["face"])
    glasses = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if glasses is None:
        abort(500, description="Could not read glasses PNG.")

    plf = spec.get("pupil_left_frac")
    prf = spec.get("pupil_right_frac")
    eyf = spec.get("eyeline_frac")

    try:
        out_bgr = try_on.compose_try_on_bgr(
            face_bgr,
            glasses,
            DEFAULT_MODEL,
            pupil_left_frac=float(plf) if plf is not None else None,
            pupil_right_frac=float(prf) if prf is not None else None,
            eyeline_frac=float(eyf) if eyf is not None else None,
        )
    except RuntimeError as e:
        return jsonify({"ok": False, "error": "NO_FACE", "message": str(e)}), 200

    ok, buf = cv2.imencode(".png", out_bgr)
    if not ok:
        abort(500, description="Encode failed.")
    from io import BytesIO

    return send_file(
        BytesIO(buf.tobytes()),
        mimetype="image/png",
        as_attachment=False,
        download_name="try_on.png",
    )


def main() -> None:
    mvp_assets.ensure_mvp_catalog()
    try_on.ensure_model(DEFAULT_MODEL)
    # 单进程即可承载本地 Demo；生产需换 WSGI 与多进程。
    app.run(host="127.0.0.1", port=5050, debug=False)


if __name__ == "__main__":
    main()
