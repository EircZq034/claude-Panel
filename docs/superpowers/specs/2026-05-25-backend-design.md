# Claude Panel 后端设计规格

## 概述

为 Claude Panel 桌面程序添加 FastAPI 后端，实现：
- 读取真实 Claude Code 配置数据（settings.json 等）
- 命令和技能的增删改操作
- 数据持久化存储

## 技术栈

- **框架**: FastAPI（异步，自带 Swagger 文档）
- **数据库**: SQLite（Python 标准库 sqlite3）
- **部署**: 分离式（uvicorn 后台线程 + PyWebView 前端壳）
- **端口**: 8520

## 目录结构

```
claude-Panel/
├── main.py              # 入口：启动 FastAPI → 打开 PyWebView
├── backend.py           # 全部后端逻辑（模型、数据库、路由）
├── renderer/            # 前端 HTML + JavaScript
├── data/                # SQLite 数据库文件（自动创建）
```

## 数据模型

### 命令表 (commands)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| name | TEXT | 如 `/compact` |
| desc | TEXT | 如 "压缩上下文" |
| icon | TEXT | 如 "🔧" |

### 技能表 (skills)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| name | TEXT | 如 `brainstorming` |
| desc | TEXT | 描述 |
| icon | TEXT | 如 "💡" |
| enabled | INTEGER | 1=启用, 0=禁用 |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/env | 读取真实配置，返回环境信息 |
| GET | /api/commands | 命令列表 |
| POST | /api/commands | 添加命令 |
| DELETE | /api/commands/{id} | 删除命令 |
| GET | /api/skills | 技能列表 |
| PUT | /api/skills/{id} | 更新技能（启用/禁用/编辑） |

## 环境数据来源

- **模型名**: `~/.claude/settings.json` → `ANTHROPIC_MODEL`
- **版本号**: 执行 `claude --version`（失败则显示 "未知"）
- **系统信息**: `platform.platform()`
- **敏感脱敏**: `ANTHROPIC_AUTH_TOKEN` 只显示前 7 位 + `***`

## 启动流程

1. `main.py` 启动 uvicorn（后台线程，端口 8520）
2. 等待端口就绪
3. PyWebView 打开 `http://localhost:8520`
4. 前端 HTML 通过 fetch 调用 API

## 错误处理

- 配置文件不存在 → 返回空字段，不崩溃
- SQLite 操作失败 → HTTP 500 + `{"error": "..."}`
- 数据库文件/目录自动创建
- 表在首次请求时自动建表

## 前端改造

- 环境页面: 页面加载时 fetch `/api/env`，填充真实数据
- 命令页面: fetch `/api/commands`，搜索/添加/删除可用
- 技能页面: fetch `/api/skills`，启用/禁用/编辑可用
- 降级: 无 JS 时保持静态展示，不影响浏览
