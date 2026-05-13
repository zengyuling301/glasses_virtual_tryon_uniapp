#!/usr/bin/env bash
# 使用「新人脸 + 新镜框图」跑一遍试戴（不依赖 --demo 的 Lena）。
# 人脸：pravatar.cc 512 头像（可换 ?img= 编号）
# 镜框 A：本脚本生成的圆框 PNG（矢量风格）
# 镜框 B：Twemoji 眼镜位图（CC-BY-4.0，见 https://twemoji.twitter.com/ ）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p assets/cache out

IMG_ID="${1:-52}"
FACE_URL="https://i.pravatar.cc/512?img=${IMG_ID}"
TWEMOJI_GLASSES_URL="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f453.png"

echo "==> Face: ${FACE_URL}"
curl -fsSL -o assets/cache/custom_face.jpg "${FACE_URL}"

echo "==> Glasses (round PNG, generated)"
. .venv/bin/activate
python - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw

out = Path("assets/cache/custom_glasses_round.png")
w, h = 880, 400
img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
cx1, cx2 = int(w * 0.34), int(w * 0.66)
cy = int(h * 0.50)
r = int(min(w, h) * 0.19)
for cx in (cx1, cx2):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(18, 18, 22, 255), width=9)
d.line((cx1 + int(r * 0.55), cy, cx2 - int(r * 0.55), cy), fill=(18, 18, 22, 255), width=7)
d.line((cx1 - r, cy, 12, cy + 6), fill=(18, 18, 22, 210), width=6)
d.line((cx2 + r, cy, w - 12, cy + 6), fill=(18, 18, 22, 210), width=6)
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out, format="PNG")
print("wrote", out)
PY

echo "==> Try-on (round glasses) -> out/demo_custom_round.png"
python demo/try_on.py \
  --face assets/cache/custom_face.jpg \
  --glasses assets/cache/custom_glasses_round.png \
  --out out/demo_custom_round.png

echo "==> Glasses (Twemoji bitmap) -> assets/cache/custom_glasses_twemoji.png"
curl -fsSL -o assets/cache/custom_glasses_twemoji.png "${TWEMOJI_GLASSES_URL}"

echo "==> Try-on (Twemoji glasses) -> out/demo_custom_twemoji.png"
python demo/try_on.py \
  --face assets/cache/custom_face.jpg \
  --glasses assets/cache/custom_glasses_twemoji.png \
  --out out/demo_custom_twemoji.png

ls -la out/demo_custom_round.png out/demo_custom_twemoji.png
