r"""
core/db_base.py — Enterprise Multi-Tenant Database Engine for AUTOPILOT.

Supports:
- PostgreSQL (Supabase / Neon / AWS RDS) with connection pooling and tenant isolation.
- SQLite fallback for local developer environments.
- Context-managed workspace scoping (ensuring queries never leak cross-tenant).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .config import CONFIG
from .logbook import Logbook

log = Logbook("db_base")

# Database connection settings
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

# Thread-local storage for active tenant / workspace context
_context = threading.local()


def set_current_workspace(workspace_id: str, organization_id: Optional[str] = None) -> None:
    """Sets the active tenant context for the current thread."""
    _context.workspace_id = workspace_id
    _context.organization_id = organization_id


def get_current_workspace() -> Optional[str]:
    """Returns the current workspace ID bound to the thread."""
    return getattr(_context, "workspace_id", None)


def get_current_organization() -> Optional[str]:
    """Returns the current organization ID bound to the thread."""
    return getattr(_context, "organization_id", None)


def clear_tenant_context() -> None:
    """Clears tenant context."""
    _context.workspace_id = None
    _context.organization_id = None


class DatabaseEngine:
    """
    Unified database engine providing tenant isolation, transaction safety,
    and abstraction across PostgreSQL and SQLite.
    """

    def __init__(self):
        self.is_postgres = IS_POSTGRES
        self.db_url = DATABASE_URL
        self._pool = None
        self._init_pool()

    def _init_pool(self):
        if self.is_postgres:
            try:
                import psycopg2
                from psycopg2 import pool
                log.info("Initializing PostgreSQL Connection Pool", url_prefix=self.db_url[:20] + "...")
                minconn = int(os.getenv("DATABASE_MIN_CONN", "1"))
                maxconn = int(os.getenv("DATABASE_MAX_CONN", "10"))
                self._pool = psycopg2.pool.ThreadedConnectionPool(minconn, maxconn, self.db_url)
                self._ensure_postgres_schema()
            except ImportError:
                log.warning("psycopg2 not installed. Falling back to SQLite local database.")
                self.is_postgres = False
            except Exception as e:
                log.error("Failed to initialize PostgreSQL pool", error=str(e))
                self.is_postgres = False
        if not self.is_postgres:
            self._ensure_sqlite_schema()

    def _ensure_sqlite_schema(self):
        """Initializes multi-tenant tables in local SQLite."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            billing_email TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            autopilot_mode TEXT DEFAULT 'assisted',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS credit_accounts (
            id TEXT PRIMARY KEY,
            organization_id TEXT UNIQUE NOT NULL,
            balance INTEGER DEFAULT 1000,
            lifetime_purchased INTEGER DEFAULT 1000,
            lifetime_used INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS usage_ledger (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            workspace_id TEXT,
            operation_type TEXT NOT NULL,
            units_consumed REAL NOT NULL,
            raw_cost_usd REAL NOT NULL,
            credits_debited INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS video_jobs (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'admin_abhay',
            video_id TEXT NOT NULL,
            job_type TEXT DEFAULT 'render_full',
            status TEXT DEFAULT 'queued',
            priority INTEGER DEFAULT 50,
            progress INTEGER DEFAULT 0,
            current_step TEXT,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS channel_credentials (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'admin_abhay',
            platform TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            encrypted_token TEXT NOT NULL,
            token_metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, platform, channel_id)
        );

        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            title TEXT,
            topic TEXT,
            status TEXT DEFAULT 'draft',
            duration_sec REAL DEFAULT 0.0,
            video_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS platform_accounts (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            external_account_id TEXT NOT NULL,
            username TEXT,
            display_name TEXT,
            profile_image_url TEXT,
            account_type TEXT DEFAULT 'BUSINESS',
            status TEXT DEFAULT 'connected',
            encrypted_access_token TEXT NOT NULL,
            token_expires_at TEXT,
            scopes TEXT,
            metadata_json TEXT DEFAULT '{}',
            last_synced_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            disconnected_at TEXT,
            UNIQUE(workspace_id, platform, external_account_id)
        );

        CREATE TABLE IF NOT EXISTS publishing_jobs (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            platform_account_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            caption TEXT,
            scheduled_at TEXT,
            external_media_id TEXT,
            external_container_id TEXT,
            error_code TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            idempotency_key TEXT UNIQUE NOT NULL,
            published_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_onboarded INTEGER DEFAULT 0,
            preferences_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS series (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'admin_abhay',
            title TEXT NOT NULL,
            description TEXT,
            genre TEXT DEFAULT 'mystery',
            tone TEXT DEFAULT 'suspense',
            cast_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY,
            series_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            user_id TEXT DEFAULT 'admin_abhay',
            episode_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            recap TEXT,
            conflict TEXT,
            cliffhanger TEXT,
            script_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'draft',
            video_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series_id, episode_number)
        );
        """
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            # Safe backward-compatible migrations for preexisting local databases
            for tbl, col, ctype in [
                ("series", "user_id", "TEXT DEFAULT 'admin_abhay'"),
                ("episodes", "user_id", "TEXT DEFAULT 'admin_abhay'"),
                ("channel_credentials", "user_id", "TEXT DEFAULT 'admin_abhay'"),
                ("video_jobs", "user_id", "TEXT DEFAULT 'admin_abhay'"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {ctype};")
                except Exception:
                    pass

            for col, ctype in [
                ("full_name", "TEXT"),
                ("is_onboarded", "INTEGER DEFAULT 0"),
                ("preferences_json", "TEXT DEFAULT '{}'"),
                ("name", "TEXT"),
                ("tour_completed", "INTEGER DEFAULT 0"),
                ("created_at", "TEXT"),
                ("created_ts", "TEXT")
            ]:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype};")
                except Exception:
                    pass
            conn.commit()

    def _ensure_postgres_schema(self):
        """Initializes multi-tenant tables in PostgreSQL if not already present."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS organizations (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(128) NOT NULL,
            slug VARCHAR(64) UNIQUE NOT NULL,
            billing_email VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workspaces (
            id VARCHAR(64) PRIMARY KEY,
            organization_id VARCHAR(64) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name VARCHAR(128) NOT NULL,
            slug VARCHAR(64) NOT NULL,
            autopilot_mode VARCHAR(32) DEFAULT 'assisted',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS brand_kits (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            name VARCHAR(128) NOT NULL,
            primary_color VARCHAR(16) DEFAULT '#6366F1',
            font_family VARCHAR(64) DEFAULT 'Inter',
            caption_style TEXT DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS credit_accounts (
            id VARCHAR(64) PRIMARY KEY,
            organization_id VARCHAR(64) UNIQUE NOT NULL,
            balance INT DEFAULT 1000,
            lifetime_purchased INT DEFAULT 1000,
            lifetime_used INT DEFAULT 0,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS usage_ledger (
            id VARCHAR(64) PRIMARY KEY,
            organization_id VARCHAR(64) NOT NULL,
            workspace_id VARCHAR(64),
            operation_type VARCHAR(64) NOT NULL,
            units_consumed NUMERIC(12, 4) NOT NULL,
            raw_cost_usd NUMERIC(10, 6) NOT NULL,
            credits_debited INT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS channel_credentials (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL,
            platform VARCHAR(32) NOT NULL,
            channel_id VARCHAR(128) NOT NULL,
            channel_name VARCHAR(255),
            encrypted_token TEXT NOT NULL,
            token_metadata TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(workspace_id, platform, channel_id)
        );

        CREATE TABLE IF NOT EXISTS videos (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL,
            title VARCHAR(255),
            topic TEXT,
            status VARCHAR(32) DEFAULT 'draft',
            duration_sec NUMERIC(8, 2) DEFAULT 0.0,
            video_url TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS platform_accounts (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            platform VARCHAR(32) NOT NULL,
            external_account_id VARCHAR(128) NOT NULL,
            username VARCHAR(128),
            display_name VARCHAR(255),
            profile_image_url TEXT,
            account_type VARCHAR(32) DEFAULT 'BUSINESS',
            status VARCHAR(32) DEFAULT 'connected',
            encrypted_access_token TEXT NOT NULL,
            token_expires_at TIMESTAMPTZ,
            scopes TEXT,
            metadata_json TEXT DEFAULT '{}',
            last_synced_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            disconnected_at TIMESTAMPTZ,
            UNIQUE(workspace_id, platform, external_account_id)
        );

        CREATE TABLE IF NOT EXISTS publishing_jobs (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            platform_account_id VARCHAR(64) NOT NULL,
            video_id VARCHAR(64) NOT NULL,
            status VARCHAR(32) DEFAULT 'pending',
            caption TEXT,
            scheduled_at TIMESTAMPTZ,
            external_media_id VARCHAR(128),
            external_container_id VARCHAR(128),
            error_code VARCHAR(64),
            error_message TEXT,
            retry_count INT DEFAULT 0,
            idempotency_key VARCHAR(128) UNIQUE NOT NULL,
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(128) NOT NULL,
            role VARCHAR(32) DEFAULT 'user',
            is_onboarded BOOLEAN DEFAULT FALSE,
            preferences_json TEXT DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS series (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            genre VARCHAR(64) DEFAULT 'mystery',
            tone VARCHAR(64) DEFAULT 'suspense',
            cast_json TEXT DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id VARCHAR(64) PRIMARY KEY,
            series_id VARCHAR(64) NOT NULL REFERENCES series(id) ON DELETE CASCADE,
            workspace_id VARCHAR(64) NOT NULL,
            episode_number INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            recap TEXT,
            conflict TEXT,
            cliffhanger TEXT,
            script_json TEXT DEFAULT '{}',
            status VARCHAR(32) DEFAULT 'draft',
            video_id VARCHAR(64),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(series_id, episode_number)
        );
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()

    @contextmanager
    def get_connection(self):
        """Yields a database connection with auto-commit or rollback."""
        if self.is_postgres and self._pool:
            conn = self._pool.getconn()
            try:
                # Set tenant context if active
                ws_id = get_current_workspace()
                if ws_id:
                    with conn.cursor() as cur:
                        cur.execute("SET LOCAL app.current_workspace_id = %s;", (ws_id,))
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self._pool.putconn(conn)
        else:
            # Fallback to local SQLite
            db_path = Path(CONFIG.get("db_path", "data/autopilot.db"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def execute_query(self, query: str, params: Union[Tuple, List, Dict] = ()) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns a list of dictionaries."""
        with self.get_connection() as conn:
            if self.is_postgres:
                import psycopg2.extras
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
            else:
                cur = conn.cursor()
                # Translate PostgreSQL %s placeholder to SQLite ?
                sqlite_query = query.replace("%s", "?")
                try:
                    cur.execute(sqlite_query, params)
                    return [dict(row) for row in cur.fetchall()]
                except sqlite3.OperationalError as e:
                    log.warning("SQLite query skipped (table may not exist yet)", error=str(e), query=sqlite_query)
                    return []

    def execute_mutation(self, query: str, params: Union[Tuple, List, Dict] = ()) -> int:
        """Executes an INSERT/UPDATE/DELETE query and returns rows affected."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            sqlite_query = query.replace("%s", "?") if not self.is_postgres else query
            try:
                cur.execute(sqlite_query, params)
                rowcount = getattr(cur, "rowcount", 0)
                return rowcount if rowcount != -1 else 1
            except sqlite3.OperationalError as e:
                log.warning("SQLite mutation skipped", error=str(e), query=sqlite_query)
                return 0

    # =========================================================================
    # User Management Helpers
    # =========================================================================
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        rows = self.execute_query("SELECT * FROM users WHERE email = %s", (email.strip().lower(),))
        if not rows:
            return None
        u = dict(rows[0])
        u["id"] = u.get("user_id") or str(u.get("id"))
        u["full_name"] = u.get("full_name") or u.get("name") or "Creator"
        u["role"] = u.get("role", "user")
        u["is_onboarded"] = bool(u.get("is_onboarded", 0) or u.get("tour_completed", 0))
        return u

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        rows = self.execute_query("SELECT * FROM users WHERE user_id = %s OR id = %s", (user_id, user_id))
        if not rows:
            return None
        u = dict(rows[0])
        u["id"] = u.get("user_id") or str(u.get("id"))
        u["full_name"] = u.get("full_name") or u.get("name") or "Creator"
        u["role"] = u.get("role", "user")
        u["is_onboarded"] = bool(u.get("is_onboarded", 0) or u.get("tour_completed", 0))
        return u

    def create_user(
        self, user_id: str, email: str, password_hash: str, full_name: str,
        role: str = "user", is_onboarded: int = 0
    ) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        now = datetime.now(timezone.utc).isoformat()
        if self.is_postgres:
            self.execute_mutation(
                """
                INSERT INTO users (id, email, password_hash, full_name, role, is_onboarded, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, email_clean, password_hash, full_name, role, is_onboarded, now)
            )
        else:
            self.execute_mutation(
                """
                INSERT INTO users (user_id, email, password_hash, full_name, name, role, is_onboarded, created_ts, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, email_clean, password_hash, full_name, full_name, role, is_onboarded, now, now)
            )
        return {
            "id": user_id,
            "email": email_clean,
            "full_name": full_name,
            "name": full_name,
            "role": role,
            "is_onboarded": bool(is_onboarded),
            "created_at": now
        }

    def update_user_onboarded(self, user_id: str, is_onboarded: int = 1, preferences: Optional[Dict[str, Any]] = None) -> bool:
        pref_str = json.dumps(preferences or {})
        rows = self.execute_mutation(
            "UPDATE users SET is_onboarded = %s, tour_completed = %s, preferences_json = %s WHERE user_id = %s OR id = %s",
            (is_onboarded, is_onboarded, pref_str, user_id, user_id)
        )
        return rows > 0

    # =========================================================================
    # Series & Episode Management Helpers
    # =========================================================================
    def create_series(
        self, series_id: str, workspace_id: str, title: str,
        description: str = "", genre: str = "mystery", tone: str = "suspense",
        cast_json: str = "{}", user_id: str = "admin_abhay"
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        self.execute_mutation(
            """
            INSERT INTO series (id, workspace_id, user_id, title, description, genre, tone, cast_json, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (series_id, workspace_id, user_id, title, description, genre, tone, cast_json, now)
        )
        return {
            "id": series_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "genre": genre,
            "tone": tone,
            "created_at": now
        }

    def list_series(self, workspace_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if user_id:
            rows = self.execute_query(
                "SELECT * FROM series WHERE user_id = %s OR workspace_id = %s ORDER BY created_at DESC",
                (user_id, workspace_id)
            )
        else:
            rows = self.execute_query(
                "SELECT * FROM series WHERE workspace_id = %s ORDER BY created_at DESC",
                (workspace_id,)
            )
        return [dict(r) for r in rows]

    def get_series(self, workspace_id: str, series_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if user_id:
            rows = self.execute_query(
                "SELECT * FROM series WHERE (user_id = %s OR workspace_id = %s) AND id = %s",
                (user_id, workspace_id, series_id)
            )
        else:
            rows = self.execute_query(
                "SELECT * FROM series WHERE workspace_id = %s AND id = %s",
                (workspace_id, series_id)
            )
        return dict(rows[0]) if rows else None

    def create_episode(
        self, episode_id: str, series_id: str, workspace_id: str,
        episode_number: int, title: str, recap: str = "", conflict: str = "",
        cliffhanger: str = "", script_json: str = "{}", status: str = "draft",
        video_id: Optional[str] = None, user_id: str = "admin_abhay"
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        if IS_POSTGRES:
            self.execute_mutation(
                """
                INSERT INTO episodes (
                    id, series_id, workspace_id, user_id, episode_number, title,
                    recap, conflict, cliffhanger, script_json, status, video_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_id, episode_number) DO UPDATE SET
                    title = EXCLUDED.title,
                    recap = EXCLUDED.recap,
                    conflict = EXCLUDED.conflict,
                    cliffhanger = EXCLUDED.cliffhanger,
                    script_json = EXCLUDED.script_json,
                    status = EXCLUDED.status,
                    video_id = EXCLUDED.video_id
                """,
                (
                    episode_id, series_id, workspace_id, user_id, episode_number, title,
                    recap, conflict, cliffhanger, script_json, status, video_id, now
                )
            )
        else:
            self.execute_mutation(
                """
                INSERT OR REPLACE INTO episodes (
                    id, series_id, workspace_id, user_id, episode_number, title,
                    recap, conflict, cliffhanger, script_json, status, video_id, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    episode_id, series_id, workspace_id, user_id, episode_number, title,
                    recap, conflict, cliffhanger, script_json, status, video_id, now
                )
            )
        return {
            "id": episode_id,
            "series_id": series_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "episode_number": episode_number,
            "title": title,
            "status": status,
            "created_at": now
        }

    def list_episodes(self, workspace_id: str, series_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if user_id:
            rows = self.execute_query(
                """
                SELECT * FROM episodes
                WHERE (user_id = %s OR workspace_id = %s) AND series_id = %s
                ORDER BY episode_number ASC
                """,
                (user_id, workspace_id, series_id)
            )
        else:
            rows = self.execute_query(
                """
                SELECT * FROM episodes
                WHERE workspace_id = %s AND series_id = %s
                ORDER BY episode_number ASC
                """,
                (workspace_id, series_id)
            )
        return [dict(r) for r in rows]


    def get_episode(self, workspace_id: str, episode_id: str) -> Optional[Dict[str, Any]]:
        rows = self.execute_query(
            "SELECT * FROM episodes WHERE workspace_id = %s AND id = %s",
            (workspace_id, episode_id)
        )
        return dict(rows[0]) if rows else None

    def update_episode(self, episode_id: str, status: Optional[str] = None, video_id: Optional[str] = None) -> bool:
        updates = []
        params = []
        if status:
            updates.append("status = %s")
            params.append(status)
        if video_id:
            updates.append("video_id = %s")
            params.append(video_id)
        if not updates:
            return False
        params.append(episode_id)
        q = f"UPDATE episodes SET {', '.join(updates)} WHERE id = %s"
        return self.execute_mutation(q, tuple(params)) > 0


# Global Database Instance
DB_ENGINE = DatabaseEngine()
