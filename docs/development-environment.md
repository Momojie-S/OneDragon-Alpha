# 开发环境搭建

## OpenSpec

OpenSpec 是项目使用的开发工作流工具，用于规范需求开发流程和变更管理。

官网：https://github.com/Fission-AI/OpenSpec

### 安装

使用 npm 全局安装最新版本：

```
npm install -g @fission-ai/openspec@latest
```

### 初始化

在项目根目录运行初始化命令，创建 OpenSpec 配置：

```
openspec init
```

### 更新

定期更新 OpenSpec 到最新版本：

```
openspec update
```

### 使用方式

项目通过 opsx 命令（OpenSpec 的封装）进行开发工作流管理，详见 CLAUDE.md 中的开发流程规范。

## Pyright

Pyright 是 Python 语言服务器（LSP Server），为 Claude Code 的 pyright-lsp 插件提供类型检查和代码智能功能。

官网：https://github.com/microsoft/pyright

### 功能

pyright-lsp 插件通过 Language Server Protocol 连接到 Pyright 服务，为 Claude Code 提供代码智能功能：

- 即时诊断：在每次编辑后立即显示错误和警告
- 代码导航：跳转到定义、查找引用、获取类型信息
- 语言感知：提供类型信息和代码符号文档

### 安装

使用 npm 全局安装 Pyright 语言服务器：

```
npm install -g pyright
```
