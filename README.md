# Wattpad 下载器

基于 Python 和 Chainlit 的 Wattpad 书籍下载工具，支持自动处理长章节分页，将书籍内容保存为结构化的 TXT 文件。

## 功能特性

- 🚀 自动识别并抓取 Wattpad 长章节的分页内容
- 📝 将书籍保存为文件夹结构，每个章节对应独立的 `.txt` 文件
- 📊 自动提取并生成元数据文件和封面图
- ⚡ 基于 Chainlit 2.x 的优雅异步交互界面
- 🛠️ 高性能异步架构，基于 `aiohttp` 实现连接复用
- 🌐 支持系统代理配置
- 📦 使用 `uv` 进行快速依赖管理

## 系统要求

- Python >= 3.10
- uv (Python 包管理器)

## 快速开始

### 1. 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆项目并安装依赖

```bash
git clone <repository-url>
cd wattpad-downloader
uv sync
```

### 3. 配置代理 (可选)

```bash
export http_proxy=http://127.0.0.1:10808
export https_proxy=http://127.0.0.1:10808
```

### 4. 运行应用

**推荐方式 (在新终端中运行):**

```bash
# 打开新终端，进入项目目录
cd wattpad-downloader

# 使用 uv run 启动
uv run chainlit run app.py --port 8000
```

**备选方式:**

```bash
# 方式 1: 使用启动脚本
./run.sh

# 方式 2: 激活虚拟环境
source .venv/bin/activate
chainlit run app.py --port 8000

# 方式 3: 直接使用虚拟环境中的 Python
.venv/bin/python -m chainlit run app.py --port 8000
```

访问 http://localhost:8000 开始使用。

**注意**: 如果遇到 Python 版本兼容性问题，请确保在新的终端会话中运行。

## 使用说明

1. 在输入框中粘贴 Wattpad 故事的 URL 或故事 ID
   - 支持故事 URL: `https://www.wattpad.com/story/123456789`
   - 支持章节 URL: `https://www.wattpad.com/123456789`
   - 支持纯数字 ID: `123456789`

2. 程序会自动在后台并发抓取所有章节

3. 下载完成后，书籍文件夹将出现在 `downloads/` 目录下

## 下载目录结构

```
downloads/
└── 书名_故事ID/
    ├── metadata.txt       # 书籍详细信息
    ├── cover.jpg          # 书籍封面
    ├── 001_章节标题.txt   # 章节内容
    ├── 002_章节标题.txt
    └── ...
```

## 开发指南

### 运行测试

```bash
uv run python tests/run_tests.py
```

### 项目结构

```
wattpad-downloader/
├── app.py              # Chainlit 应用入口
├── core.py             # 核心业务逻辑
├── run.sh              # 启动脚本
├── pyproject.toml      # 项目配置
├── tests/              # 测试目录
│   ├── test_core.py    # 核心功能测试
│   ├── test_app.py     # 应用层测试
│   └── run_tests.py    # 测试运行脚本
└── downloads/          # 下载输出目录
```

### 技术栈

- **Web 框架**: Chainlit 1.1.300+
- **HTTP 客户端**: aiohttp 3.9.1+
- **HTML 解析**: BeautifulSoup4 + lxml
- **数据验证**: Pydantic 2.6.1+
- **日志记录**: eliot 1.16.0+
- **缓存**: aiohttp-client-cache
- **测试**: pytest + pytest-asyncio

### 核心特性

- 异步 I/O 架构提升性能
- 自动重试机制 (backoff)
- 响应缓存 (12 小时过期)
- 完整的类型注解
- 单元测试覆盖

## 配置选项

可通过 `.env` 文件配置:

```env
USE_CACHE=true
CACHE_TYPE=file
DEBUG=false
```

## 优化记录

详细的优化记录和测试结果请查看 [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)

## 许可证

请查看 LICENSE 文件
