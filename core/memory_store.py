
import os, json, sqlite3, time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = os.getenv("MEM_DB") or str((Path(os.getenv("WORKSPACE",".")) / "data" / "mem.db").absolute())

def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def _now() -> float: return time.time()

def _fts_schema_ok(cur) -> bool:
    try:
        row = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='conversations_fts'").fetchone()
        if not row: 
            return False
        sql = row["sql"] or ""
        # We want unicode61 + prefix=
        return "unicode61" in sql and "prefix=" in sql
    except Exception:
        return False

def init_db():
    con = _connect(); cur = con.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS conversations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT DEFAULT '[]',
        created_at REAL NOT NULL
    );
    """)
    # FTS with desired tokenizer + prefixes
    if not _fts_schema_ok(cur):
        # Rebuild FTS with better tokenizer/prefixes
        cur.execute("DROP TABLE IF EXISTS conversations_fts")
        cur.execute("""
            CREATE VIRTUAL TABLE conversations_fts USING fts5(
                content, 
                content='conversations', 
                content_rowid='id',
                tokenize = 'unicode61 remove_diacritics 2',
                prefix = '2 3 4'
            );
        """)
        # Backfill current rows
        cur.execute("INSERT INTO conversations_fts(rowid, content) SELECT id, content FROM conversations")
    # Triggers (idempotent recreates safe in SQLite; but wrap in try/ignore)
    cur.executescript("""
    CREATE TRIGGER IF NOT EXISTS conversations_ai AFTER INSERT ON conversations BEGIN
        INSERT INTO conversations_fts(rowid, content) VALUES (new.id, new.content);
    END;
    CREATE TRIGGER IF NOT EXISTS conversations_ad AFTER DELETE ON conversations BEGIN
        INSERT INTO conversations_fts(conversations_fts, rowid, content) VALUES('delete', old.id, old.content);
    END;
    CREATE TRIGGER IF NOT EXISTS conversations_au AFTER UPDATE ON conversations BEGIN
        INSERT INTO conversations_fts(conversations_fts, rowid, content) VALUES('delete', old.id, old.content);
        INSERT INTO conversations_fts(rowid, content) VALUES (new.id, new.content);
    END;

    CREATE TABLE IF NOT EXISTS psyche_state(
        user_id TEXT PRIMARY KEY,
        mood REAL DEFAULT 0.0,
        energy REAL DEFAULT 0.0,
        stress REAL DEFAULT 0.0,
        focus REAL DEFAULT 0.0,
        updated_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS psyche_journal(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        mood_change REAL NOT NULL,
        note TEXT NOT NULL,
        created_at REAL NOT NULL
    );
    """)
    con.commit(); con.close()

def save_message(user_id: str, role: str, content: str, tags: Optional[List[str]]=None) -> int:
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute("INSERT INTO conversations(user_id, role, content, tags, created_at) VALUES(?,?,?,?,?)",
                (user_id, role, content, json.dumps(tags or []), _now()))
    con.commit()
    rid = cur.lastrowid
    con.close()
    return rid

def recent_messages(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute("SELECT id, role, content, created_at FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows[::-1]

def search_messages(user_id: str, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    init_db()
    con = _connect(); cur = con.cursor()
    # FTS5 with bm25 ranking; prefix support covers partials
    cur.execute("""
        SELECT c.id, c.role, c.content, c.created_at, bm25(conversations_fts) AS rank
        FROM conversations_fts
        JOIN conversations c ON c.id = conversations_fts.rowid
        WHERE conversations_fts MATCH ? AND c.user_id=?
        ORDER BY rank LIMIT ?
    """, (query, user_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def get_state(user_id: str) -> Dict[str, float]:
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute("SELECT user_id, mood, energy, stress, focus, updated_at FROM psyche_state WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        state = {"user_id": user_id, "mood": 0.0, "energy": 0.0, "stress": 0.0, "focus": 0.0, "updated_at": _now()}
        cur.execute("INSERT OR REPLACE INTO psyche_state(user_id, mood, energy, stress, focus, updated_at) VALUES(?,?,?,?,?,?)",
                    (state["user_id"], state["mood"], state["energy"], state["stress"], state["focus"], state["updated_at"]))
        con.commit(); con.close(); return state
    con.close(); return dict(row)

def _clamp(v: float, lo=-1.0, hi=1.0) -> float:
    return max(lo, min(hi, float(v)))

def update_state(user_id: str, *, mood=None, energy=None, stress=None, focus=None) -> Dict[str, float]:
    s = get_state(user_id)
    if mood is not None: s["mood"] = _clamp(mood)
    if energy is not None: s["energy"] = _clamp(energy)
    if stress is not None: s["stress"] = _clamp(stress)
    if focus is not None: s["focus"] = _clamp(focus)
    s["updated_at"] = _now()
    con = _connect(); cur = con.cursor()
    cur.execute("UPDATE psyche_state SET mood=?, energy=?, stress=?, focus=?, updated_at=? WHERE user_id=?",
                (s["mood"], s["energy"], s["stress"], s["focus"], s["updated_at"], user_id))
    con.commit(); con.close(); return s

def apply_delta(user_id: str, *, mood=0.0, energy=0.0, stress=0.0, focus=0.0) -> Dict[str, float]:
    s = get_state(user_id)
    return update_state(user_id,
                        mood=s["mood"] + float(mood),
                        energy=s["energy"] + float(energy),
                        stress=s["stress"] + float(stress),
                        focus=s["focus"] + float(focus))

def journal(user_id: str, sentiment: str, mood_change: float, note: str) -> int:
    init_db()
    con = _connect(); cur = con.cursor()
    cur.execute("INSERT INTO psyche_journal(user_id, sentiment, mood_change, note, created_at) VALUES(?,?,?,?,?)",
                (user_id, sentiment, float(mood_change), note, _now()))
    con.commit(); rid = cur.lastrowid; con.close(); return rid

def export_journal(format: str = "json") -> str:
    """Return journal as text: json or csv."""
    init_db()
    con = _connect(); cur = con.cursor()
    rows = [dict(r) for r in cur.execute("SELECT * FROM psyche_journal ORDER BY id ASC").fetchall()]
    con.close()
    if format == "csv":
        import io, csv
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["id","user_id","sentiment","mood_change","note","created_at"])
        w.writeheader()
        for r in rows: w.writerow(r)
        return buf.getvalue()
    return json.dumps(rows, ensure_ascii=False)

def export_conversations(user_id: Optional[str] = None, format: str = "json") -> str:
    init_db()
    con = _connect(); cur = con.cursor()
    if user_id:
        rows = [dict(r) for r in cur.execute("SELECT * FROM conversations WHERE user_id=? ORDER BY id ASC", (user_id,)).fetchall()]
    else:
        rows = [dict(r) for r in cur.execute("SELECT * FROM conversations ORDER BY id ASC").fetchall()]
    con.close()
    if format == "csv":
        import io, csv
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["id","user_id","role","content","tags","created_at"])
        w.writeheader()
        for r in rows: w.writerow(r)
        return buf.getvalue()
    return json.dumps(rows, ensure_ascii=False)


# --- session_prefs: per-user lightweight prefs (e.g., lang) ---
def _init_prefs():
    con = _connect(); cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS session_prefs(
        user_id TEXT PRIMARY KEY,
        lang TEXT,
        updated_at REAL NOT NULL
    );
    """)
    con.commit(); con.close()

def set_pref_lang(user_id: str, lang: str):
    _init_prefs()
    con = _connect(); cur = con.cursor()
    cur.execute("INSERT INTO session_prefs(user_id, lang, updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang, updated_at=excluded.updated_at",
                (user_id, (lang or "").lower()[:8], _now()))
    con.commit(); con.close()

def get_pref_lang(user_id: str) -> str:
    _init_prefs()
    con = _connect(); cur = con.cursor()
    cur.execute("SELECT lang FROM session_prefs WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return (row["lang"] if row and row["lang"] else "") if row else ""


# ======== LTM UPGRADE: FTS5 + DEDUPE + SCORING ========
import json as _J, hashlib as _H, math as _M

def _fts_tokenizer():
    # prefer unicode61 with diacritics to keep PL glyphs searchable
    return "unicode61 remove_diacritics 2"

def _init_ltm():
    con = _connect(); cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ltm(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant TEXT NOT NULL,
        key_hash TEXT NOT NULL,
        text TEXT NOT NULL,
        meta_json TEXT,
        lang TEXT,
        conf REAL DEFAULT 0.5,
        source TEXT,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ltm_uniq ON ltm(tenant, key_hash)")
    cur.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS ltm_fts USING fts5(text, content='ltm', content_rowid='id', tokenize='{_fts_tokenizer()}')")
    # triggers keep FTS in sync
    cur.execute("""CREATE TRIGGER IF NOT EXISTS ltm_ai AFTER INSERT ON ltm BEGIN
        INSERT INTO ltm_fts(rowid, text) VALUES (new.id, new.text);
    END;""")
    cur.execute("""CREATE TRIGGER IF NOT EXISTS ltm_ad AFTER DELETE ON ltm BEGIN
        INSERT INTO ltm_fts(ltm_fts, rowid, text) VALUES('delete', old.id, old.text);
    END;""")
    cur.execute("""CREATE TRIGGER IF NOT EXISTS ltm_au AFTER UPDATE ON ltm BEGIN
        INSERT INTO ltm_fts(ltm_fts, rowid, text) VALUES('delete', old.id, old.text);
        INSERT INTO ltm_fts(rowid, text) VALUES (new.id, new.text);
    END;""")
    con.commit(); con.close()

def _hash_text(t: str) -> str:
    return _H.sha1((t or "").strip().lower().encode("utf-8")).hexdigest()

def add_memory(tenant: str, text: str, *, meta: dict|None=None, conf: float=0.6, lang: str|None=None, source: str|None=None) -> dict:
    _init_ltm()
    h = _hash_text(text)
    ts = _now()
    con = _connect(); cur = con.cursor()
    cur.execute("""INSERT INTO ltm(tenant, key_hash, text, meta_json, lang, conf, source, created_at, updated_at)
                   VALUES(?,?,?,?,?,?,?, ?, ?)
                   ON CONFLICT(tenant,key_hash) DO UPDATE SET
                     text=excluded.text, meta_json=excluded.meta_json, lang=excluded.lang, conf=max(ltm.conf, excluded.conf),
                     source=COALESCE(excluded.source, ltm.source), updated_at=excluded.updated_at""",
                (tenant, h, text, _J.dumps(meta or {}, ensure_ascii=False), (lang or "")[:8], float(conf), source or "", ts, ts))
    con.commit()
    cur.execute("SELECT id FROM ltm WHERE tenant=? AND key_hash=?", (tenant, h))
    rid = cur.fetchone()[0]
    con.close()
    return {"id": rid, "hash": h}

def _score(bm25: float, age_s: float, conf: float) -> float:
    # Lower bm25 is better in SQLite => invert. Age penalty: half-life ~ 180 days.
    inv = 1.0 / (1.0 + bm25)
    days = age_s / (3600*24)
    decay = 0.5 ** (days / 180.0)  # 180-day half-life
    return inv * (0.6 + 0.4*conf) * (0.5 + 0.5*decay)

def search_memory(tenant: str, query: str, topk: int=8) -> list[dict]:
    _init_ltm()
    now = _now()
    con = _connect(); con.row_factory = sqlite3.Row
    cur = con.cursor()
    # Use bm25(ltm_fts) for relevance
    cur.execute("""
      SELECT ltm.id, ltm.text, ltm.meta_json, ltm.lang, ltm.conf, ltm.source, ltm.created_at, ltm.updated_at, bm25(ltm_fts) AS bm
      FROM ltm_fts JOIN ltm ON ltm_fts.rowid = ltm.id
      WHERE ltm.tenant=? AND ltm_fts MATCH ?
      ORDER BY bm LIMIT 64
    """, (tenant, query))
    rows = cur.fetchall()
    out = []
    for r in rows:
        age = now - float(r["updated_at"])
        sc = _score(float(r["bm"]), age, float(r["conf"] or 0.5))
        out.append({
            "id": r["id"],
            "text": r["text"],
            "meta": _J.loads(r["meta_json"] or "{}"),
            "lang": r["lang"] or "",
            "conf": float(r["conf"] or 0.5),
            "source": r["source"] or "",
            "score": sc
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:max(1, min(int(topk), 32))]

def memory_export(tenant: str) -> dict:
    _init_ltm()
    con = _connect(); con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT id, text, meta_json, lang, conf, source, created_at, updated_at FROM ltm WHERE tenant=? ORDER BY id", (tenant,))
    items = []
    for r in cur.fetchall():
        items.append({
            "id": r["id"],
            "text": r["text"],
            "meta": _J.loads(r["meta_json"] or "{}"),
            "lang": r["lang"],
            "conf": r["conf"],
            "source": r["source"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    con.close()
    return {"tenant": tenant, "count": len(items), "items": items}

def memory_import(tenant: str, items: list[dict]) -> int:
    _init_ltm()
    n=0
    for it in items or []:
        add_memory(tenant, it.get("text",""), meta=it.get("meta") or {}, conf=float(it.get("conf") or 0.6), lang=it.get("lang") or "", source=it.get("source") or "")
        n+=1
    return n

def memory_optimize():
    con = _connect(); cur = con.cursor()
    cur.execute("PRAGMA optimize;")
    cur.execute("VACUUM;")
    con.commit(); con.close()
