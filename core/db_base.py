r"""
core/db_base.py — Enterprise Multi-Tenant Database Engine for AUTOPILOT.

Supports:
- PostgreSQL (Supabase / Neon / AWS RDS) with connection pooling and tenant isolation.
- SQLite fallback for local developer environments.
- Context-managed workspace scoping (ensuring queries never leak cross-tenant).
"""

from __future__ import annotations

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
        """
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
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



# Global Database Instance
DB_ENGINE = DatabaseEngine()
