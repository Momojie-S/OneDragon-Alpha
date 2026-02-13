# 项目开发指南

你需要按照以下描述进行本项目的开发。

## 项目说明

@docs/project-overview.md

## 开发规范

@docs/development-guide.md

## 文档规范

@docs/documentation-guide.md

## 开发流程规范

### 需求开发流程

1. 当启动一个新的需求修改时，需要使用 opsx 草拟方案，并在后续过程按 opsx 规范进行。opsx 相关命令必须在项目根目录下运行
2. 在设计阶段：
   - 按最少地满足需求的功能点来设计，不要过度设计
   - 使用 context7 了解相关库的能力，特别是 AgentScope 和 element-plus-x 这两个比较新的库
   - 设计阶段需要考虑测试过程产生脏数据和清理方案
3. 在开发阶段，需要先进行后端开发：
   3.1. 后端代码开发
   3.2. 后端代码的端到端测试，仅做少量的核心场景
   3.3. 后端代码的单元测试，使用全 mock 的方式
   3.4. 进行详细的代码 Review
4. 完成后端开发后，再进行前端开发：
   4.1. 前端代码开发
   4.2. 前端单元测试（Vitest + Vue Test Utils，全 Mock 数据）
   4.3. 制定前端 E2E 测试计划（只保留少量核心场景）
   4.4. 使用 chrome-devtools 按计划联调
   4.5. 编写 Playwright E2E 测试（使用 Mock API）
   4.6. 对于前端核心函数，进行单元测试
   4.7. 进行详细的代码 Review
5. 开发测试完成后，使用 `opsx:verify` 进行验证
6. 验证通过后，使用 `opsx:archive` 进行归档（禁止使用 `--no-validate`）
7. 提交到 Github 并创建 PR

### 归档规范

- 禁止使用移动文件夹或者复制文件夹的方式进行归档
- 禁止使用 `--skip-specs`

## 参考命令

### 后端（Python）

#### 依赖管理
```bash
uv sync --group dev                              # 安装所有依赖（包括开发依赖）
uv sync                                         # 仅安装生产依赖
uv add <package>                                 # 添加新依赖
```

#### 开发服务
```bash
uv run --env-file .env uvicorn src.one_dragon_alpha.server.app:app --reload --port 21003
# 启动开发服务器（热重载，端口 21003）
```

#### 测试
```bash
# 运行测试
uv run --env-file .env pytest tests/                    # 运行所有测试
uv run --env-file .env pytest tests/ -v                 # 详细输出
uv run --env-file .env pytest tests/one_dragon_agent/   # 运行特定模块
uv run --env-file .env pytest tests/ -k "test_agent"    # 筛选测试（匹配关键词）

# 查看测试覆盖率（如果配置了）
uv run --env-file .env pytest tests/ --cov
```

#### 代码质量
```bash
uv run ruff check src/ tests/               # 代码检查（仅检查不修复）
uv run ruff check --fix src/ tests/         # 代码检查并自动修复
uv run ruff format src/ tests/              # 代码格式化
```

### 前端（Vue）

> 注意：运行 pnpm 命令时必须使用 `-C` 参数指定运行目录

#### 依赖管理
```bash
pnpm -C frontend install                    # 安装依赖
pnpm -C frontend add <package>              # 添加新依赖
pnpm -C frontend remove <package>           # 移除依赖
```

#### 开发服务
```bash
pnpm -C frontend dev                         # 启动开发服务器（默认占用 21002 端口）
pnpm -C frontend build                       # 构建生产版本
pnpm -C frontend preview                     # 预览构建结果
```

#### 测试
```bash
# 单元测试
pnpm -C frontend test:unit                   # 运行单元测试
pnpm -C frontend test:unit --ui              # Vitest UI 模式

# E2E 测试
pnpm -C frontend test:e2e                    # 运行 E2E 测试（headless 模式）
pnpm -C frontend test:e2e:ui                 # E2E 测试 UI 模式
pnpm -C frontend test:e2e:debug             # E2E 测试调试模式
pnpm -C frontend test:e2e:headed            # E2E 测试（显示浏览器）
```

#### 代码质量
```bash
pnpm -C frontend type-check                  # TypeScript 类型检查
pnpm -C frontend lint                        # ESLint 检查并自动修复
pnpm -C frontend format                      # Prettier 格式化
```

## 工具说明

- opsx - 保持使用 opsx 工具，按 spec-driven 的方式进行开发
- context7 - 积极使用 context7 工具搜索使用文档。例如，设计时需要了解依赖库的能力、开发测试时遇到调用方法不存在、参数个数不一致、参数类型不一致等场景
- tushare-docs-mcp - 对于 tushare 库，是用 tushare-docs-mcp 工具进行搜索文档，而不是 context7
- Bash:
  - 需要临时运行服务时，使用 Bash 工具原生的后台运行能力，而不是在命令中增加 `nohup` 或者后缀 `&` 的方式运行
  - 禁止调用 Bash 时传入多行命令，如果需要，先在临时文件夹生成复杂脚本，再运行
  - 运行 openspec 命令时，必须在项目根目录下
- agent team - 启动 agent team 时，leader 需要同步更新 opsx 状态
