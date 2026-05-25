# 后端实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 Claude Panel 添加 FastAPI 后端，实现环境信息读取、命令/技能 CRUD 和数据持久化。

**架构：** FastAPI 独立进程（uvicorn 后台线程），SQLite 存储命令和技能数据，环境信息从真实 `settings.json` 读取。前端 HTML 通过 JavaScript fetch 调用 API。

**技术栈：** Python 3.x, FastAPI, uvicorn, sqlite3（标准库）, platform（标准库）, PyWebView

---

### 任务 1：安装依赖

**文件：**
- 创建：`requirements.txt`

- [ ] **步骤 1：创建 requirements.txt**

```
fastapi
uvicorn
webview
```

- [ ] **步骤 2：安装依赖**

```bash
pip install -r requirements.txt
```

预期：fastapi、uvicorn 安装成功（webview 已安装）。

---

### 任务 2：创建 backend.py

**文件：**
- 创建：`backend.py`

- [ ] **步骤 1：编写 backend.py 完整代码**

```python
"""Claude Panel 后端 — FastAPI 应用"""
import os
import json
import sqlite3
import platform
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# === 配置 ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "panel.db"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"

app = FastAPI(title="Claude Panel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 数据库 ===
def get_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            desc TEXT NOT NULL DEFAULT '',
            icon TEXT NOT NULL DEFAULT '🔧'
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            desc TEXT NOT NULL DEFAULT '',
            icon TEXT NOT NULL DEFAULT '💡',
            enabled INTEGER NOT NULL DEFAULT 1
        )
    """)
    db.commit()
    db.close()


init_db()


# === Pydantic 模型 ===
class CommandIn(BaseModel):
    name: str
    desc: str = ""
    icon: str = "🔧"


class SkillUpdate(BaseModel):
    name: str | None = None
    desc: str | None = None
    icon: str | None = None
    enabled: int | None = None


# === 环境 API ===
@app.get("/api/env")
def get_env():
    result = {
        "claude_path": str(CLAUDE_SETTINGS),
        "version": "未知",
        "model": "未知",
        "system": platform.platform(),
        "settings": {},
    }

    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
            env = settings.get("env", {})
            result["model"] = env.get("ANTHROPIC_MODEL", "未知")
            result["settings"]["base_url"] = env.get("ANTHROPIC_BASE_URL", "")
            token = env.get("ANTHROPIC_AUTH_TOKEN", "")
            if len(token) > 7:
                token = token[:7] + "***"
            result["settings"]["auth_token"] = token
            result["settings"]["status_line_type"] = settings.get("statusLine", {}).get("type", "")
        except Exception:
            pass

    try:
        output = subprocess.check_output(["claude", "--version"], timeout=5)
        result["version"] = output.decode().strip()
    except Exception:
        pass

    return result


# === 命令 CRUD ===
@app.get("/api/commands")
def list_commands():
    db = get_db()
    rows = db.execute("SELECT * FROM commands ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


@app.post("/api/commands")
def add_command(cmd: CommandIn):
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO commands (name, desc, icon) VALUES (?, ?, ?)",
            (cmd.name, cmd.desc, cmd.icon),
        )
        db.commit()
        new_id = cur.lastrowid
        row = db.execute("SELECT * FROM commands WHERE id = ?", (new_id,)).fetchone()
        db.close()
        return dict(row)
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"数据库错误: {e}")


@app.delete("/api/commands/{cmd_id}")
def delete_command(cmd_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM commands WHERE id = ?", (cmd_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="命令不存在")
    db.execute("DELETE FROM commands WHERE id = ?", (cmd_id,))
    db.commit()
    db.close()
    return {"ok": True}


# === 技能 CRUD ===
@app.get("/api/skills")
def list_skills():
    db = get_db()
    rows = db.execute("SELECT * FROM skills ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


@app.put("/api/skills/{skill_id}")
def update_skill(skill_id: int, data: SkillUpdate):
    db = get_db()
    row = db.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="技能不存在")

    updates = {}
    for field in ("name", "desc", "icon", "enabled"):
        val = getattr(data, field)
        if val is not None:
            updates[field] = val

    if not updates:
        db.close()
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [skill_id]
    db.execute(f"UPDATE skills SET {set_clause} WHERE id = ?", values)
    db.commit()

    row = db.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    db.close()
    return dict(row)
```

- [ ] **步骤 2：验证 backend.py 语法**

```bash
python -c "import ast; ast.parse(open('D:/AI_Explore/claude-Panel/backend.py').read()); print('语法OK')"
```

- [ ] **步骤 3：Commit**

```bash
git add backend.py requirements.txt
git commit -m "feat: 添加 FastAPI 后端，含环境/命令/技能 API"
```

---

### 任务 3：修改 main.py 启动后端

**文件：**
- 修改：`main.py`

- [ ] **步骤 1：改写 main.py**

```python
"""Claude Panel 桌面程序（PyWebView 前端壳 + FastAPI 后端）"""
import os
import time
import threading
import uvicorn
import webview

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RENDERER_DIR = os.path.join(BASE_DIR, "renderer")
INDEX_URL = "http://localhost:8520"


def start_backend():
    """在后台线程启动 FastAPI"""
    from backend import app
    uvicorn.run(app, host="127.0.0.1", port=8520, log_level="warning")


def main():
    # 启动后端
    t = threading.Thread(target=start_backend, daemon=True)
    t.start()
    # 等待端口就绪
    time.sleep(1.5)

    window = webview.create_window(
        title="Claude Panel",
        url=INDEX_URL,
        width=960,
        height=700,
        min_size=(780, 560),
        text_select=True,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
```

- [ ] **步骤 2：测试启动**

```bash
cd /d/AI_Explore/claude-Panel && python -c "
import threading, time, uvicorn
from backend import app
t = threading.Thread(target=lambda: uvicorn.run(app, host='127.0.0.1', port=8520, log_level='warning'), daemon=True)
t.start()
time.sleep(1.5)
import urllib.request
resp = urllib.request.urlopen('http://localhost:8520/api/env')
print('API 响应:', resp.read().decode()[:200])
print('后端启动正常')
"
```

预期：输出版本、模型、系统信息 JSON。

- [ ] **步骤 3：Commit**

```bash
git add main.py
git commit -m "feat: main.py 启动时自动拉起 FastAPI 后端"
```

---

### 任务 4：前端 — 环境页面接入 API

**文件：**
- 修改：`renderer/env.html`

- [ ] **步骤 1：在 `</style>` 后添加 JavaScript**

在第 91 行 `</style>` 后，`</head>` 前插入：

```html
<script>
async function loadEnv() {
  try {
    const resp = await fetch('/api/env');
    const data = await resp.json();
    document.getElementById('env-path').textContent = data.claude_path || '未知';
    document.getElementById('env-version').textContent = data.version || '未知';
    document.getElementById('env-model').textContent = data.model || '未知';
    document.getElementById('env-system').textContent = data.system || '未知';
  } catch(e) {
    console.error('加载环境信息失败:', e);
  }
}
window.addEventListener('DOMContentLoaded', loadEnv);
</script>
```

- [ ] **步骤 2：给真实数据字段添加 id**

修改 `info-grid` 中的对应行，替换硬编码值：

```html
<span class="label">安装路径</span>
<span class="value" id="env-path">加载中...</span>
<span class="label">版本号</span>
<span class="value" id="env-version">加载中...</span>
<span class="label">当前模型</span>
<span class="value" id="env-model">加载中...</span>
<span class="label">系统平台</span>
<span class="value" id="env-system">加载中...</span>
```

- [ ] **步骤 3：添加 index.html 导航链接**

在 topbar 的 `.nav-links` 中添加返回主页的链接：

```html
<a href="index.html">🏠 主页</a>
```

- [ ] **步骤 4：Commit**

```bash
git add renderer/env.html
git commit -m "feat: 环境页面接入 /api/env 动态数据"
```

---

### 任务 5：前端 — 命令页面接入 API

**文件：**
- 修改：`renderer/commands.html`

- [ ] **步骤 1：添加 JavaScript**

在 `</style>` 后，`</head>` 前插入：

```html
<script>
async function loadCommands() {
  try {
    const resp = await fetch('/api/commands');
    const cmds = await resp.json();
    renderCommands(cmds);
    document.querySelector('.panel-header .count').textContent = `共 ${cmds.length} 条命令`;
  } catch(e) {
    console.error('加载命令失败:', e);
  }
}

function renderCommands(cmds) {
  const container = document.querySelector('.cmd-scroll');
  container.innerHTML = cmds.map(c =>
    `<div class="cmd-item" data-id="${c.id}">
      <span class="icon">${c.icon}</span>
      <span class="cmd">${c.name}</span>
      <span class="desc">${c.desc}</span>
      <span style="margin-left:auto;color:#ccc;cursor:pointer;font-size:14px"
            onclick="deleteCommand(${c.id})">✕</span>
    </div>`
  ).join('');
}

async function addCommand() {
  const kw = document.querySelector('.search-box input');
  const name = kw.value.trim();
  if (!name) return;
  try {
    const resp = await fetch('/api/commands', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name, desc: '', icon: '🔧'})
    });
    if (resp.ok) {
      kw.value = '';
      loadCommands();
    }
  } catch(e) {
    console.error('添加命令失败:', e);
  }
}

async function deleteCommand(id) {
  try {
    await fetch('/api/commands/' + id, {method: 'DELETE'});
    loadCommands();
  } catch(e) {
    console.error('删除命令失败:', e);
  }
}

window.addEventListener('DOMContentLoaded', loadCommands);
</script>
```

- [ ] **步骤 2：改造搜索框和按钮**

搜索框去掉 `readonly`，改成回车触发添加：

```html
<input type="text" placeholder="输入命令名回车添加..." onkeydown="if(event.key==='Enter')addCommand()">
```

"添加命令"按钮绑定 `onclick`：

```html
<button onclick="addCommand()" style="margin-left:auto; background:#4a90d9; color:#fff; border:none; border-radius:8px; padding:6px 16px; font-size:14px; cursor:pointer; font-family:inherit;">＋ 添加命令</button>
```

- [ ] **步骤 3：添加 index.html 导航链接**（同任务 4 步骤 3）

- [ ] **步骤 4：Commit**

```bash
git add renderer/commands.html
git commit -m "feat: 命令页接入 /api/commands CRUD"
```

---

### 任务 6：前端 — 技能页面接入 API

**文件：**
- 修改：`renderer/skills.html`

- [ ] **步骤 1：添加 JavaScript**

在 `</style>` 后，`</head>` 前插入：

```html
<script>
async function loadSkills() {
  try {
    const resp = await fetch('/api/skills');
    const skills = await resp.json();
    document.querySelector('.panel-header .count').textContent = `已安装 ${skills.length} 个`;
    renderSkills(skills);
  } catch(e) {
    console.error('加载技能失败:', e);
  }
}

function renderSkills(skills) {
  const container = document.querySelector('.skills-scroll');
  container.innerHTML = skills.map(s => {
    const bg = s.enabled ? '#f8f8fc' : '#f0f0f0';
    const border = s.enabled ? '#eeeef4' : '#ddd';
    const activeAttr = s.enabled ? 'enabled="1"' : 'enabled="0"';
    return `<div style="background:${bg}; border-radius:12px; padding:10px 14px; border:1px solid ${border}; display:flex; align-items:stretch; gap:10px;">
      <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
          <span style="font-size:20px; color:#555;">${s.icon}</span>
          <span style="font-size:16px; font-weight:600; color:#1a1a2e;">${s.name}</span>
          <span style="font-size:14px; color:#888;">/${s.name}</span>
        </div>
        <div style="font-size:14px; color:#888; margin-left:30px;">${s.desc}</div>
      </div>
      <div class="action-box">
        <div style="display:flex; gap:16px; white-space:nowrap;">
          <span style="font-size:14px; color:#ccc;">✏️ 编辑</span>
          <span style="font-size:14px; color:#4a90d9; cursor:pointer;" onclick="toggleSkill(${s.id}, ${s.enabled})">${s.enabled ? '⏸️ 禁用' : '▶️ 启用'}</span>
          <span style="font-size:14px; color:#888; cursor:pointer;" onclick="deleteSkill(${s.id})">🗑️ 删除</span>
        </div>
      </div>
    </div>`;
  }).join('');
}

async function toggleSkill(id, current) {
  const next = current ? 0 : 1;
  await fetch('/api/skills/' + id, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({enabled: next})
  });
  loadSkills();
}

async function deleteSkill(id) {
  await fetch('/api/skills/' + id, {method: 'DELETE'});  // 需先添加 DELETE 路由
  loadSkills();
}

window.addEventListener('DOMContentLoaded', loadSkills);
</script>
```

- [ ] **步骤 2：在 backend.py 中添加技能删除路由**

```python
@app.delete("/api/skills/{skill_id}")
def delete_skill(skill_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="技能不存在")
    db.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
    db.commit()
    db.close()
    return {"ok": True}
```

- [ ] **步骤 3：添加 index.html 导航链接**（同任务 4 步骤 3）

- [ ] **步骤 4：Commit**

```bash
git add renderer/skills.html backend.py
git commit -m "feat: 技能页接入 /api/skills API，添加删除路由"
```

---

### 任务 7：添加种子数据 & 端到端验证

**文件：**
- 修改：`backend.py`

- [ ] **步骤 1：在 init_db() 末尾添加种子数据逻辑**

在 `init_db()` 函数末尾追加：

```python
    # 种子数据
    count = db.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    if count == 0:
        cmds = [
            ("/compact", "压缩上下文", "🔧"),
            ("/cost", "查看用量", "💰"),
            ("/code-review", "代码审查", "📋"),
            ("/config", "配置管理", "⚙️"),
            ("/brainstorming", "需求分析", "💡"),
            ("/debugging", "调试流程", "🐛"),
            ("/tdd", "测试驱动开发", "🧪"),
            ("/documentation", "文档生成", "📝"),
            ("/search", "全局搜索", "🔍"),
            ("/notify", "通知管理", "🔔"),
            ("/stats", "统计报告", "📊"),
            ("/web", "网页搜索", "🌐"),
        ]
        db.executemany(
            "INSERT INTO commands (name, desc, icon) VALUES (?, ?, ?)", cmds
        )

    scount = db.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    if scount == 0:
        skills = [
            ("brainstorming", "创造性工作前的需求分析工具", "💡"),
            ("debugging", "系统化调试流程", "🐛"),
            ("TDD", "测试驱动开发", "🧪"),
            ("code-review", "代码审查辅助", "📋"),
            ("documentation", "文档生成与维护", "📝"),
        ]
        db.executemany(
            "INSERT INTO skills (name, desc, icon) VALUES (?, ?, ?)", skills
        )
```

注意：种子数据 insert 需要在 commit 之前，重新组织 `init_db()`：

```python
def init_db():
    db = get_db()
    db.execute("""...""")  # create commands table
    db.execute("""...""")  # create skills table

    # 种子数据
    count = db.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    if count == 0:
        ...
    scount = db.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    if scount == 0:
        ...

    db.commit()
    db.close()
```

- [ ] **步骤 2：端到端测试**

```bash
cd /d/AI_Explore/claude-Panel && python -c "
import threading, time, urllib.request, json
import uvicorn
from backend import app

t = threading.Thread(target=lambda: uvicorn.run(app, host='127.0.0.1', port=8521, log_level='warning'), daemon=True)
t.start()
time.sleep(1.5)

# 测试环境 API
resp = urllib.request.urlopen('http://localhost:8521/api/env')
env = json.loads(resp.read())
assert 'model' in env, 'env 缺少 model'
print(f'✅ 环境 API: model={env[\"model\"]}')

# 测试命令列表
resp = urllib.request.urlopen('http://localhost:8521/api/commands')
cmds = json.loads(resp.read())
assert len(cmds) > 0, '命令列表为空'
print(f'✅ 命令 API: {len(cmds)} 条')

# 测试添加命令
req = urllib.request.Request('http://localhost:8521/api/commands',
    data=json.dumps({'name': '/test', 'desc': '测试'}).encode(),
    headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
assert resp.status == 200
print('✅ 添加命令: OK')

# 测试技能列表
resp = urllib.request.urlopen('http://localhost:8521/api/skills')
skills = json.loads(resp.read())
assert len(skills) > 0, '技能列表为空'
print(f'✅ 技能 API: {len(skills)} 个')

print('全部测试通过')
"
```

预期：5 项全部通过。

- [ ] **步骤 3：Commit**

```bash
git add backend.py
git commit -m "feat: 添加种子数据并验证端到端 API"
```

---

### 任务 8：index.html 导航改造

**文件：**
- 修改：`renderer/index.html`

- [ ] **步骤 1：将本地文件链接改为 API 路由页面**

三个子页面链接保持不变（`env.html`、`commands.html`、`skills.html`），因为 PyWebView 会通过后端访问。

- [ ] **步骤 2：Commit**

```bash
git add renderer/index.html
git commit -m "feat: 主页保持兼容，子页面通过后端路由访问"
```

---

### 任务 9：清理 & 最终验证

- [ ] **步骤 1：删除旧的静态数据占位注释**

不需要 — 保持干净。

- [ ] **步骤 2：最终 git log 检查**

```bash
cd /d/AI_Explore/claude-Panel && git log --oneline
```

预期：至少 6 个清晰的 commit。

- [ ] **步骤 3：完整启动测试**

```bash
cd /d/AI_Explore/claude-Panel && python main.py
```

预期：桌面窗口打开，三页面 API 数据正常加载。
