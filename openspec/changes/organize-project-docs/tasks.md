# Tasks: 项目文档重构

## 1. 准备阶段

- [x] 1.1 备份现有 CLAUDE.md 为 `CLAUDE.md.bak`
- [x] 1.2 创建新目录 `docs/architecture/`
- [x] 1.3 创建新目录 `docs/features/backend/`
- [x] 1.4 创建新目录 `docs/features/frontend/`
- [x] 1.5 创建新目录 `docs/manual/`（产品使用手册，暂时空白）

## 2. 创建空白文档框架

- [x] 2.1 创建空白文档 `docs/project-overview.md`
- [x] 2.2 创建空白文档 `docs/development-guide.md`
- [x] 2.3 创建空白文档 `docs/documentation-guide.md`
- [x] 2.4 创建空白文档 `docs/README.md`

## 3. 从 CLAUDE.md 提取内容

- [x] 3.1 将"项目概述"、"技术栈"、"目录结构"部分写入 `docs/project-overview.md`
- [x] 3.2 将"环境说明"部分写入 `docs/project-overview.md`
- [x] 3.3 将"后端开发规范"、"前端开发规范"部分写入 `docs/development-guide.md`
- [x] 3.4 将"测试策略"部分写入 `docs/development-guide.md`
- [x] 3.5 将"开发流程规范"部分写入 `docs/development-guide.md`

## 4. 移动现有文档

- [x] 4.1 移动 `docs/develop/alpha-architecture.md` → `docs/architecture/alpha-architecture.md`
- [x] 4.2 移动 `docs/develop/backend/chat.md` → `docs/features/backend/chat.md`
- [x] 4.3 移动 `docs/develop/backend/mysql_connection_service.md` → `docs/features/backend/mysql_connection_service.md`
- [x] 4.4 移动 `docs/develop/frontend/chat.md` → `docs/features/frontend/chat.md`
- [x] 4.5 整理 `docs/modules/model-config/` 目录下的文档
- [x] 4.6 删除空的 `docs/develop/` 目录

## 5. 创建文档规范

- [x] 5.1 编写 `docs/documentation-guide.md`，包含文档编写规范
- [x] 5.2 明确"无代码示例"、"无代码片段"、"设计导向"、"简洁优先"原则
- [x] 5.3 说明文档应包含的内容和不应包含的内容

## 6. 优化现有文档

- [x] 6.1 检查 `docs/architecture/alpha-architecture.md`，去除代码示例
- [x] 6.2 检查 `docs/modules/model-config/` 下的文档，去除代码示例
- [x] 6.3 检查 `docs/features/` 下的文档，去除代码示例
- [x] 6.4 优化文档表达，突出设计核心和重点

## 7. 简化 CLAUDE.md

- [x] 7.1 使用 `@docs/project-overview.md` 替换项目概述部分
- [x] 7.2 使用 `@docs/development-guide.md` 替换开发规范部分
- [x] 7.3 保留 AI 助手特有的工作指令（opsx、工具说明）
- [x] 7.4 保留环境变量配置说明和参考命令
- [x] 7.5 验证 CLAUDE.md 简洁性和完整性

## 8. 创建文档索引

- [x] 8.1 编写 `docs/README.md`，包含文档导航（包含 manual/ 目录说明）
- [x] 8.2 按目录分类列出所有文档
- [x] 8.3 为每个目录和文档添加简短说明
- [x] 8.4 为 manual/ 目录添加说明："产品使用手册（待完善）"

## 9. 验证与测试

- [x] 9.1 验证 `@` 引用语法是否正确工作
- [x] 9.2 检查所有文档链接是否有效
- [x] 9.3 确认没有丢失重要信息
- [x] 9.4 使用 AI 助手测试 CLAUDE.md 的可读性

## 10. 清理与收尾

- [ ] 10.1 删除 `CLAUDE.md.bak` 备份（验证无误后）
- [x] 10.2 提交变更到 git
