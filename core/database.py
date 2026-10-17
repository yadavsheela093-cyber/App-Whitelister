"""
core/database.py
Database layer for Application Whitelisting Tool.
"""
 
import sqlite3
import os
 
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whitelister.db")
 
 
def _norm(path: str) -> str:
    """Normalise a path: absolute + resolved + lowercase on Windows."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))
 
 
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn
 
 
def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS whitelist (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT    NOT NULL,
                path      TEXT    NOT NULL UNIQUE,
                sha256    TEXT    NOT NULL,
                added_on  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                enabled   INTEGER NOT NULL DEFAULT 1
            );
 
            CREATE TABLE IF NOT EXISTS logs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name   TEXT    NOT NULL,
                path       TEXT    NOT NULL,
                sha256     TEXT,
                status     TEXT    NOT NULL CHECK(status IN ('ALLOWED','BLOCKED','HASH_MISMATCH','ERROR')),
                reason     TEXT,
                timestamp  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );
 
            CREATE TABLE IF NOT EXISTS admin (
                id            INTEGER PRIMARY KEY CHECK(id = 1),
                password_hash TEXT NOT NULL
            );
 
            CREATE INDEX IF NOT EXISTS idx_logs_status    ON logs(status);
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_wl_name        ON whitelist(name);
        """)
 
 
def add_app(name: str, path: str, sha256: str) -> tuple:
    """Add app to whitelist. Always stores the normalised path."""
    normalised = _norm(path)
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO whitelist (name, path, sha256) VALUES (?, ?, ?)",
                (name, normalised, sha256)
            )
        return True, f"'{name}' added to whitelist."
    except sqlite3.IntegrityError:
        return False, f"'{name}' is already in the whitelist."
    except Exception as e:
        return False, str(e)
 
 
def remove_app(app_id: int) -> tuple:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM whitelist WHERE id = ?", (app_id,))
        if cur.rowcount:
            return True, "Application removed."
        return False, "Application not found."
 
 
def get_all_apps(search: str = "") -> list:
    with get_connection() as conn:
        if search:
            pattern = f"%{search}%"
            return conn.execute(
                "SELECT * FROM whitelist WHERE name LIKE ? OR path LIKE ? ORDER BY name",
                (pattern, pattern)
            ).fetchall()
        return conn.execute("SELECT * FROM whitelist ORDER BY name").fetchall()
 
 
def get_app_by_path(path: str):
    """
    Case-insensitive, normalised path lookup.
    Fixes Windows issues where C:\\Users and c:\\users refer to the same file.
    Also fixes forward-slash vs backslash mismatches.
    """
    query_norm = _norm(path)
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM whitelist WHERE enabled = 1").fetchall()
        for row in rows:
            if _norm(row["path"]) == query_norm:
                return row
    return None
 
 
def update_app_hash(app_id: int, sha256: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE whitelist SET sha256 = ? WHERE id = ?", (sha256, app_id))
 
 
def toggle_app(app_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT enabled FROM whitelist WHERE id=?", (app_id,)).fetchone()
        if row is None:
            return False
        new_state = 0 if row["enabled"] else 1
        conn.execute("UPDATE whitelist SET enabled=? WHERE id=?", (new_state, app_id))
        return bool(new_state)
 
 
def add_log(app_name: str, path: str, status: str,
            sha256: str = "", reason: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO logs (app_name, path, sha256, status, reason) VALUES (?,?,?,?,?)",
            (app_name, path, sha256 or None, status, reason or None)
        )
 
 
def get_logs(status_filter: str = "ALL", limit: int = 500) -> list:
    with get_connection() as conn:
        if status_filter == "ALL":
            return conn.execute(
                "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return conn.execute(
            "SELECT * FROM logs WHERE status=? ORDER BY timestamp DESC LIMIT ?",
            (status_filter, limit)
        ).fetchall()
 
 
def clear_logs() -> int:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM logs")
        return cur.rowcount
 
 
def get_stats() -> dict:
    with get_connection() as conn:
        total_wl  = conn.execute("SELECT COUNT(*) FROM whitelist").fetchone()[0]
        allowed   = conn.execute("SELECT COUNT(*) FROM logs WHERE status='ALLOWED'").fetchone()[0]
        blocked   = conn.execute("SELECT COUNT(*) FROM logs WHERE status='BLOCKED'").fetchone()[0]
        mismatch  = conn.execute("SELECT COUNT(*) FROM logs WHERE status='HASH_MISMATCH'").fetchone()[0]
        total_log = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    return {
        "whitelisted": total_wl,
        "allowed": allowed,
        "blocked": blocked,
        "hash_mismatch": mismatch,
        "total_logs": total_log,
    }
 
 
def set_admin_password(password_hash: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admin (id, password_hash) VALUES (1, ?)",
            (password_hash,)
        )
 
 
def get_admin_password_hash():
    with get_connection() as conn:
        row = conn.execute("SELECT password_hash FROM admin WHERE id=1").fetchone()
        return row["password_hash"] if row else None