# PhotoLib 安装与启动

## 环境要求
- Python 3.10+
- Node.js 18+
- npm

## 一次性安装

### 1. 安装 Python 依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装前端依赖
```bash
cd frontend
npm install
```

## 启动（开发模式）

双击 `start.bat` 即可，或手动：

```bash
# 终端1 - 后端
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 终端2 - 前端
cd frontend
npm run dev
```

浏览器打开 http://localhost:3000

## 配置

首次使用需在「设置」页面填写：
- **Anthropic API Key**：从 https://console.anthropic.com 获取，用于 AI 主题识别
- **AWS 配置**（可选）：S3 存储桶信息，用于云端备份

配置保存在 `~/.photo-manager/config.json`，数据库在 `~/.photo-manager/library.db`

## 功能说明

| 功能 | 说明 |
|------|------|
| 导入文件夹 | 粘贴本地照片目录路径，自动读取 EXIF |
| AI 识别主题 | 选中照片后点击，调用 Claude Vision 分析 |
| 主题分类页 | 按风光/人像/街头等主题浏览 |
| 云端同步 | 上传原图到 S3，支持按年/月/日分层存储 |
| 搜索 | 支持按描述、标签、主题、相机型号搜索 |

## 打包为桌面应用（可选）

```bash
# 根目录
npm install
npm run build        # 编译前端
npm run dist         # 打包为 .exe/.dmg
```
