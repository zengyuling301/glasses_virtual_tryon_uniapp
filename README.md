# glasses_virtual_tryon

眼镜虚拟试戴 **MVP 技术方案**见 `docs/glasses_tryon_mvp.md`。本仓库提供最小 **Python Demo**：**MediaPipe Face Landmarker**（Tasks API）做人脸关键点，**透明 PNG 镜框**按瞳距缩放、旋转后 **Alpha 叠加**到人脸图。

## 环境

- Python **3.9+**（与 MediaPipe 官方 wheel 匹配；建议 3.10/3.11）
- 需要能访问 **Google Storage**（下载 `face_landmarker.task`）与演示用人脸图 URL（`--demo` 时）

```bash
cd glasses_virtual_tryon
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

（阿里云、腾讯云等镜像同理，将 `-i` / `trusted-host` 换成对应地址即可。）

**说明**：`face_landmarker.task` 与演示人脸图从 **Google Storage / GitHub** 拉取；若在国内直连失败，请先导出本机代理再运行（脚本内 `download_file` 会读取 `http_proxy` / `https_proxy` / `ALL_PROXY`）：

```bash
export http_proxy=http://127.0.0.1:1087
export https_proxy=http://127.0.0.1:1087
export ALL_PROXY=socks5://127.0.0.1:1080
python demo/try_on.py --demo
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

## 换人脸 / 换镜框再跑一遍（示例）

仓库提供脚本：下载 **512×512 随机头像**（pravatar）、**圆框 PNG（脚本内生成）**、以及 **Twemoji 眼镜位图**，各跑一张结果：

```bash
chmod +x demo/run_custom_example.sh   # 仅需一次
./demo/run_custom_example.sh 52       # 可选：pravatar 的 img 编号，默认 52
```

输出：`out/demo_custom_round.png`、`out/demo_custom_twemoji.png`。若拉取 pravatar / jsDelivr 需代理，先在当前 shell 里 `export http_proxy=...` 再执行脚本。

Twemoji 资源版权归 Twitter / X，授权以官方说明为准（通常需保留归属说明）；正式商用请替换为自有商品素材。

## 调参

在 `demo/try_on.py` 顶部常量（默认值与 `write_sample_glasses_png` 双圈示例一致）：

- `PUPIL_LEFT_FRAC` / `PUPIL_RIGHT_FRAC`：镜框 PNG 上 **左右镜片光学中心** 的水平位置（0～1，且左侧数值须小于右侧）。
- `EYELINE_FRAC`：镜片中心的纵向位置（0～1）。

人脸侧对齐使用 **虹膜环质心**（478 点模型末段 468–477）；若模型无虹膜点则退回内眦 133/362。瞳距按 **瞳孔（虹膜）中心** 计算，一般会比内眦略大，镜框整体也会略放大。

命令行可覆盖（便于不同商品 PNG 微调）：

```bash
python demo/try_on.py --face a.jpg --glasses g.png --out out/x.png \
  --pupil-left-frac 0.30 --pupil-right-frac 0.70 --eyeline-frac 0.52
```

## 为何不是 InsightFace

InsightFace 更强在识别/属性，试戴骨架只需稳定关键点；MediaPipe **安装与授权路径更简单**，故 Demo 优先 MediaPipe。若后续要统一人脸业务栈，可将 `detect_landmarks_rgb` 换为 InsightFace 输出同构的 `(N,3)` 像素坐标即可。

## 许可说明

`--demo` 使用的测试人脸为 OpenCV 仓库中的经典示例图，仅用于本地技术验证；正式产品请使用自有素材与合规授权。
