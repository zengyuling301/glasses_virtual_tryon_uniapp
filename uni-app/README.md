# 开心玉米 AI 试戴 · uni-app 前端

与仓库内 **Flask 试戴 API**（`demo/app.py`）对接，交互对齐《分页框线设计图 v2.1.1》：P1 拍照 → P2 测算 → P3 试戴工作台 + 美化抽屉 + 完成 Sheet。

## 前置：启动后端

```bash
cd ..   # 仓库根目录 glasses_virtual_tryon
source .venv/bin/activate
python demo/try_on.py --init-assets
python demo/app.py   # 默认 http://0.0.0.0:5050
```

后端已支持：

- `Access-Control-Allow-Origin`（H5 跨域）
- `GET/POST /api/analyze`、`/api/tryon?wrap=1` 返回 base64 试戴图（供 uni-app 展示）

## 工程目录说明

uni-cli（Vite）要求页面与配置在 **`src/`** 下：

- `src/pages/`、`src/manifest.json`、`src/pages.json` 等
- 根目录保留 `package.json`、`vite.config.js`、`index.html`

## 配置 API 地址

| 访问方式 | API 推荐 |
|----------|----------|
| 电脑 `http://localhost:5173` | 默认 `''`，走 vite 代理 `/api` → `127.0.0.1:5050` |
| 手机 `http://192.168.x.x:5173` | **自动** `http://192.168.x.x:5050`（与页面同 IP） |

也可在 `.env.development` 手动指定：

```bash
VITE_API_BASE=http://192.168.110.61:5050
```

后端须监听局域网：`python demo/app.py`（默认 `0.0.0.0:5050`）。

## iOS Safari 与实时摄像头

用 **HTTP** 打开 `http://192.168.x.x:5173` 时，**iOS Safari 不允许 `getUserMedia` 实时预览**（浏览器安全策略，不是代码写错）。

- 页面会提示使用 **「前置拍照」**（系统相机，无实时预览）或 **「相册」**
- 若必须要实时预览：需 **HTTPS** 访问前端，或使用打包后的 App / 微信小程序

电脑 Chrome 通过 `localhost` 的 HTTP 可以实时预览。

## 实时人脸对齐框（H5）

拍照页在 Chrome 实时预览下会加载 **MediaPipe Face Landmarker**（与后端同系模型），根据瞳距、正脸程度、是否在框内等切换：

- **蓝框**：未达标，底部提示「请靠近/摆正/移至框中央」等  
- **绿框 + 橙点**：达标，短震动，「拍照」按钮可点  

首次进入需从 CDN 下载 wasm 与 `face_landmarker.task`（约数 MB）。若加载失败会降级为「可直接拍摄」。国内网络可先导出代理再 `npm run dev:h5`，或将模型放到 `public/models/face_landmarker.task` 并改 `faceGuide.js` 的 `MODEL_URL` 为 `/models/face_landmarker.task`（可从仓库 `assets/` 复制，需先 `python demo/try_on.py --init-assets`）。

## 没有 npm 时怎么办？

终端提示 `command not found: npm` 表示系统未安装 **Node.js（含 npm）**。任选其一：

### 1）Homebrew（macOS 常见）

```bash
brew install node
node -v && npm -v
cd uni-app
npm install
npm run dev:h5
```

国内可把 npm 源改为镜像（可选）：

```bash
npm config set registry https://registry.npmmirror.com
```

### 2）Conda（你当前是 `(base)` 环境，推荐）

```bash
conda install -c conda-forge nodejs=20
node -v && npm -v
```

若 `which node` 仍指向 Cursor 内置 node，请 **优先使用 conda 的 node**（与 npm 配对）：

```bash
export PATH="/opt/homebrew/Caskroom/miniforge/base/bin:$PATH"
# 或：conda activate base  后确认 which node 为 miniforge 路径
node -v   # 应显示 v20.x
npm -v
cd uni-app
npm install
npm run dev:h5
```

> Homebrew 在 macOS 26.x 上可能报错 `unknown or unsupported macOS version`，可暂时不用 brew，改用 Conda 或 HBuilderX。

### 3）不装 Node：用 HBuilderX（推荐无命令行时）

见下方「方式 A」，**不需要** `npm install`。

---

## 运行方式

### 方式 A：HBuilderX（推荐 · 无需 npm）

1. HBuilderX → 文件 → 导入 → 选择本目录 `uni-app`
2. 运行 → 运行到浏览器 / 运行到手机模拟器
3. 微信开发者工具需在微信后台配置 request 合法域名（本地调试可关域名校验）

### 方式 B：CLI

```bash
cd uni-app
npm install
npm run dev:h5
```

浏览器打开控制台提示的地址（通常 `http://localhost:5173`）。

## 页面说明

| 路由 | 说明 |
|------|------|
| `pages/capture/index` | P1：对齐框 + 点击拍照 + 3 秒倒计时 |
| `pages/analyzing/index` | P2：测算加载，自动请求 `/api/analyze` 并预合成 Top1 |
| `pages/workspace/index` | P3：试戴预览、横滑/缩略图换款、FAB 完成、上滑美化抽屉 |

## 与正式 1.0 的差异（当前仍走 2D MVP 后端）

- 试戴图为 **2D PNG 合成**，非 3D（后端能力决定）
- 面宽展示为 **S/M/L 分档**，非毫米（待算法升级）
- 美颜 / 发型 / 场景抽屉为 **UI 占位**，待接第三方
- 加购 / 无水印保存为 **Toast 示意**，待接 PHP 商品库

## 嵌入现有 APP

将本目录作为 **uni-app 子模块** 迁入甲方工程，或使用 `uni-app` 发行 **原生 App 资源** 后由原生壳加载。业务接口由 PHP 转发至同一 Flask 算法服务即可，前端仅需改 `API_BASE`。
