"""Generate demo frame PNGs and catalog.json for the MVP web demo."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_DIR = PROJECT_ROOT / "assets" / "frames"
CATALOG_PATH = FRAMES_DIR / "catalog.json"


def write_round_glasses_png(
    dest: Path,
    *,
    pupil_left_frac: float,
    pupil_right_frac: float,
    eyeline_frac: float,
    rim_frac: float,
) -> None:
    """Wireframe round frame; rim_frac is lens radius as fraction of min(w,h)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = 900, 420
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx1 = int(pupil_left_frac * w)
    cx2 = int(pupil_right_frac * w)
    cy = int(eyeline_frac * h)
    r = int(min(w, h) * rim_frac)
    for cx in (cx1, cx2):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(35, 35, 35, 255), width=10)
    draw.line((cx1 + int(r * 0.55), cy, cx2 - int(r * 0.55), cy), fill=(35, 35, 35, 230), width=8)
    draw.line((cx1 - r, cy, 18, cy + 8), fill=(35, 35, 35, 200), width=7)
    draw.line((cx2 + r, cy, w - 18, cy + 8), fill=(35, 35, 35, 200), width=7)
    img.save(dest, format="PNG")


def ensure_mvp_catalog(*, force: bool = False) -> Path:
    """Write catalog.json and per-SKU PNGs if missing (or when force=True)."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    if CATALOG_PATH.is_file() and not force:
        return CATALOG_PATH

    # band: S = 相对窄脸, M = 中等, L = 相对宽脸（与 cheek_span / IPD 分档对齐，见 demo/face_match.py）
    frames = [
        {
            "id": "frame-narrow",
            "name": "窄版圆框",
            "band": "S",
            "image": "mvp_narrow.png",
            "pupil_left_frac": 0.36,
            "pupil_right_frac": 0.64,
            "eyeline_frac": 0.50,
            "mm_total_width": 128,
            "blurb": "镜圈总宽偏小，适合脸颊相对较窄的脸型。",
        },
        {
            "id": "frame-medium",
            "name": "标准圆框",
            "band": "M",
            "image": "mvp_medium.png",
            "pupil_left_frac": 0.32,
            "pupil_right_frac": 0.68,
            "eyeline_frac": 0.50,
            "mm_total_width": 138,
            "blurb": "中等镜圈宽度，适合大多数脸型。",
        },
        {
            "id": "frame-wide",
            "name": "加宽圆框",
            "band": "L",
            "image": "mvp_wide.png",
            "pupil_left_frac": 0.28,
            "pupil_right_frac": 0.72,
            "eyeline_frac": 0.50,
            "mm_total_width": 148,
            "blurb": "镜圈总宽偏大，适合脸颊相对较宽的脸型。",
        },
    ]

    for f in frames:
        img_name = f["image"]
        dest = FRAMES_DIR / img_name
        if force or not dest.is_file():
            rim = {"S": 0.16, "M": 0.19, "L": 0.22}[f["band"]]
            write_round_glasses_png(
                dest,
                pupil_left_frac=float(f["pupil_left_frac"]),
                pupil_right_frac=float(f["pupil_right_frac"]),
                eyeline_frac=float(f["eyeline_frac"]),
                rim_frac=rim,
            )

    payload = {"version": 1, "frames": frames}
    CATALOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return CATALOG_PATH


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Write MVP frame PNGs + catalog.json")
    p.add_argument("--force", action="store_true", help="Overwrite catalog and PNGs")
    args = p.parse_args()
    path = ensure_mvp_catalog(force=args.force)
    print(path)
