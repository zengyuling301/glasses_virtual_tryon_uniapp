# glasses_virtual_tryon

眼镜虚拟试戴的 **MVP 技术方案**见 [`docs/glasses_tryon_mvp.md`](docs/glasses_tryon_mvp.md)。本仓库实现 **2D 位图叠加**：**MediaPipe Face Landmarker**（Tasks API）做人脸关键点，**带 Alpha 的镜框 PNG** 按瞳距缩放、旋转后与自拍 **Alpha 合成**；Web 端在此基础上增加 **颊宽/瞳距归一化分档** 与镜架元数据规则，输出可解释的匹配状态与静态试戴图。

## 仓库结构

| 路径 | 说明 |
|------|------|
| `uni-app/` | **uni-app 前端**（对接 Flask MVP，对齐框线 v2.1.1 主流程） |
| `docs/glasses_tryon_mvp.md` | 产品与技术边界（MVP、预警、工时粗估等） |
| `demo/try_on.py` | 命令行试戴：下载模型、检测、叠加；含 `compose_try_on_bgr` 供 Web 复用 |
| `demo/app.py` | Flask Web：上传/拍照 → 分析 → 试戴 PNG |
| `demo/face_match.py` | 面宽代理指标、S/M/L 分档、`MATCH` / `WARN_*` 规则 |
| `demo/mvp_assets.py` | 生成 `assets/frames/catalog.json` 与 Demo 线框 PNG |
| `demo/templates/mvp.html` | 单页前端（界面状态文案为中文；API 仍为英文枚举） |
| `demo/static/mvp.css` | 页面样式 |
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

依赖要点：`mediapipe`、`opencv-python-headless`、`numpy`、`Pillow`、**`pillow-heif`**（iPhone **HEIC** 相册上传）、**`flask`**（Web MVP）。若已建 venv，更新依赖后需重新执行 `pip install -r requirements.txt …`。

国内若直连官方资源失败，可在同一 shell 中配置代理后再运行（`demo/try_on.py` 内 `download_file` 会读取 `http_proxy` / `https_proxy` / `ALL_PROXY`）：

```bash
export http_proxy=http://127.0.0.1:1087
export https_proxy=http://127.0.0.1:1087
export ALL_PROXY=socks5://127.0.0.1:1080
python demo/try_on.py --demo
```

## Web MVP（推荐演示）

流程：**上传或拍照（正面）→ 分析面宽分档 → 按规则推荐镜架 → 选择 SKU 生成试戴 PNG**。

```bash
source .venv/bin/activate
python demo/try_on.py --init-assets   # 若尚无 assets/face_landmarker.task
python demo/mvp_assets.py             # 写入 catalog 与 mvp_*.png；加 --force 可覆盖
python demo/app.py                    # 本机 http://127.0.0.1:5050 ；同网手机用 http://<电脑局域网IP>:5050
```

- 首次启动 `demo/app.py` 时，若缺少 `assets/frames/catalog.json` 或线框图，也会尝试自动补全（逻辑在 `mvp_assets.ensure_mvp_catalog`）。
- **上传大小**：默认单张约 **40MB**（`demo/app.py` 中 `MVP_MAX_UPLOAD_MB`）；超过会返回 **413** 与 JSON 说明。前面若有 **Nginx**，需同步增大 `client_max_body_size`，否则会先被 Nginx 拦下并返回 HTML 413。
- 结束服务：在运行 `app.py` 的终端 **Ctrl+C**，或结束对应 Python 进程。

**已戴眼镜检测误报（本地调试）**：启发式可能把眉毛/锐化自拍误判为镜框。已默认放宽；仍误报时可：

```bash
MVP_DISABLE_GLASSES_GUARD=1 python demo/app.py
```

**HTTP 接口（便于联调）**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 单页界面 |
| `GET` | `/api/catalog` | 镜架列表 JSON |
| `GET` | `/api/frame-preview/<frame_id>` | 返回该款镜架 PNG 线框图，供推荐列表缩略图展示 |
| `POST` | `/api/analyze` | `multipart/form-data` 字段 `face`：返回指标与推荐（`match_status` 为 `MATCH` / `WARN_TOO_NARROW` / `WARN_TOO_WIDE` / `LOW_CONFIDENCE`）；每条推荐含 `image` 文件名 |
| `POST` | `/api/tryon` | 字段 `face` + `frame_id`：返回合成 **PNG** |

正式商品请替换 `assets/frames/` 下透明 PNG，并在 `catalog.json` 中为每 SKU 配置 **`pupil_left_frac` / `pupil_right_frac` / `eyeline_frac`**（与镜圈光学中心对齐；试戴时脸侧锚点为**眼内外眼角中点**，纵向可配 **`nose_bridge_blend`** 混合鼻梁），以及业务字段（如 `band`、标称毫米宽等）。规则与方案文档中的「分档 + 预警」一致。

**注意**：Jinja2 会解析模板里的 `{{ … }}`。若在 `mvp.html` 的内联脚本中书写含双花括号的注释或字符串，需使用 `{% raw %}…{% endraw %}` 或避免 `{{`，否则首页会 500。

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
