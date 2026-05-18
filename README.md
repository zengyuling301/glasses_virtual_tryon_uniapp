# glasses_virtual_tryon

眼镜虚拟试戴的 **MVP 技术方案**见 [`docs/glasses_tryon_mvp.md`](docs/glasses_tryon_mvp.md)。本仓库实现 **2D 位图叠加**：**MediaPipe Face Landmarker**（Tasks API）做人脸关键点，**带 Alpha 的镜框 PNG** 按瞳距缩放、旋转后与自拍 **Alpha 合成**；后端提供面宽分档、镜架推荐与静态试戴图 API，**uni-app** 前端对接完整试戴流程。

## 仓库结构

| 路径 | 说明 |
|------|------|
| `uni-app/` | **uni-app 前端**（对接 Flask API，对齐框线 v2.1.1 主流程） |
| `docs/glasses_tryon_mvp.md` | 产品与技术边界（MVP、预警、工时粗估等） |
| `demo/try_on.py` | 命令行试戴：下载模型、检测、叠加；含 `compose_try_on_bgr` 供 API 复用 |
| `demo/app.py` | Flask API：上传 → 分析 → 试戴 PNG |
| `demo/face_match.py` | 面宽代理指标、S/M/L 分档、`MATCH` / `WARN_*` 规则 |
| `assets/frames/` | 镜架 PNG + `catalog.json`（SKU 与瞳距锚点参数） |
| `demo/run_custom_example.sh` | 随机头像 / Twemoji 等一键示例 |

## 环境

- Python **3.9+**（与 MediaPipe 官方 wheel 匹配；建议 3.10/3.11）
- 首次下载 **`face_landmarker.task`** 需能访问 **Google Storage**；`--demo` 还会拉取 OpenCV 示例人脸 **GitHub** URL

```bash
cd glasses_virtual_tryon
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

依赖要点：`mediapipe`、`opencv-python-headless`、`numpy`、`Pillow`、**`pillow-heif`**（iPhone **HEIC** 相册上传）、**`flask`**（试戴 API）。若已建 venv，更新依赖后需重新执行 `pip install -r requirements.txt …`。

国内若直连官方资源失败，可在同一 shell 中配置代理后再运行（`demo/try_on.py` 内 `download_file` 会读取 `http_proxy` / `https_proxy` / `ALL_PROXY`）：

```bash
export http_proxy=http://127.0.0.1:1087
export https_proxy=http://127.0.0.1:1087
export ALL_PROXY=socks5://127.0.0.1:1080
python demo/try_on.py --demo
```

## 启动（uni-app + 后端）

```bash
source .venv/bin/activate
python demo/try_on.py --init-assets   # 若尚无 assets/face_landmarker.task 与 sample.png
python demo/app.py                    # 默认 http://0.0.0.0:5050
```

另开终端启动前端，见 [`uni-app/README.md`](uni-app/README.md)。

- **镜架素材**：在 `assets/frames/` 放置带 Alpha 的 PNG，并维护 `catalog.json`（每 SKU 配置 `image`、`band`、`pupil_left_frac` / `pupil_right_frac` / `eyeline_frac` 等）。
- **上传大小**：默认单张约 **40MB**（环境变量 `MVP_MAX_UPLOAD_MB`）；超过返回 **413** JSON。前面若有 **Nginx**，需同步增大 `client_max_body_size`。
- 结束服务：在运行 `app.py` 的终端 **Ctrl+C**。

**已戴眼镜检测**：在 **uni-app 实时预览**阶段进行（蓝框提示「请摘下眼镜」）；`/api/analyze` 与 `/api/tryon` **不再重复检测**。后端 `photo_guard` 仍保留供 CLI 或其它调用。

**HTTP 接口**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | API 说明 JSON |
| `GET` | `/api/catalog` | 镜架列表 JSON |
| `GET` | `/api/frame-preview/<frame_id>` | 该款镜架 PNG 缩略图 |
| `POST` | `/api/analyze` | `multipart/form-data` 字段 `face`：指标与推荐 |
| `POST` | `/api/tryon` | 字段 `face` + `frame_id`：合成 PNG（`?wrap=1` 或头 `X-Tryon-Wrap: 1` 返回 base64 JSON） |

正式商品请替换 `assets/frames/` 下透明 PNG，并在 `catalog.json` 中为每 SKU 配置瞳距锚点与业务字段。规则与方案文档中的「分档 + 预警」一致。

## 命令行一键演示

下载模型、生成本地示例镜框、拉取 OpenCV 示例人脸并输出合成图：

```bash
python demo/try_on.py --demo
# 默认输出: out/try_on.png（目录见 .gitignore）
```

## 命令行：自备人脸与镜框

先准备模型与示例镜框（若无则生成）：

```bash
python demo/try_on.py --init-assets
```

再指定人脸与镜框（镜框需带 **Alpha**，且与设计稿一致的 **`PUPIL_*` / `EYELINE_FRAC`** 对齐）：

```bash
python demo/try_on.py --face /path/to/selfie.jpg --glasses assets/frames/sample.png --out out/mine.png
```

## 换人脸 / 换镜框示例脚本

下载 **512×512 随机头像**（pravatar）、脚本生成的圆框、以及 **Twemoji** 眼镜位图，各输出一张：

```bash
chmod +x demo/run_custom_example.sh   # 仅需一次
./demo/run_custom_example.sh 52         # 可选 pravatar 图片编号，默认 52
```

输出：`out/demo_custom_round.png`、`out/demo_custom_twemoji.png`。若访问 pravatar / jsDelivr 需代理，请先在同一 shell 中 `export http_proxy=...`。

Twemoji 资源版权归 Twitter / X，授权以官方说明为准；正式商用请替换为自有商品素材。

## 调参（CLI 与默认镜框）

在 `demo/try_on.py` 顶部常量（与 `write_sample_glasses_png` 双圈示例一致）：

- `PUPIL_LEFT_FRAC` / `PUPIL_RIGHT_FRAC`：镜框 PNG 上 **左右镜片光学中心** 的水平比例（0～1，左须小于右）。
- `EYELINE_FRAC`：镜片中心纵向比例（0～1）。

对齐使用 **虹膜环质心**（478 点模型 468–477）；无虹膜点时退回内眦 133/362。命令行可覆盖：

```bash
python demo/try_on.py --face a.jpg --glasses g.png --out out/x.png \
  --pupil-left-frac 0.30 --pupil-right-frac 0.70 --eyeline-frac 0.52
```

## 为何不是 InsightFace

InsightFace 更强在识别与属性；试戴骨架只需稳定关键点。MediaPipe **安装与授权路径更简单**，故 Demo 优先 MediaPipe。若后续要统一人脸业务栈，可将 `detect_landmarks_rgb` 换为 InsightFace，并保持同构的 `(N,3)` 像素坐标输出。

## 许可说明

`--demo` 使用的测试人脸来自 OpenCV 仓库经典示例图，仅用于本地技术验证；正式产品请使用自有素材与合规授权。
