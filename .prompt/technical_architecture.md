# 技术架构文档 (Technical Architecture)

## 技术栈现状

### 核心依赖
- **Python**: >=3.10
- **Web 框架**: Chainlit >=1.1.300
- **HTTP 客户端**: aiohttp >=3.9.1
- **缓存**: aiohttp-client-cache (自定义 fork)
- **HTML 解析**: BeautifulSoup4 + lxml
- **配置管理**: pydantic-settings >=2.6.1
- **日志**: eliot >=1.16.0
- **重试**: backoff >=2.2.1

### 过时依赖识别

#### [x] 1. ebooklib 未使用
**现状**: `ebooklib>=0.18` 在依赖列表中但代码中无引用
**原因**: 已从 EPUB 模式切换为 TXT 模式
**操作**: 从 `pyproject.toml` 移除

#### [ ] 2. eliot 日志系统过于复杂
**现状**: 使用 `eliot` 进行结构化日志，但仅在 DEBUG 模式写入文件
**问题**: 
- 学习曲线陡峭
- 与 Chainlit 的日志系统不集成
- `EliotHandler` 配置冗余
**方案**:
- 迁移到标准 `logging` 模块
- 使用 `rich` 的 `RichHandler` 提升终端输出
- 保留 JSON 日志可选项

#### [ ] 3. aiohttp-client-cache 使用自定义 fork
**现状**: 
```toml
[tool.uv.sources]
aiohttp-client-cache = { git = "https://github.com/TheOnlyWayUp/aiohttp-client-cache.git", rev = "keydb-ttl" }
```
**风险**:
- 依赖不稳定的个人 fork
- 无法获取上游更新
- 维护成本高
**方案**:
- 评估是否可以使用官方版本
- 如需 KeyDB TTL 功能，考虑直接使用 Redis 客户端
- 或提交 PR 到上游合并功能

## 架构分层

### 当前结构
```
app.py          # Chainlit 视图层 (UI + 流程编排)
core.py         # 业务逻辑层 (API 调用 + 数据处理)
.chainlit/      # Chainlit 配置
downloads/      # 数据存储层
```

### [ ] 4. 缺少清晰的模块划分
**现状**: `core.py` 混合了多种职责
**问题**:
- API 调用
- 数据模型
- 工具函数
- 配置管理
- 缓存逻辑
**方案**: 重构为模块化结构
```
src/
├── api/
│   ├── client.py      # HTTP 客户端封装
│   └── wattpad.py     # Wattpad API 调用
├── models/
│   └── story.py       # Pydantic 模型
├── services/
│   ├── downloader.py  # 下载服务
│   └── cleaner.py     # 内容清洗
├── utils/
│   ├── cache.py       # 缓存配置
│   └── text.py        # 文本工具 (slugify)
└── config.py          # 配置管理
```

## 性能优化机会

### [ ] 5. 并发控制缺失
**现状**: 使用 `for idx, part in enumerate()` 串行下载章节
**影响**: 下载速度慢
**方案**:
```python
# 使用 asyncio.gather 并发下载
tasks = [download_chapter(part, ...) for part in metadata["parts"]]
results = await asyncio.gather(*tasks, return_exceptions=True)
```
**注意**: 需添加信号量限制并发数

### [ ] 6. 缓存策略不合理
**现状**: 
- 全局 12 小时过期时间
- 无差异化缓存策略
**问题**:
- Story 元数据可能更新（新章节）
- Part 内容基本不变
**方案**:
- Story API: 1 小时缓存
- Part Content: 7 天缓存
- Cover 图片: 永久缓存

### [ ] 7. 文件 I/O 阻塞事件循环
**现状**: 使用 `cl.make_async()` 包装同步写入
**问题**: 虽然不阻塞，但效率不高
**方案**:
- 使用 `aiofiles` 进行真正的异步文件操作
- 批量写入减少 I/O 次数

## 代码质量问题

### [ ] 8. 类型注解不完整
**现状**: 部分函数缺少返回类型注解
**影响**: IDE 提示不友好，类型安全性差
**方案**:
- 启用 `mypy` 或 `pyright` 检查
- 补全所有函数签名

### [ ] 9. 错误处理粗糙
**现状**: 
```python
except Exception as e:
    logger.exception("Download failed")
    await cl.Message(content=f"An error occurred: {str(e)}").send()
```
**问题**: 
- 捕获所有异常过于宽泛
- 用户看到的错误信息不友好
**方案**:
- 定义自定义异常类
- 分类处理网络错误、解析错误、文件错误
- 提供可操作的错误提示

### [ ] 10. 魔法数字和硬编码
**现状**:
```python
if page > 50: break  # 硬编码最大页数
if len(body) < 10: break  # 魔法数字
```
**方案**: 提取为配置常量
```python
MAX_PAGES_PER_CHAPTER = 50
MIN_CONTENT_LENGTH = 10
```

## 安全性问题

### [ ] 11. 路径遍历风险
**现状**: 使用用户输入的书名创建目录
**风险**: 恶意书名可能包含 `../` 等路径遍历字符
**方案**:
- 强化 `slugify()` 函数
- 使用 `Path.resolve()` 验证最终路径在 `downloads/` 内

### [ ] 12. 代理配置暴露
**现状**: `trust_env=True` 自动读取系统代理
**风险**: 可能泄露内网代理配置
**方案**:
- 添加显式代理配置选项
- 在 UI 中提示当前使用的代理

## 部署与运维

### [ ] 13. Dockerfile 优化
**现状**:
```dockerfile
RUN uv sync --no-install-project
COPY core.py .
COPY app.py .
```
**问题**:
- 代码变更会导致依赖层重建
- 缺少健康检查
**方案**:
```dockerfile
# 先复制依赖文件
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 再复制代码
COPY . .

# 添加健康检查
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1
```

### [ ] 14. 缺少环境变量验证
**现状**: `.env_template` 存在但无强制校验
**风险**: 生产环境配置错误
**方案**:
- 使用 Pydantic Settings 的 `@validator` 强制校验
- 启动时打印配置摘要

### [ ] 15. 无监控和指标
**现状**: 无 Prometheus/Grafana 集成
**影响**: 无法监控下载成功率、性能瓶颈
**方案**:
- 添加 `prometheus-client` 依赖
- 暴露 `/metrics` 端点
- 记录关键指标：
  - 下载请求数
  - 平均下载时长
  - 缓存命中率
  - 错误率

## 测试覆盖

### [ ] 16. 完全缺少测试
**现状**: 无 `tests/` 目录
**风险**: 重构困难，回归风险高
**方案**:
- 添加 `pytest` + `pytest-asyncio`
- 优先覆盖核心逻辑：
  - `fetch_part_content()` 分页逻辑
  - `clean_content()` HTML 清洗
  - `slugify()` 边界情况
- 使用 `aioresponses` mock HTTP 请求

## 依赖管理

### [ ] 17. uv.lock 未提交
**现状**: `.gitignore` 可能排除了 `uv.lock`
**问题**: 无法保证依赖版本一致性
**方案**: 
- 确保 `uv.lock` 被提交到版本控制
- CI/CD 使用 `uv sync --frozen`

### [ ] 18. 依赖版本过于宽松
**现状**: `aiohttp>=3.9.1` 无上限
**风险**: 未来版本可能引入破坏性变更
**方案**: 使用兼容性版本约束
```toml
aiohttp = "^3.9.1"  # 等价于 >=3.9.1,<4.0.0
```

## Chainlit 特定问题

### [ ] 19. 未充分利用 Chainlit 2.x 特性
**现状**: 仅使用基础的 `cl.Message` 和 `cl.Step`
**可用但未使用的功能**:
- `cl.Action` 交互按钮（如"重试失败章节"）
- `cl.Avatar` 自定义头像
- `cl.ChatSettings` 动态配置（格式选择、并发数）
- `cl.on_settings_update` 实时配置更新

### [ ] 20. 配置文件冗余
**现状**: `.chainlit/config.toml` 包含大量默认值注释
**方案**: 仅保留自定义配置，删除注释行

## 国际化

### [ ] 21. 多语言支持不完整
**现状**: 
- 存在 `chainlit.zh.md` 但未在配置中指定
- UI 文案硬编码英文
**方案**:
- 在 `config.toml` 设置 `language = "zh-CN"`
- 使用 `.chainlit/translations/zh-CN.json` 覆盖默认文案

## 技术债务优先级

### 高优先级 (影响功能/安全)
1. [x] 移除 `ebooklib` 冗余依赖
2. [ ] 修复路径遍历安全风险
3. [ ] 实现并发下载提升性能
4. [ ] 添加错误恢复机制

### 中优先级 (提升质量)
5. [ ] 重构模块化结构
6. [ ] 迁移日志系统到标准库
7. [ ] 补全类型注解
8. [ ] 添加核心功能测试

### 低优先级 (优化体验)
9. [ ] 优化 Dockerfile
10. [ ] 充分利用 Chainlit 特性
11. [ ] 添加监控指标
12. [ ] 完善国际化
