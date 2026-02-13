# Proposal: 项目文档重构

## Why

当前 CLAUDE.md 混合了多种职责的内容（项目概述、技术栈、开发规范、AI 指令等），导致：
- 文档过长且职责不清，难以维护
- 项目架构和设计说明散落在 `docs/develop` 目录下，结构不清晰
- 开发规范与项目说明混杂在一起，不便于人类开发者查阅

通过文档重构，实现：
- **CLAUDE.md** 专注于 AI 助手的工作指令和注意事项
- **独立的项目文档** 便于人类阅读和理解项目
- **清晰的文档层次** 提高可维护性

## What Changes

### 文档结构调整

1. **创建项目概览文档** (`docs/project-overview.md`)
   - 项目概述、技术栈、目录结构
   - 环境说明（服务端口、依赖）
   - 从 CLAUDE.md 的"项目概述"部分迁移

2. **创建开发规范文档** (`docs/development-guide.md`)
   - 后端开发规范（编码风格、类型提示、导入约定等）
   - 前端开发规范
   - 测试策略（单元测试、E2E 测试、测试数据清理）
   - 开发流程（需求开发流程、opsx 使用）
   - 从 CLAUDE.md 的"开发流程规范"、"开发规范"部分迁移

3. **重组 `docs/` 目录结构**

   建议的新结构：
   ```
   docs/
   ├── README.md                      # 文档导航索引（新建）
   ├── project-overview.md            # 项目概览（新建）
   ├── development-guide.md           # 开发规范（新建）
   ├── documentation-guide.md         # 文档规范（新建）
   ├── architecture/                  # 架构设计（新建目录）
   │   └── alpha-architecture.md
   ├── modules/                       # 模块文档（保留并整理）
   │   └── model-config/
   ├── features/                      # 功能文档（新建目录）
   │   ├── backend/
   │   └── frontend/
   ├── manual/                       # 产品使用手册（新建目录，空白）
   └── database/                      # 数据库文档（保留）
   ```

   具体调整：
   - 创建 `architecture/` 目录，移动 `develop/alpha-architecture.md`
   - 创建 `features/` 目录，移动 `develop/backend/` 和 `develop/frontend/`
   - 创建 `manual/` 目录（空白，用于将来放置产品使用手册）
   - 整理 `modules/model-config/`，按子模块组织文档
   - 删除 `develop/` 目录（内容已重新组织）
   - 创建 `README.md` 作为文档索引

4. **简化 CLAUDE.md**
   - 保留 AI 助手特有的工作指令
   - 使用 `@path/to/file` 语法引用项目文档
   - 移除重复的项目说明和开发规范内容

### 文档规范

创建 `docs/documentation-guide.md`，明确项目文档编写规范：

**核心原则**：
- **简洁优先** - 避免冗余，每句话都要有价值
- **设计导向** - 突出核心设计思路和架构决策，而非实现细节
- **无代码示例** - 文档中不包含具体实现代码
- **无代码片段** - 避免粘贴配置文件或代码片段
- **概念清晰** - 用自然语言描述"是什么"和"为什么"

**文档应包含**：
- 设计目标和核心思路
- 架构概览和模块关系
- 关键决策的背景原因
- 接口定义和数据流（如果需要）
- 开发流程和规范要点

**文档不应包含**：
- 具体实现代码
- 代码示例（hello world 级别的示例也不需要）
- 详细的配置文件内容
- IDE 使用教程
- 第三方库的基础教程（可通过链接引用官方文档）

此规范将应用于 `docs/` 下的所有文档。

### 引用语法使用

在 CLAUDE.md 中使用：
```markdown
## 项目说明

@docs/project-overview.md

## 开发规范

@docs/development-guide.md
```

## Capabilities

### New Capabilities

无。此变更是纯粹的文档重构，不涉及新功能或规范变更。

### Modified Capabilities

无。此变更不改变任何功能规范或需求，仅调整文档结构。

## Impact

### 受影响的文件

**新建文件**：
1. `docs/README.md` - 文档导航索引
2. `docs/project-overview.md` - 项目概览
3. `docs/development-guide.md` - 开发规范
4. `docs/documentation-guide.md` - 文档规范

**新建目录**：
1. `docs/architecture/` - 架构设计文档
2. `docs/features/` - 功能设计文档
3. `docs/manual/` - 产品使用手册（空白）

**移动文件**：
1. `docs/develop/alpha-architecture.md` → `docs/architecture/alpha-architecture.md`
2. `docs/develop/backend/*` → `docs/features/backend/*`
3. `docs/develop/frontend/*` → `docs/features/frontend/*`

**删除目录**：
1. `docs/develop/` - 内容已重新组织到其他目录

**修改文件**：
1. `CLAUDE.md` - 大幅简化，使用 `@` 引用语法
2. `CLAUDE.local.md` - 可能需要调整（如果包含重复内容）

**保持不变**：
- `docs/database/` - 保持原结构
- `docs/modules/` - 保持原结构，仅整理内容

### 不受影响的内容

- 代码实现、API、数据库结构
- 现有功能行为
- 测试逻辑
