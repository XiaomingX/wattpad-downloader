# Wattpad Downloader (TXT Mode)

一个基于 Python 和 Chainlit 实现的专家级 Wattpad 书籍下载工具。它可以自动处理长章节分页，并将书籍内容以结构化的 TXT 格式保存到本地。

![image](https://github.com/user-attachments/assets/b9d87d6b-5302-4561-98b0-d7f95bff9f04)

## 特性
- 🚀 **专家级抓取**: 自动识别并爬取 Wattpad 长章节的内部分页内容。
- 文本化存储**: 将书籍保存为文件夹结构，每个章节对应一个独立命名的 `.txt` 文件。
- 📊 **元数据整合**: 自动提取并生成 `metadata.txt` 和封面图 `cover.jpg`。
- ⚡ **Chainlit 2.x 驱动**: 提供优雅的异步交互界面，通过 `cl.Step` 实时展示任务流。
- 🛠️ **高性能异步**: 基于 `aiohttp` 实现连接复用，下载速度快且稳定。
- 🌐 **代理支持**: 完美支持系统环境变量代理。
- 📦 **现代化管理**: 使用 `uv` 进行毫秒级的依赖同步。

## 目录结构示例
下载后的书籍将按如下结构存储：
```text
downloads/
└── phantom-me_311395088/
    ├── metadata.txt       # 书籍详细信息
    ├── cover.jpg          # 书籍封面
    ├── 001_Prologue.txt   # 章节内容
    ├── 002_Chapter One.txt
    └── ...
```

## 快速开始

### 本地开发

1. **安装 uv** (如果尚未安装):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **克隆项目并安装依赖**:
   ```bash
   git clone https://github.com/XiaomingX/wattpad-downloader && cd wattpad-downloader
   uv sync
   ```

3. **设置代理 (可选)**:
   ```bash
   export http_proxy=http://127.0.0.1:10808
   export https_proxy=http://127.0.0.1:10808
   ```

4. **运行应用**:
   ```bash
   uv run chainlit run app.py
   ```
   访问 `http://localhost:8000` 即可开始使用。

## 使用说明

- 在输入框中粘贴 Wattpad 故事的 URL (支持 Story URL 或 Chapter URL) 或 故事 ID。
- 程序会自动在后台并发抓取所有章节。
- 下载完成后，书籍文件夹将出现在项目的 `downloads/` 目录下。

---

*注：本项目已从 EPUB 生成模式切换为结构化 TXT 存储模式，以提供更好的文本管理体验。*