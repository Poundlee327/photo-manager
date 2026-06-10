# PhotoLib — 摄影素材管理工具

> 本地照片库管理桌面应用，自动读取 EXIF、调用 Claude AI 识别拍摄主题，支持 AWS S3 云端备份。

![截图占位](docs/screenshot.png)

---

## 功能特性

- **EXIF 自动解析** — 导入时自动读取拍摄时间、相机型号、镜头、光圈、快门、ISO、GPS 坐标
- **AI 主题识别** — 调用 Claude Vision 分析图像内容，输出主题分类（风光/人像/街头/建筑…）、主体元素、描述文字和关键词标签
- **主题浏览** — 按 AI 分类结果筛选浏览，快速定位目标素材
- **多维搜索** — 支持关键词、日期范围、主题、相机型号组合筛选
- **云端备份** — 一键上传至 AWS S3，按 `年/月/日` 自动分层存储
- **GPS 地图** — 点击坐标直接跳转 Google Maps 查看拍摄地
- **缩略图缓存** — 导入时自动生成，页面加载快，AI 分析省 Token

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 API | Python 3.10 + FastAPI + SQLite |
| 前端 | React 18 + TypeScript + Tailwind CSS + Vite |
| 桌面壳 | Electron 28 |
| EXIF 解析 | Pillow + exifread |
| AI 分析 | Anthropic Claude claude-sonnet-4-6 (Vision) |
| 云存储 | AWS S3 (boto3) |

---

## 安装

### 环境要求

- Python 3.10 或以上
- Node.js 18 或以上
- npm

### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/<your-username>/photo-manager.git
cd photo-manager

# 2. 安装 Python 依赖
cd backend
pip install -r requirements.txt
cd ..

# 3. 安装前端依赖
cd frontend
npm install
cd ..
```

---

## 启动（开发模式）

**Windows：**双击 `start.bat`

**手动启动：**

```bash
# 终端 1 — 后端
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 终端 2 — 前端
cd frontend
npm run dev
```

浏览器打开 [http://localhost:3000](http://localhost:3000)

---

## 使用说明

### 1. 初始配置

首次打开后，进入左侧导航「**设置**」页：

| 字段 | 说明 | 必填 |
|------|------|------|
| Anthropic API Key | 从 [console.anthropic.com](https://console.anthropic.com) 获取 | AI 识别必填 |
| AWS Access Key ID | IAM 用户的访问密钥 | 云备份必填 |
| AWS Secret Access Key | IAM 用户的私钥 | 云备份必填 |
| S3 Bucket 名称 | 已创建的存储桶名称 | 云备份必填 |
| S3 Region | 存储桶所在区域，默认 `us-east-1` | 云备份必填 |
| 缩略图尺寸 | 默认 400px，越大越清晰但占空间 | 否 |

点击「保存设置」后即时生效。

---

### 2. 导入照片

1. 点击顶部「**导入文件夹**」按钮
2. 粘贴本地照片目录的完整路径，例如：
   - Windows：`D:\Photos\2024`
   - macOS：`/Users/yourname/Pictures/2024`
3. 点击「开始扫描」

导入过程会自动：
- 遍历目录下所有支持格式的图片（JPEG/PNG/TIFF/HEIC/RAW/CR2/NEF/ARW）
- 读取 EXIF 信息（拍摄时间、相机、镜头、GPS 等）
- 生成缩略图
- 跳过已导入的文件

完成后弹窗显示新增/跳过数量。

---

### 3. AI 主题识别

1. 在照片库中勾选要分析的照片（点击卡片左上角复选框）
2. 可点击「**全选**」批量操作
3. 点击「**AI 识别主题**」

每张照片会调用 Claude Vision 返回：
- **主题**：风光 / 人像 / 街头 / 建筑 / 生态 / 美食 / 运动 / 天文 等
- **主体元素**：最多 5 个描述词
- **一句话描述**：30 字以内
- **关键词标签**：场景、颜色、情绪、技法等维度，最多 10 个

已分析的照片卡片右上角会出现紫色 ✦ 图标。

> **提示**：分析费用按 Claude API 计费。建议先筛选重要照片再批量分析，或使用缩略图模式节省 Token。

---

### 4. 按主题浏览

左侧导航点击「**主题分类**」，顶部显示所有已识别的主题及数量，点击主题标签即可筛选对应照片。

---

### 5. 搜索照片

照片库顶部搜索栏支持：
- 输入关键词（匹配描述、标签、主题、文件名）
- 选择日期范围（拍摄日期）
- 点击「筛选」或回车搜索，「重置」清空条件

---

### 6. 查看照片详情

点击任意照片卡片，弹出详情面板，显示：
- 原图预览
- AI 描述、主体元素、关键词标签
- 完整 EXIF 参数（相机、镜头、焦距、光圈、快门、ISO、分辨率）
- GPS 坐标（可点击跳转 Google Maps）

---

### 7. 云端备份

进入「**云同步**」页面：
- 左侧显示待同步照片，右侧显示已同步照片
- 点击「同步全部」上传所有未同步照片
- 也可在照片库选中照片后点击「上传云端」单独同步

上传后文件存储路径格式：`s3://your-bucket/photos/2024/06/10/DSC_0001.jpg`

已同步照片卡片右上角显示蓝色云朵图标。

---

## 数据存储位置

应用数据默认保存在用户主目录：

```
~/.photo-manager/
├── library.db       # SQLite 数据库（照片元数据）
├── config.json      # 配置文件（API Key 等）
└── thumbnails/      # 缩略图缓存
```

**照片原文件不会被移动或复制**，应用只记录路径和元数据。

---

## 打包为桌面应用（可选）

```bash
# 根目录安装 Electron 依赖
npm install

# 编译前端
npm run build

# 打包（Windows 生成 .exe，macOS 生成 .dmg）
npm run dist
```

输出在 `dist-electron/` 目录。

---

## 支持的图片格式

| 格式 | 扩展名 |
|------|--------|
| JPEG | `.jpg` `.jpeg` |
| PNG | `.png` |
| TIFF | `.tiff` `.tif` |
| HEIC | `.heic` |
| WebP | `.webp` |
| RAW 通用 | `.raw` |
| Canon RAW | `.cr2` |
| Nikon RAW | `.nef` |
| Sony RAW | `.arw` |

---

## 常见问题

**Q: AI 分析失败，提示 API Key 未配置**
A: 进入「设置」页填写 Anthropic API Key 并保存。

**Q: 扫描提示目录不存在**
A: 确认路径正确，Windows 路径使用反斜杠如 `D:\Photos`。

**Q: 导入了大量照片，AI 分析费用贵吗？**
A: 应用使用缩略图（而非原图）发送给 Claude，大幅降低 Token 消耗。分析一张照片约消耗 500-800 Token。

**Q: 云同步失败**
A: 检查 AWS IAM 用户是否有 `s3:PutObject` 权限，Bucket 名称和 Region 是否正确。

---

## License

MIT
