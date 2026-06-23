# 开心玉米 AI 试戴系统 · 后端 Git 操作指南

> **面向后端开发同事** | 零基础 Git 操作手册 | 照着步骤做就行

---

## 目录

- [第一步：安装 Git](#第一步安装-git)
- [第二步：配置身份（只需一次）](#第二步配置身份只需一次)
- [第三步：克隆仓库到本地](#第三步克隆仓库到本地)
- [第四步：拉取最新代码（每次工作前必须做）](#第四步拉取最新代码每次工作前必须做)
- [第五步：修改代码](#第五步修改代码)
- [第六步：提交代码](#第六步提交代码)
- [第七步：推送到 GitHub](#第七步推送到-github)
- [之后的日常工作流程](#之后的日常工作流程)
- [常见问题排查](#常见问题排查)
- [需要告诉前端同事的话](#需要告诉前端同事的话)

---

## 前提条件

1. 前端同事已在 GitHub 仓库给你发送了**邀请邮件**
2. 你已点击邮件中的链接，**接受了邀请**
3. 你知道自己注册 GitHub 时用的**邮箱地址**

如果还没收到邀请，请联系前端同事（项目负责人）发送邀请。

---

## 第一步：安装 Git

### Windows 电脑

1. 打开浏览器，访问：[`https://git-scm.com/download/win`](https://git-scm.com/download/win)
2. 下载安装包（`Git-2.x.x-64-bit.exe`），双击打开
3. **全部默认选项**，一路点击 **Next** 直到安装完成
4. 安装完成后，桌面右键菜单会多出一个 **"Git Bash Here"**

**验证安装成功**：

打开 **Git Bash**（桌面右键 → "Git Bash Here"），输入：

```bash
git --version
```

如果看到类似 `git version 2.43.0` 的输出，说明安装成功。

### Mac 电脑

1. 打开"终端"（Terminal）应用
2. 输入：

```bash
git --version
```

3. 如果提示需要安装，点击"安装"即可

---

## 第二步：配置身份（只需一次）

打开 **Git Bash**（Windows）或 **Terminal**（Mac），逐行执行以下命令：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的GitHub注册邮箱"
```

**⚠️ 注意**：邮箱必须是你**注册 GitHub 时用的邮箱**，否则后续推送会报错。

**示例**：

```bash
git config --global user.name "张三"
git config --global user.email "zhangsan@example.com"
```

---

## 第三步：克隆仓库到本地

打开 **Git Bash** 或 **Terminal**，逐行执行：

```bash
# 1. 进入你想放代码的目录（这里用桌面举例）
cd ~/Desktop

# 2. 克隆仓库（把下面的地址换成实际的仓库地址）
git clone https://github.com/zengyuling301/glasses_virtual_tryon_uniapp.git

# 3. 进入项目文件夹
cd glasses_virtual_tryon_uniapp
```

执行完成后，你的桌面上会多出一个 `glasses_virtual_tryon_uniapp` 文件夹，里面就是项目代码。

---

## 第四步：拉取最新代码（每次工作前必须做）

**⚠️ 这一步非常重要！** 每次你准备修改代码前，必须先执行：

```bash
git pull origin main
```

这会把前端同事最新提交的代码拉取到本地，确保你基于最新版本工作，避免代码冲突。

**正常输出示例**：

```
remote: Enumerating objects: 15, done.
remote: Counting objects: 100% (15/15), done.
Unpacking objects: 100% (15/15), done.
From github.com:zengyuling301/glasses_virtual_tryon_uniapp
 * branch            main       -> FETCH_HEAD
Updating d6dff1d..e769c04
Fast-forward
 ...
```

---

## 第五步：修改代码

### ⚠️ 重要规则：你只能改这些文件

**可以修改的目录**：`demo/` 文件夹下的所有文件

```
glasses_virtual_tryon_uniapp/
├── demo/          ← ✅ 你只改这里
│   ├── app.py
│   ├── face_match.py
│   ├── photo_guard.py
│   └── try_on.py
├── uni-app/       ← ❌ 不要碰！这是前端代码
├── docs/          ← ❌ 不要碰！
└── ...
```

**绝对不要修改**：
- `uni-app/` 目录下的任何文件（前端代码）
- 根目录下的 `README.md` 等文档
- `.gitignore` 等配置文件

用你习惯的编辑器（VS Code、PyCharm、Sublime 等）修改 `demo/` 下的文件，保存。

---

## 第六步：提交代码

修改完成后，打开 **Git Bash** 或 **Terminal**，确保当前在项目目录下（路径显示 `glasses_virtual_tryon_uniapp`），然后执行：

### 6.1 查看修改了哪些文件

```bash
git status
```

**正常输出示例**（只显示 demo/ 下的文件）：

```
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)

        modified:   demo/app.py
        modified:   demo/face_match.py
```

**⚠️ 如果看到 `uni-app/` 目录下的文件被修改**：

说明你误改了前端代码！请立即执行：

```bash
git checkout -- uni-app/
```

这会恢复误改的前端文件。然后重新执行 `git status` 确认。

### 6.2 把修改的文件加入暂存区

```bash
git add demo/
```

### 6.3 提交代码（写清楚你改了什么）

```bash
git commit -m "fix(demo/app.py): 修复 analyze 接口返回 500 错误"
```

#### commit 消息格式（必须遵守）

```
类型(文件路径): 简短说明，写明改了什么、为什么改
```

| 类型 | 含义 | 示例 |
|------|------|------|
| `fix` | 修复了 bug | `fix(demo/app.py): 修复上传图片超过 40MB 时返回 500 的问题` |
| `feat` | 新增了功能 | `feat(demo/face_match.py): 新增面宽适配三级判断逻辑` |
| `refactor` | 优化代码结构 | `refactor(demo/photo_guard.py): 优化已戴眼镜检测阈值` |
| `docs` | 修改注释或文档 | `docs(demo/app.py): 补充 API 接口注释说明` |

**示例**：

```bash
# 修复 bug
$ git commit -m "fix(demo/app.py): 修复 HEIC 图片解码失败时未回退 Pillow 的问题"

# 新增功能
$ git commit -m "feat(demo/face_match.py): 新增面宽 S/M/L 三档判断与适配标签输出"

# 优化代码
$ git commit -m "refactor(demo/photo_guard.py): 提高头姿 stress 阈值，减少误报"
```

---

## 第七步：推送到 GitHub

```bash
git push origin main
```

### 第一次推送时的额外操作

系统可能会弹出窗口让你登录 GitHub，或者在终端里提示输入用户名和密码。按提示操作即可：

- **用户名**：你的 GitHub 账号用户名
- **密码**：不是你的 GitHub 登录密码，而是 **Personal Access Token**（个人访问令牌）
  - 如果你不知道这个 Token，请告诉前端同事，让他帮你处理

**推送成功后的输出示例**：

```
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Writing objects: 100% (3/3), 312 bytes | 312.00 KiB/s, done.
Total 3 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2), completed with 2 local objects.
To github.com:zengyuling301/glasses_virtual_tryon_uniapp.git
   d6dff1d..e769c04  main -> main
```

**推送成功后，告诉前端同事**："我 push 了，你可以 pull 了。"

---

## 之后的日常工作流程

以后每次修改代码，重复以下 **4 个命令**：

```bash
# 1. 开始工作前，先拉取前端同事的最新代码
#    （这步很重要！如果前端同事也改了代码，必须先拉取）
git pull origin main

# 2. 修改 demo/ 下的文件
#    （用编辑器修改，保存）

# 3. 提交代码
git add demo/
git commit -m "fix(demo/xxx.py): 修改说明"

# 4. 推送到 GitHub
git push origin main
```

---

## 常见问题排查

### Q1: `git push` 提示 `Permission denied` 或 `Access denied`

**原因**：GitHub 邀请未接受，或权限不足。

**解决**：
1. 检查你的邮箱，找到 GitHub 邀请邮件，点击"接受邀请"
2. 如果找不到邮件，请让前端同事重新发送邀请
3. 或者检查你输入的用户名/密码（Token）是否正确

### Q2: `git push` 提示 `Everything up-to-date`

**原因**：没有新的修改需要提交。

**解决**：
1. 检查你是否保存了修改的文件
2. 执行 `git status` 查看是否有修改未提交
3. 如果确实没有修改，说明代码已经是最新的，无需推送

### Q3: `git status` 显示 `uni-app/` 目录下的文件被修改

**原因**：你误改了前端代码（可能是不小心打开或编辑了）。

**解决**：
```bash
# 恢复误改的前端文件
git checkout -- uni-app/

# 重新检查状态
git status
```

### Q4: 想撤销刚才的修改（还没提交）

```bash
# 撤销单个文件
git checkout -- demo/文件名.py

# 撤销 demo/ 目录下所有修改
git checkout -- demo/
```

### Q5: 提交了但发现还有遗漏的修改

```bash
# 修改遗漏的文件并保存

# 重新提交
$ git add demo/
$ git commit -m "fix(demo/xxx.py): 补充上次的修改，修复了 XXX"
$ git push origin main
```

### Q6: 提示 `fatal: not a git repository`

**原因**：你当前不在项目目录下。

**解决**：
```bash
# 进入项目目录
cd ~/Desktop/glasses_virtual_tryon_uniapp
```

### Q7: 提示 `Please tell me who you are`

**原因**：没有配置 Git 身份（第二步没有做）。

**解决**：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的GitHub注册邮箱"
```

### Q8: 提示 `CONFLICT` 或代码冲突

**原因**：前端同事和你同时修改了同一个文件。

**解决**：
1. **不要自己解决冲突**
2. 截图报错信息发给前端同事
3. 告诉前端同事你修改了哪些文件，让他帮你合并

---

## 需要告诉前端同事的话

每次你 push 成功后，请告诉前端同事以下信息：

1. **"我 push 了"** — 前端同事执行 `git pull origin main` 拉取你的代码
2. **我修改了哪些文件** — 例如："我改了 `demo/app.py` 和 `demo/face_match.py`"
3. **修改了什么** — 简单说明，例如："修复了 analyze 接口 500 错误"

**示例**：

> 我 push 了，改了 `demo/app.py` 和 `demo/photo_guard.py`。`app.py` 修复了上传图片超过 40MB 返回 500 的问题，`photo_guard.py` 提高了已戴眼镜检测的阈值。你可以 pull 了。

---

## 紧急联系人

- **遇到无法解决的问题**：立即停止操作，截图报错信息，发给前端同事
- **不要强行执行任何命令**（尤其是带 `--force` 的命令）

---

> **文档版本**：v1.0
> **适用仓库**：`https://github.com/zengyuling301/glasses_virtual_tryon_uniapp`
> **前端同事**：请在 GitHub 仓库设置中给后端同事发送 **Write** 权限的邀请
