# Claude Panel

> 桌面版 Claude Code 可视化管理面板 — 命令速查 · 技能管理 · 环境监控

基于 PyWebView + FastAPI + SQLite 构建，开机即用的 Windows 桌面工具。

---

## 项目结构

```
claude-Panel/
├── main.py               # 桌面入口（PyWebView 壳 + FastAPI 后台线程）
├── backend.py            # FastAPI 后端（API 路由 + SQLite + 文件扫描）
├── requirements.txt      # Python 依赖
├── data/                 # 运行时数据
│   ├── panel.db          # SQLite 数据库
│   └── readmes/          # 上传的 README 文件
└── renderer/             # 前端页面
    ├── index.html        # 主页（三卡导航）
    ├── commands.html     # 命令速查
    ├── skills.html       # 技能管理
    └── env.html          # 环境详情
```

## 快速开始

```bash
cd D:\AI_Explore\claude-Panel
pip install -r requirements.txt
python main.py
```

## 功能概览

### 命令速查
- 查看 Claude Code 所有内置/自定义斜杠命令
- **模糊搜索** 按名称或描述实时过滤
- **添加/删除** 命令（手动或扫描导入）
- 命令数据持久化到 SQLite

### 技能管理
- 扫描多个源目录的技能：
  - `~/.claude/commands/*.md` — 自定义命令（独立 .md 文件）
  - `~/.claude/skills/*/SKILL.md` — 用户级技能（子目录结构）
  - `D:\AI_Test\.claude\skills/*/SKILL.md` — 项目级技能
- 技能 **启用/禁用**
- **README 文件上传**（.md 拖拽上传，存本地）
- **README 一键打开**（调用系统默认程序 `os.startfile`）
- 技能数据 + README 路径持久化

### 环境详情
- 实时读取 Claude Code 配置：
  - 安装路径、版本号、当前模型、系统平台
  - API Base URL、Auth Token（脱敏显示）
- 使用统计（来自 `sessions/` + `stats-cache.json`）：
  - 总会话数、总消息数、累计时长
  - 当前会话开始时间、已持续时长

### 主题切换
- 四页面统一暗黑/浅色主题
- 点击按钮一键切换，`localStorage` 跨页面持久化
- 页面刷新后自动恢复偏好，无闪烁

## 技术架构

| 层级 | 技术 | 说明 |
|------|------|------|
| 桌面壳 | PyWebView | 无边框窗口 960×700，加载本地 HTTP 服务 |
| Web 服务 | FastAPI + Uvicorn | 端口 8520，CORS 全开，后台线程启动 |
| 数据库 | SQLite (WAL) | `data/panel.db`，`commands` + `skills` 两张表 |
| 前端 | 原生 HTML/CSS/JS | 无框架，`fetch()` 调 API，零构建 |
| 文件操作 | Python stdlib | `os.startfile` 打开文件，`pathlib` 扫描目录 |

## API 接口

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/env` | 获取 Claude 环境信息 + 使用统计 |
| GET/POST/DELETE | `/api/commands` | 命令 CRUD |
| GET/PUT/DELETE | `/api/skills` | 技能 CRUD + 启用/禁用 |
| GET | `/api/skills/scan` | 扫描文件系统同步技能入库 |
| POST | `/api/skills/{id}/readme/upload` | 上传 README 文件 |
| POST | `/api/skills/{id}/readme/open` | 用系统程序打开 README |
| DELETE | `/api/skills/{id}/readme` | 删除 README（含本地文件） |

## 外部数据来源

后端启动时读取以下 Claude Code 本地文件：

| 数据 | 路径 | 读取内容 |
|------|------|----------|
| 用户设置 | `~/.claude/settings.json` | 模型、API 地址、Token |
| 会话记录 | `~/.claude/sessions/*.json` | 会话数、时长计算 |
| 统计缓存 | `~/.claude/stats-cache.json` | 历史消息数、会话数 |
| 自定义命令 | `~/.claude/commands/*.md` | 解析为技能 |
| 技能文件 | `~/.claude/skills/*/SKILL.md` | 子目录扫描 |
| 项目技能 | `D:\AI_Test\.claude\skills/*/SKILL.md` | 项目级技能扫描 |

## 开发说明

- **语言要求**：对话用中文，代码/变量/路径保留英文
- **依赖安装**：新增 `python-multipart` 用于文件上传
- **Node.js**：本项目为零前端构建依赖的纯 HTML 项目，不需要 `npm install`

## License

MIT
