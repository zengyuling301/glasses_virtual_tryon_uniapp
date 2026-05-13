# glasses_virtual_tryon

眼镜虚拟试戴 **MVP 技术方案**见 `docs/glasses_tryon_mvp.md`。本仓库提供最小 **Python Demo**：**MediaPipe Face Landmarker**（Tasks API）做人脸关键点，**透明 PNG 镜框**按瞳距缩放、旋转后 **Alpha 叠加**到人脸图。

## 环境

- Python **3.9+**（与 MediaPipe 官方 wheel 匹配；建议 3.10/3.11）
- 需要能访问 **Google Storage**（下载 `face_landmarker.task`）与演示用人脸图 URL（`--demo` 时）

```bash
cd glasses_virtual_tryon
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 一键演示

下载模型、生成本地占位镜框 PNG、拉取 OpenCV 示例人脸并输出合成图：

```bash
python demo/try_on.py --demo
# 默认输出: out/try_on.png
```

## 自备照片

先准备资源（模型 + 示例镜框，若无则生成）：

```bash
python demo/try_on.py --init-assets
```

再指定人脸与镜框（镜框需带 **Alpha**，且与脚本内 `PUPIL_*` / `EYELINE_FRAC` 对齐设计）：

```bash
python demo/try_on.py --face /path/to/selfie.jpg --glasses assets/frames/sample.png --out out/mine.png
```

## 调参

在 `demo/try_on.py` 顶部常量：

- `PUPIL_LEFT_FRAC` / `PUPIL_RIGHT_FRAC`：镜框 PNG 上「两瞳中心」水平占宽比例（0～1）
- `EYELINE_FRAC`：瞳高线在镜框图上的纵向比例（0～1）
- `LM_RIGHT_INNER` / `LM_LEFT_INNER`：MediaPipe 478 点模型内眦索引（默认 133 / 362）

## 为何不是 InsightFace

InsightFace 更强在识别/属性，试戴骨架只需稳定关键点；MediaPipe **安装与授权路径更简单**，故 Demo 优先 MediaPipe。若后续要统一人脸业务栈，可将 `detect_landmarks_rgb` 换为 InsightFace 输出同构的 `(N,3)` 像素坐标即可。

## 许可说明

`--demo` 使用的测试人脸为 OpenCV 仓库中的经典示例图，仅用于本地技术验证；正式产品请使用自有素材与合规授权。
