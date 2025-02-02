# create-svelte

使用 [`create-svelte`](https://github.com/sveltejs/kit/tree/main/packages/create-svelte) 快速创建一个 Svelte 项目。

## 创建项目

如果你看到这个页面，说明你应该已经完成了这一步。恭喜！

```bash
# 在当前目录下创建新项目
npm create svelte@latest

# 在 my-app 目录下创建新项目
npm create svelte@latest my-app
```

## 开发

创建项目并安装好依赖（可以使用 `npm install`、`pnpm install` 或 `yarn`），然后启动开发服务器：

```bash
npm run dev

# 或者启动服务器并自动在浏览器中打开应用
npm run dev -- --open
```

## 构建

创建生产环境版本的应用：

```bash
npm run build
```

你可以通过 `npm run preview` 来预览生产版本。

> 部署时，你可能需要根据目标环境安装 [adapter](https://kit.svelte.dev/docs/adapters)。