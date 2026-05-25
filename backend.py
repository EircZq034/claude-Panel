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
