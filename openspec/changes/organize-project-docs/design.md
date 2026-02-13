# Design: 项目文档重构

## Context

### 当前状态

- **CLAUDE.md** 混合了多种内容：项目概述、技术栈、开发规范、测试策略、AI 指令等，导致文档职责不清
- **docs/develop** 目录结构混乱，架构设计、功能文档、模块文档混杂在一起
- 文档内容包含大量代码示例和实现细节，偏离设计文档的初衷

### 约束条件

- CLAUDE.md 支持使用 `@path/to/file` 语法引用其他文档
- 文档需要便于 AI 助手和人类开发者共同阅读
- 现有文档内容需要保留和迁移，不能丢失信息

## Goals / Non-Goals

**Goals:**
1. **职责分离** - CLAUDE.md 专注于 AI 指令，项目文档独立出来
2. **结构清晰** - docs 目录按职责分类（架构/模块/功能/数据库）
3. **文档简洁** - 去除代码示例和实现细节，突出设计核心
4. **便于维护** - 建立清晰的文档规范和索引

**Non-Goals:**
- 不改变代码实现
- 不改变 API 或功能行为
- 不重写所有文档内容（仅重组和优化）

## Decisions

### 1. 文档目录结构

**决策**：采用五层目录结构

```
docs/
├── [顶层文档]           # 项目级文档
├── architecture/        # 架构设计
├── modules/            # 模块文档
├── features/           # 功能文档
├── manual/             # 产品使用手册
└── database/           # 数据库文档
```

**理由**：
- 按文档职责分类，而非按技术栈（frontend/backend）分类
- architecture/ 突出系统架构和技术选型
- modules/ 按功能模块组织，便于查找
- features/ 按具体功能组织，与代码实现对应
- manual/ 面向最终用户，放置产品使用手册和操作指南

**替代方案考虑**：
- 按技术栈分类（frontend/backend）：被否决，因为一个功能通常涉及前后端，分离会导致文档割裂
- 按开发阶段分类（design/implementation）：被否决，因为增加认知负担，开发者需要跨目录查找

### 2. 文档提取策略

**决策**：从 CLAUDE.md 提取以下内容到独立文档

| CLAUDE.md 章节 | 目标文档 |
|---------------|---------|
| 项目概述、技术栈、目录结构 | `docs/project-overview.md` |
| 开发流程规范、开发规范 | `docs/development-guide.md` |
| 项目说明引用 | `@docs/project-overview.md` |
| 开发规范引用 | `@docs/development-guide.md` |

**保留在 CLAUDE.md**：
- AI 助手工作指令（opsx 使用、工具说明）
- 环境变量配置说明
- 参考命令（快速查找）

**理由**：
- CLAUDE.md 是 AI 助手的主要工作上下文，应保留指令性内容
- 项目说明和开发规范是静态知识，适合独立文档
- 使用 `@` 引用可以减少重复，保持 CLAUDE.md 简洁

### 3. 文档规范核心原则

**决策**：建立严格的文档编写规范

- **无代码示例** - 文档不包含具体实现代码
- **无代码片段** - 不粘贴配置文件或代码片段
- **设计导向** - 突出"是什么"和"为什么"，而非"怎么做"
- **简洁优先** - 每句话都要有价值，避免冗余

**理由**：
- 代码示例容易过时，增加维护负担
- 文档应聚焦设计思路，而非实现细节
- 实现细节应通过代码本身和注释表达

### 4. 文档迁移顺序

**决策**：按以下顺序执行迁移

1. 创建新目录和空白文档
2. 从 CLAUDE.md 提取内容到 project-overview.md 和 development-guide.md
3. 移动 docs/develop 下的现有文档到新结构
4. 创建 documentation-guide.md
5. 简化 CLAUDE.md，使用 `@` 引用
6. 创建 docs/README.md 作为索引

**理由**：
- 先创建目标文档，避免迁移过程中丢失信息
- 最后简化 CLAUDE.md，确保引用目标已存在
- 创建索引放在最后，确保所有文档路径已确定

## Risks / Trade-offs

### 风险 1：`@` 引用语法不生效
**风险**：如果 `@` 引用语法不能正确展开，CLAUDE.md 会失去重要信息
**缓解**：在完成迁移后测试 AI 助手是否能正确读取引用内容；如果不行，保留关键信息的摘要

### 风险 2：文档迁移导致链接失效
**风险**：移动文档后，其他地方的链接可能失效
**缓解**：使用全局搜索查找可能的引用，逐步更新；保留 develop/ 目录作为软链接（过渡期）

### 风险 3：去除代码示例影响可读性
**风险**：部分开发者习惯通过代码示例理解设计
**缓解**：在 documentation-guide.md 中说明设计思路；代码示例应放在代码注释或独立教程中

### 权衡：文档简洁 vs 信息完整性
**权衡**：去除代码示例和实现细节可能导致文档过于抽象
**平衡**：在文档中提供关键接口定义和数据流描述（不包含具体实现代码）

## Migration Plan

### 执行步骤

#### 第一阶段：创建新文档
1. 创建目录：`docs/architecture/`, `docs/features/`, `docs/manual/`
2. 创建空白文档：
   - `docs/project-overview.md`
   - `docs/development-guide.md`
   - `docs/documentation-guide.md`
   - `docs/README.md`

#### 第二阶段：内容迁移
1. 从 CLAUDE.md 提取项目概述 → `docs/project-overview.md`
2. 从 CLAUDE.md 提取开发规范 → `docs/development-guide.md`
3. 移动架构文档：`docs/develop/alpha-architecture.md` → `docs/architecture/`
4. 移动功能文档：`docs/develop/backend/*` → `docs/features/backend/`
5. 移动功能文档：`docs/develop/frontend/*` → `docs/features/frontend/`

#### 第三阶段：创建文档规范
1. 编写 `docs/documentation-guide.md`，包含文档编写规范
2. 应用规范到现有文档（去除代码示例、优化表达）

#### 第四阶段：简化 CLAUDE.md
1. 使用 `@docs/project-overview.md` 替换项目概述部分
2. 使用 `@docs/development-guide.md` 替换开发规范部分
3. 保留 AI 助手特有的工作指令

#### 第五阶段：创建索引
1. 编写 `docs/README.md`，包含文档导航
2. 删除空的 `docs/develop/` 目录

### 回滚策略

如果迁移出现问题：
1. 保留原 CLAUDE.md 的备份（`CLAUDE.md.bak`）
2. 使用 git 可以恢复所有移动的文档
3. `docs/develop/` 目录在确认无误前保留

## Open Questions

无。此变更是文档重构，不涉及技术不确定因素。
