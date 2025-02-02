# WattpadDownloader（[演示链接](https://wpd.rambhat.la)）

一个简洁、易扩展的Web应用，用于将Wattpad上的书籍下载为EPUB格式文件。

![image](https://github.com/user-attachments/assets/b9d87d6b-5302-4561-98b0-d7f95bff9f04)

感谢您的星标 ⭐！

## 特性
- ⚡ 前端轻量，JavaScript最小化。
- 🪙 支持账户认证（可以下载您账户中的付费故事！）
- 🌐 支持API（更多信息请访问实例中的`/docs`路径）
- 🐇 快速生成，处理请求频率限制。
- 🐳 支持Docker容器部署。
- 🏷️ 生成的EPUB文件包含元数据（符合Dublin Core标准）。
- 📖 与电子阅读器兼容（支持Kindle、ReMarkable、KOBO、KOReader等）。
- 💻 易于修改和扩展。

## 使用说明

1. 克隆项目：  
   ```bash
   git clone https://github.com/XiaomingX/wattpad-downloader && cd wattpad-downloader
   ```

2. 构建Docker镜像：  
   ```bash
   docker build -t mynodeapp:1.0 .
   ```

2.2 查看编译好的Docker镜像
   ```bash
   docker images
   ```

3. 启动容器（以在3000启动为例子）：
   ```bash
   docker run -d -p 3000:80 wp_downloader
   ```

至此，你的实例已经搭建完成，可以通过 `http://localhost:3000` 访问。API文档可以通过 `http://localhost:3000/docs` 查看。

### 并发请求处理
文件缓存可能会在处理大量并发请求时遇到问题。如果你需要同时下载多个书籍，建议使用Redis缓存。假设你已经构建了镜像：

1. 配置 `.env` 文件。若使用Docker容器，`localhost`无法直接访问，你需要提供 [`host.docker.internal`](https://docs.docker.com/desktop/features/networking/#i-want-to-connect-from-a-container-to-a-service-on-the-host) 或其他平台特定的变体。
   
   ```bash
   USE_CACHE=true
   CACHE_TYPE=redis
   REDIS_CONNECTION_URL=redis://username:password@host:port
   ```

2. 启动容器并传入 `.env` 文件：
   ```bash
   docker run -d -p 5042:80 --env-file .env wp_downloader
   ```

或者，如果Redis运行在本地主机：
1. 修改 `.env` 文件，将 `localhost` 替换为 `host.docker.internal`。例如，`redis://localhost:6379` 应改为 `redis://host.docker.internal:6379`。
   
2. 启动容器：
   ```bash
   docker run -d -p 3000:80 --env-file .env --add-host host.docker.internal:host-gateway wp_downloader
   ```

---

特别感谢 [aerkalov/ebooklib](https://github.com/aerkalov/ebooklib) 提供的快速且文档完善的包。