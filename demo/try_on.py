#!/usr/bin/env python3
"""
Minimal glasses try-on skeleton: MediaPipe Face Landmarker + 2D PNG overlay.

  python demo/try_on.py --face path/to/face.jpg --glasses assets/frames/sample.png --out out/try_on.png
  python demo/try_on.py --init-assets    # download model + write sample frame PNG
  python demo/try_on.py --demo            # init assets, fetch a test portrait, run overlay

Landmark indices follow the MediaPipe face mesh convention (478-point model).
Tune PUPIL_* / EYELINE_FRAC to match **lens optical centers** in your glasses PNG,
or pass --pupil-left-frac / --pupil-right-frac / --eyeline-frac.
"""

from __future__ import annotations

import argparse
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import cv2
import numpy as np

# --- MediaPipe Tasks (Face Landmarker) ---
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks_python
    from mediapipe.tasks.python import vision as mp_vision
except ImportError as e:  # pragma: no cover
    print("Missing dependency. Run: pip install -r requirements.txt", file=sys.stderr)
    raise e

# Fallback eye anchors if iris indices are missing (old models).
LM_RIGHT_INNER = 133
LM_LEFT_INNER = 362
# MediaPipe Face Landmarker 478 pts: iris rings at end of list (see Google Face Mesh iris).
LM_IRIS_RIGHT_START = 473
LM_IRIS_LEFT_START = 468

# In the *glasses PNG*, **lens center** horizontal positions as fraction of width [0,1].
# Must match how `write_sample_glasses_png` / your product art places each lens hub.
PUPIL_LEFT_FRAC = 0.32
PUPIL_RIGHT_FRAC = 0.68
# Vertical position of lens centers from top of glasses PNG [0,1].
EYELINE_FRAC = 0.50

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = PROJECT_ROOT / "assets" / "face_landmarker.task"
DEFAULT_GLASSES = PROJECT_ROOT / "assets" / "frames" / "sample.png"
DEFAULT_OUT = PROJECT_ROOT / "out" / "try_on.png"

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)

# OpenCV sample portrait (classic CV test image; use your own photo in production).
DEMO_FACE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path, *, attempts: int = 4) -> None:
    """Fetch URL to disk. Uses ``http_proxy`` / ``https_proxy`` / ``ALL_PROXY`` via ``getproxies()``."""
    ensure_parent(dest)
    print(f"Downloading:\n  {url}\n -> {dest}")
    proxies = urllib.request.getproxies()
    if proxies:
        print(f"Using proxies: {proxies}")
    ctx = ssl.create_default_context()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler(proxies),
        urllib.request.HTTPSHandler(context=ctx),
    )
    req = urllib.request.Request(url, headers={"User-Agent": "glasses_virtual_tryon/1.0"})
    last_err: BaseException | None = None
    for i in range(attempts):
        try:
            with opener.open(req, timeout=180) as resp:  # noqa: S310
                dest.write_bytes(resp.read())
            return
        except (OSError, urllib.error.URLError) as e:
            last_err = e
            if i + 1 < attempts:
                wait = 2**i
                print(f"Download failed ({e}); retry in {wait}s …", file=sys.stderr)
                time.sleep(wait)
    assert last_err is not None
    raise last_err


def ensure_model(model_path: Path) -> None:
    if model_path.is_file():
        return
    download_file(MODEL_URL, model_path)


def write_sample_glasses_png(dest: Path) -> None:
    """Wireframe frame with two lens openings; lens hubs align with PUPIL_* / EYELINE_FRAC in this file."""
    from PIL import Image, ImageDraw

    ensure_parent(dest)
    w, h = 900, 420
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx1 = int(PUPIL_LEFT_FRAC * w)
    cx2 = int(PUPIL_RIGHT_FRAC * w)
    cy = int(EYELINE_FRAC * h)
    r = int(min(w, h) * 0.19)
    for cx in (cx1, cx2):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(35, 35, 35, 255), width=10)
    draw.line((cx1 + int(r * 0.55), cy, cx2 - int(r * 0.55), cy), fill=(35, 35, 35, 230), width=8)
    draw.line((cx1 - r, cy, 18, cy + 8), fill=(35, 35, 35, 200), width=7)
    draw.line((cx2 + r, cy, w - 18, cy + 8), fill=(35, 35, 35, 200), width=7)
    img.save(dest, format="PNG")
    print(f"Wrote sample glasses PNG: {dest}")


def build_face_landmarker(model_path: Path):
    options = mp_vision.FaceLandmarkerOptions(
        base_options=mp_tasks_python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=mp_vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    return mp_vision.FaceLandmarker.create_from_options(options)


def detect_landmarks_rgb(landmarker, rgb: np.ndarray):
    rgb = np.ascontiguousarray(rgb)
    h, w = rgb.shape[:2]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)
    if not result.face_landmarks:
        return None
    lm = result.face_landmarks[0]
    pts = np.zeros((len(lm), 3), dtype=np.float64)
    for i, p in enumerate(lm):
        pts[i, 0] = p.x * w
        pts[i, 1] = p.y * h
        pts[i, 2] = p.z * w  # z scaled by width (MediaPipe convention)
    return pts


def iris_centers_xy(landmarks_xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Return (right_iris_xy, left_iris_xy) in image pixels.
    Uses iris ring landmarks when present (478-pt model); else falls back to inner canthi.
    """
    n = landmarks_xy.shape[0]
    if n > LM_IRIS_RIGHT_START + 4:
        left_ring = landmarks_xy[468:473, :2]
        right_ring = landmarks_xy[473:478, :2]
        pl = np.mean(left_ring, axis=0)
        pr = np.mean(right_ring, axis=0)
        # Frontal face: subject's left eye is on the image right (larger x).
        if pl[0] < pr[0]:
            pr, pl = pl, pr
        return pr, pl
    pr = landmarks_xy[LM_RIGHT_INNER, :2]
    pl = landmarks_xy[LM_LEFT_INNER, :2]
    return pr, pl


def overlay_glasses_bgra(
    face_bgr: np.ndarray,
    glasses_bgra: np.ndarray,
    landmarks_xy: np.ndarray,
    *,
    pupil_left_frac: float | None = None,
    pupil_right_frac: float | None = None,
    eyeline_frac: float | None = None,
) -> np.ndarray:
    """
    Similarity transform: map lens centers in glasses PNG to iris centers on the face.
    """
    h, w = face_bgr.shape[:2]
    pr, pl = iris_centers_xy(landmarks_xy)
    vec = pl - pr
    ipd = float(np.linalg.norm(vec))
    if ipd < 1.0:
        raise ValueError("Interpupillary distance too small; bad landmarks?")
    center = (pr + pl) / 2.0
    angle_deg = float(np.degrees(np.arctan2(vec[1], vec[0])))

    plf = float(pupil_left_frac if pupil_left_frac is not None else PUPIL_LEFT_FRAC)
    prf = float(pupil_right_frac if pupil_right_frac is not None else PUPIL_RIGHT_FRAC)
    eyf = float(eyeline_frac if eyeline_frac is not None else EYELINE_FRAC)
    if not (0.0 <= plf < prf <= 1.0 and 0.0 <= eyf <= 1.0):
        raise ValueError("Invalid pupil / eyeline fractions.")

    gh, gw = glasses_bgra.shape[:2]
    span_g = (prf - plf) * float(gw)
    if span_g < 1.0:
        raise ValueError("Invalid glasses PNG width or pupil fractions.")
    scale = ipd / span_g
    new_w = max(1, int(round(gw * scale)))
    new_h = max(1, int(round(gh * scale)))
    resized = cv2.resize(glasses_bgra, (new_w, new_h), interpolation=cv2.INTER_AREA)

    ax = (plf + prf) / 2.0 * new_w
    ay = eyf * new_h

    theta = np.radians(angle_deg)
    c, s = float(np.cos(theta)), float(np.sin(theta))
    r_mat = np.array([[c, -s], [s, c]], dtype=np.float64)
    t_vec = center.astype(np.float64) - r_mat @ np.array([ax, ay], dtype=np.float64)
    m_2x3 = np.hstack([r_mat, t_vec.reshape(2, 1)])

    warped = cv2.warpAffine(
        resized,
        m_2x3,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    out = face_bgr.astype(np.float32)
    b, g, r, a = cv2.split(warped.astype(np.float32))
    a = a / 255.0
    a3 = np.stack([a, a, a], axis=-1)
    fg = np.stack([b, g, r], axis=-1)
    comp = out * (1.0 - a3) + fg * a3
    return np.clip(comp, 0, 255).astype(np.uint8)


def run_try_on(
    face_path: Path,
    glasses_path: Path,
    out_path: Path,
    model_path: Path,
    *,
    pupil_left_frac: float | None = None,
    pupil_right_frac: float | None = None,
    eyeline_frac: float | None = None,
) -> None:
    ensure_model(model_path)
    face_bgr = cv2.imread(str(face_path), cv2.IMREAD_COLOR)
    if face_bgr is None:
        raise FileNotFoundError(f"Could not read face image: {face_path}")
    glasses_bgra = cv2.imread(str(glasses_path), cv2.IMREAD_UNCHANGED)
    if glasses_bgra is None:
        raise FileNotFoundError(f"Could not read glasses PNG: {glasses_path}")
    if glasses_bgra.shape[2] == 3:
        glasses_bgra = cv2.cvtColor(glasses_bgra, cv2.COLOR_BGR2BGRA)
        glasses_bgra[:, :, 3] = 255

    rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    landmarker = build_face_landmarker(model_path)
    try:
        lms = detect_landmarks_rgb(landmarker, rgb)
    finally:
        landmarker.close()
    if lms is None:
        raise RuntimeError("No face detected. Try a clearer frontal photo.")

    out_bgr = overlay_glasses_bgra(
        face_bgr,
        glasses_bgra,
        lms,
        pupil_left_frac=pupil_left_frac,
        pupil_right_frac=pupil_right_frac,
        eyeline_frac=eyeline_frac,
    )
    ensure_parent(out_path)
    cv2.imwrite(str(out_path), out_bgr)
    print(f"Wrote: {out_path}")


def cmd_init_assets(args: argparse.Namespace) -> None:
    ensure_model(Path(args.model))
    gpath = Path(args.glasses)
    if not gpath.is_file() or args.force_sample:
        write_sample_glasses_png(gpath)
    print("Assets ready.")


def _frac_args(args: argparse.Namespace) -> dict:
    return {
        "pupil_left_frac": args.pupil_left_frac,
        "pupil_right_frac": args.pupil_right_frac,
        "eyeline_frac": args.eyeline_frac,
    }


def cmd_demo(args: argparse.Namespace) -> None:
    cmd_init_assets(args)
    cache = PROJECT_ROOT / "assets" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    face_path = cache / "demo_face.jpg"
    if not face_path.is_file() or args.force_demo_face:
        download_file(DEMO_FACE_URL, face_path)
    out_path = Path(args.out)
    run_try_on(face_path, Path(args.glasses), out_path, Path(args.model), **_frac_args(args))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", type=str, default=str(DEFAULT_MODEL), help="Path to face_landmarker.task")
    p.add_argument("--glasses", type=str, default=str(DEFAULT_GLASSES), help="Glasses PNG with alpha")
    p.add_argument("--out", type=str, default=str(DEFAULT_OUT), help="Output image path")
    p.add_argument("--init-assets", action="store_true", help="Download model and create sample glasses PNG")
    p.add_argument("--demo", action="store_true", help="Init assets + download demo face + run try-on")
    p.add_argument("--force-sample", action="store_true", help="Overwrite sample glasses PNG")
    p.add_argument("--force-demo-face", action="store_true", help="Re-download demo face image")
    p.add_argument("--face", type=str, default="", help="Input face image (BGR readable by OpenCV)")
    p.add_argument(
        "--pupil-left-frac",
        type=float,
        default=None,
        help="Glasses PNG: horizontal fraction [0-1] of **left lens center** (default: module constant)",
    )
    p.add_argument(
        "--pupil-right-frac",
        type=float,
        default=None,
        help="Glasses PNG: horizontal fraction of **right lens center** (default: module constant)",
    )
    p.add_argument(
        "--eyeline-frac",
        type=float,
        default=None,
        help="Glasses PNG: vertical fraction [0-1] of lens-center height (default: module constant)",
    )
    args = p.parse_args()

    if args.init_assets and not args.demo:
        cmd_init_assets(args)
        return

    if args.demo:
        cmd_demo(args)
        return

    if not args.face:
        p.print_help()
        print("\nError: provide --face <path>, or use --demo / --init-assets.", file=sys.stderr)
        sys.exit(2)

    run_try_on(
        Path(args.face),
        Path(args.glasses),
        Path(args.out),
        Path(args.model),
        **_frac_args(args),
    )


if __name__ == "__main__":
    main()
