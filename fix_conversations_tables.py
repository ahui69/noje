#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path("/root/mrd")
DB_CANDIDATES = [
    ROOT / "core" / "mem.db",
    ROOT / "mem.db",
]

def _utc_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def _p(s: str) -> None:
    sys.stdout.write(s + "\n")
    sys.stdout.flush()

def _pe(s: str) -> None:
    sys.stderr.write(s + "\n")
    sys.stderr.flush()

def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys=ON;")
    try:
        con.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return con

def _tables(con: sqlite3.Connection) -> set[str]:
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return {r[0] for r in cur.fetchall()}

def _columns(con: sqlite3.Connection, table: str) -> list[str]:
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return [r[1] for r in cur.fetchall()]

def _supports_fts5(con: sqlite3.Connection) -> bool:
    try:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS __fts5_probe USING fts5(x);")
        con.execute("DROP TABLE IF EXISTS __fts5_probe;")
        con.commit()
        return True
    except Exception:
        try:
            con.rollback()
        except Exception:
            pass
        return False

def _backup(db_path: Path) -> Path:
    dst = db_path.with_suffix(db_path.suffix + f".bak.{_utc_stamp()}")
    shutil.copy2(db_path, dst)
    return dst

def _ensure_conversations(con: sqlite3.Connection) -> None:
    con.executescript("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        user_id TEXT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        meta_json TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_conversations_ts ON conversations(ts);
    CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
    CREATE INDEX IF NOT EXISTS idx_conversations_role ON conversations(role);
    """)
    con.commit()

def _ensure_conversations_fts(con: sqlite3.Connection) -> None:
    con.executescript("""
    CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts
    USING fts5(
        content,
        user_id,
        ts,
        role,
        meta_json,
        content='conversations',
        content_rowid='id'
    );

    CREATE TRIGGER IF NOT EXISTS conversations_ai AFTER INSERT ON conversations BEGIN
        INSERT INTO conversations_fts(rowid, content, user_id, ts, role, meta_json)
        VALUES (new.id, new.content, new.user_id, new.ts, new.role, new.meta_json);
    END;

    CREATE TRIGGER IF NOT EXISTS conversations_ad AFTER DELETE ON conversations BEGIN
        INSERT INTO conversations_fts(conversations_fts, rowid, content, user_id, ts, role, meta_json)
        VALUES('delete', old.id, old.content, old.user_id, old.ts, old.role, old.meta_json);
    END;

    CREATE TRIGGER IF NOT EXISTS conversations_au AFTER UPDATE ON conversations BEGIN
        INSERT INTO conversations_fts(conversations_fts, rowid, content, user_id, ts, role, meta_json)
        VALUES('delete', old.id, old.content, old.user_id, old.ts, old.role, old.meta_json);
        INSERT INTO conversations_fts(rowid, content, user_id, ts, role, meta_json)
        VALUES (new.id, new.content, new.user_id, new.ts, new.role, new.meta_json);
    END;
    """)
    con.commit()

def _try_backfill_from_memory(con: sqlite3.Connection) -> int:
    """
    Backfill tylko jeśli da się jednoznacznie znaleźć sensowne kolumny w 'memory'.
    Nic nie “zgaduje” agresywnie: jak mapowanie niepewne -> 0 i koniec.
    """
    tabs = _tables(con)
    if "memory" not in tabs:
        return 0

    cols = [c.lower() for c in _columns(con, "memory")]
    # Heurystyka bezpieczna: content/text + (role/type/kind opcjonalnie) + (ts/created_at opcjonalnie)
    content_col = None
    for cand in ("content", "text", "value", "data"):
        if cand in cols:
            content_col = cand
            break
    if not content_col:
        return 0

    user_col = "user_id" if "user_id" in cols else ("user" if "user" in cols else None)
    role_col = None
    for cand in ("role", "kind", "type", "category"):
        if cand in cols:
            role_col = cand
            break
    ts_col = None
    for cand in ("ts", "created_at", "created", "timestamp", "time"):
        if cand in cols:
            ts_col = cand
            break
    meta_col = None
    for cand in ("meta_json", "meta", "metadata", "json"):
        if cand in cols:
            meta_col = cand
            break

    # Minimalny zestaw: content wystarczy (role ustawione na 'user', ts na "now")
    # Ale żeby nie robić śmietnika: backfill tylko jeśli jest też TS albo ROLE.
    if not (ts_col or role_col):
        return 0

    cur = con.cursor()
    # Upewnienie, że nie dubluje: backfill tylko jeśli conversations puste
    cur.execute("SELECT COUNT(1) FROM conversations;")
    if int(cur.fetchone()[0] or 0) > 0:
        return 0

    select_cols = []
    select_cols.append(content_col)
    if user_col:
        select_cols.append(user_col)
    if role_col:
        select_cols.append(role_col)
    if ts_col:
        select_cols.append(ts_col)
    if meta_col:
        select_cols.append(meta_col)

    cur.execute(f"SELECT {', '.join(select_cols)} FROM memory;")
    rows = cur.fetchall()
    inserted = 0

    for r in rows:
        idx = 0
        content = r[idx]; idx += 1
        if content is None:
            continue
        content = str(content).strip()
        if not content:
            continue

        user_id = None
        if user_col:
            user_id = r[idx]; idx += 1
            user_id = None if user_id is None else str(user_id).strip() or None

        role = "user"
        if role_col:
            role = r[idx]; idx += 1
            role = "user" if role is None else str(role).strip() or "user"

        ts = datetime.utcnow().isoformat()
        if ts_col:
            ts_val = r[idx]; idx += 1
            if ts_val is not None:
                ts = str(ts_val).strip() or ts

        meta_json = None
        if meta_col:
            meta_val = r[idx]; idx += 1
            meta_json = None if meta_val is None else str(meta_val)

        cur.execute(
            "INSERT INTO conversations(ts, user_id, role, content, meta_json) VALUES (?, ?, ?, ?, ?);",
            (ts, user_id, role, content, meta_json),
        )
        inserted += 1

    con.commit()
    return inserted

def _rebuild_fts(con: sqlite3.Connection) -> None:
    con.execute("INSERT INTO conversations_fts(conversations_fts) VALUES('rebuild');")
    con.commit()

def main() -> int:
    any_done = False

    for db in DB_CANDIDATES:
        if not db.parent.exists():
            continue
        if not db.exists():
            continue

        _p(f"\n[DB] {db}")
        con = _connect(db)
        try:
            tabs = _tables(con)
            need_conv = "conversations" not in tabs
            need_fts = "conversations_fts" not in tabs

            _p(f"[INFO] has conversations={not need_conv}, conversations_fts={not need_fts}")

            if not (need_conv or need_fts):
                _p("[OK] Nothing to do.")
                continue

            b = _backup(db)
            _p(f"[BACKUP] {b}")

            if need_fts and not _supports_fts5(con):
                _pe("[ERR] SQLite in this environment does not support FTS5. Cannot create conversations_fts.")
                continue

            _ensure_conversations(con)
            _ensure_conversations_fts(con)

            inserted = _try_backfill_from_memory(con)
            if inserted:
                _p(f"[BACKFILL] inserted into conversations: {inserted}")

            _rebuild_fts(con)

            tabs2 = sorted(_tables(con))
            _p(f"[DONE] tables now: {len(tabs2)}")
            for t in tabs2:
                if "conver" in t or "fts" in t:
                    _p(f" - {t}")

            any_done = True
        finally:
            con.close()

    if not any_done:
        _p("\n[INFO] No changes applied (either DBs already ok, or DBs not found).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
