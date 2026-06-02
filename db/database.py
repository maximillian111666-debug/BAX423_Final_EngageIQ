import sqlite3
import os
import json
import numpy as np
from datetime import datetime


def get_connection(db_path: str = None) -> sqlite3.Connection:
    from config import DB_PATH
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: str = None):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            source        TEXT NOT NULL,
            external_id   TEXT NOT NULL,
            url           TEXT NOT NULL,
            title         TEXT NOT NULL,
            body          TEXT DEFAULT '',
            domain        TEXT NOT NULL,
            tags          TEXT DEFAULT '[]',
            stars         INTEGER DEFAULT 0,
            forks         INTEGER DEFAULT 0,
            comments      INTEGER DEFAULT 0,
            score         INTEGER DEFAULT 0,
            activity_score REAL DEFAULT 0.0,
            created_at    TEXT DEFAULT '',
            fetched_at    TEXT NOT NULL,
            minhash       TEXT DEFAULT '[]',
            UNIQUE(source, external_id)
        );

        CREATE TABLE IF NOT EXISTS embeddings (
            opportunity_id INTEGER PRIMARY KEY,
            vector         BLOB NOT NULL,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        );

        CREATE TABLE IF NOT EXISTS user_profiles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            bio        TEXT DEFAULT '',
            interests  TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS profile_embeddings (
            profile_id INTEGER PRIMARY KEY,
            vector     BLOB NOT NULL,
            FOREIGN KEY (profile_id) REFERENCES user_profiles(id)
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id     INTEGER NOT NULL,
            opportunity_id INTEGER NOT NULL,
            action         TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            FOREIGN KEY (profile_id)     REFERENCES user_profiles(id),
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        );

        CREATE TABLE IF NOT EXISTS bandit_state (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id     INTEGER NOT NULL,
            domain         TEXT NOT NULL,
            alpha          REAL DEFAULT 1.0,
            beta           REAL DEFAULT 1.0,
            updated_at     TEXT NOT NULL,
            UNIQUE(profile_id, domain)
        );

        CREATE INDEX IF NOT EXISTS idx_opp_domain  ON opportunities(domain);
        CREATE INDEX IF NOT EXISTS idx_opp_source  ON opportunities(source);
        CREATE INDEX IF NOT EXISTS idx_fb_profile  ON feedback(profile_id);
        CREATE INDEX IF NOT EXISTS idx_fb_opp      ON feedback(opportunity_id);
    """)
    conn.commit()
    conn.close()


def insert_opportunity(conn: sqlite3.Connection, opp: dict) -> int | None:
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO opportunities
            (source, external_id, url, title, body, domain, tags,
             stars, forks, comments, score, activity_score, created_at, fetched_at, minhash)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            opp["source"], str(opp["external_id"]), opp["url"], opp["title"][:500],
            opp.get("body", "")[:2000], opp["domain"],
            json.dumps(opp.get("tags", [])),
            opp.get("stars", 0), opp.get("forks", 0), opp.get("comments", 0),
            opp.get("score", 0), opp.get("activity_score", 0.0),
            opp.get("created_at", ""), datetime.now().isoformat(),
            json.dumps(opp.get("minhash", []))
        ))
        conn.commit()
        return cur.lastrowid if cur.rowcount > 0 else None
    except Exception:
        conn.rollback()
        return None


def save_embedding(conn: sqlite3.Connection, opp_id: int, vector: np.ndarray):
    conn.execute(
        "INSERT OR REPLACE INTO embeddings (opportunity_id, vector) VALUES (?, ?)",
        (opp_id, vector.astype(np.float32).tobytes())
    )
    conn.commit()


def load_embedding(conn: sqlite3.Connection, opp_id: int) -> np.ndarray | None:
    row = conn.execute(
        "SELECT vector FROM embeddings WHERE opportunity_id = ?", (opp_id,)
    ).fetchone()
    if row:
        return np.frombuffer(row[0], dtype=np.float32)
    return None


def save_profile_embedding(conn: sqlite3.Connection, profile_id: int, vector: np.ndarray):
    conn.execute(
        "INSERT OR REPLACE INTO profile_embeddings (profile_id, vector) VALUES (?, ?)",
        (profile_id, vector.astype(np.float32).tobytes())
    )
    conn.commit()


def load_profile_embedding(conn: sqlite3.Connection, profile_id: int) -> np.ndarray | None:
    row = conn.execute(
        "SELECT vector FROM profile_embeddings WHERE profile_id = ?", (profile_id,)
    ).fetchone()
    if row:
        return np.frombuffer(row[0], dtype=np.float32)
    return None


def count_opportunities(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]


def count_embeddings(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]


def get_opportunities(conn: sqlite3.Connection, domain: str = None, source: str = None,
                      limit: int = 5000, offset: int = 0) -> list[dict]:
    q = "SELECT * FROM opportunities WHERE 1=1"
    params: list = []
    if domain:
        q += " AND domain = ?"
        params.append(domain)
    if source:
        q += " AND source = ?"
        params.append(source)
    q += " ORDER BY activity_score DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_opportunity_by_id(conn: sqlite3.Connection, opp_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    return dict(row) if row else None


def get_or_create_profile(conn: sqlite3.Connection, name: str, bio: str = "",
                           interests: list[str] = None) -> dict:
    row = conn.execute("SELECT * FROM user_profiles WHERE name = ?", (name,)).fetchone()
    if row:
        return dict(row)
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO user_profiles (name, bio, interests, created_at, updated_at) VALUES (?,?,?,?,?)",
        (name, bio, json.dumps(interests or []), now, now)
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM user_profiles WHERE name = ?", (name,)).fetchone())


def update_profile(conn: sqlite3.Connection, profile_id: int, bio: str, interests: list[str]):
    conn.execute(
        "UPDATE user_profiles SET bio=?, interests=?, updated_at=? WHERE id=?",
        (bio, json.dumps(interests), datetime.now().isoformat(), profile_id)
    )
    conn.commit()


def insert_feedback(conn: sqlite3.Connection, profile_id: int, opp_id: int, action: str):
    conn.execute(
        "INSERT INTO feedback (profile_id, opportunity_id, action, created_at) VALUES (?,?,?,?)",
        (profile_id, opp_id, action, datetime.now().isoformat())
    )
    conn.commit()


def get_feedback_counts(conn: sqlite3.Connection, profile_id: int) -> dict:
    rows = conn.execute(
        "SELECT action, COUNT(*) as cnt FROM feedback WHERE profile_id=? GROUP BY action",
        (profile_id,)
    ).fetchall()
    return {r["action"]: r["cnt"] for r in rows}


def get_bandit_state(conn: sqlite3.Connection, profile_id: int) -> dict[str, tuple[float, float]]:
    rows = conn.execute(
        "SELECT domain, alpha, beta FROM bandit_state WHERE profile_id=?", (profile_id,)
    ).fetchall()
    return {r["domain"]: (r["alpha"], r["beta"]) for r in rows}


def update_bandit(conn: sqlite3.Connection, profile_id: int, domain: str, alpha: float, beta: float):
    conn.execute("""
        INSERT INTO bandit_state (profile_id, domain, alpha, beta, updated_at)
        VALUES (?,?,?,?,?)
        ON CONFLICT(profile_id, domain) DO UPDATE SET alpha=excluded.alpha, beta=excluded.beta, updated_at=excluded.updated_at
    """, (profile_id, domain, alpha, beta, datetime.now().isoformat()))
    conn.commit()


def get_domain_stats(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("""
        SELECT domain,
               COUNT(*) as count,
               AVG(stars) as avg_stars,
               AVG(comments) as avg_comments,
               SUM(stars) as total_stars,
               MAX(fetched_at) as latest_fetch
        FROM opportunities
        GROUP BY domain
        ORDER BY count DESC
    """).fetchall()]


def get_time_series(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("""
        SELECT substr(fetched_at, 1, 10) as day,
               domain,
               COUNT(*) as count,
               SUM(stars) as stars
        FROM opportunities
        WHERE fetched_at != ''
        GROUP BY day, domain
        ORDER BY day
    """).fetchall()]


def get_top_opportunities(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM opportunities ORDER BY activity_score DESC LIMIT ?", (limit,)
    ).fetchall()]
