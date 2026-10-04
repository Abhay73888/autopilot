r"""
core/platform_schema.py — Idempotent Platform Schema Migrations for AUTOPILOT

Adds:
- users.status, users.last_active_ts, users.block_reason, users.blocked_at, users.blocked_by
Creates:
- activity_log
- audit_log
- notifications

Idempotent: safe to run repeatedly without data duplication or loss.
"""

from __future__ import annotations

import sqlite3
from typing import Any, List, Optional
from core.db_base import DB_ENGINE, IS_POSTGRES
from core.logbook import Logbook

log = Logbook("platform_schema")


def ensure_platform_schema(db_engine=None) -> bool:
    """
    Applies idempotent platform schema migrations.
    Safely adds missing columns to users and ensures activity_log,
    audit_log, and notifications tables exist with appropriate indexes.
    """
    engine = db_engine or DB_ENGINE

    try:
        with engine.get_connection() as conn:
            if IS_POSTGRES:
                _migrate_postgres(conn)
            else:
                _migrate_sqlite(conn)
        log.info("Platform schema migrations applied successfully.")
        return True
    except Exception as e:
        log.error("Failed to apply platform schema migrations", error=str(e))
        raise


def _migrate_sqlite(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # 1. Check existing columns in users table
    cur.execute("PRAGMA table_info(users);")
    existing_cols = {row[1]: row for row in cur.fetchall()}

    columns_to_add = [
        ("status", "TEXT DEFAULT 'active'"),
        ("last_active_ts", "TEXT"),
        ("block_reason", "TEXT"),
        ("blocked_at", "TEXT"),
        ("blocked_by", "TEXT"),
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};")
                log.info(f"Added column users.{col_name}")
            except sqlite3.OperationalError as e:
                # Column might already exist in rare race conditions
                if "duplicate column" not in str(e).lower():
                    raise

    # Ensure any preexisting user has status='active' if NULL
    cur.execute("UPDATE users SET status = 'active' WHERE status IS NULL OR status = '';")

    # 2. Activity Log Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        actor_id TEXT,
        action TEXT NOT NULL,
        resource_type TEXT,
        resource_id TEXT,
        details_json TEXT DEFAULT '{}',
        ip_address TEXT,
        user_agent TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_actor ON activity_log(actor_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at);")

    # 3. Audit Log Table (Admin modifications only)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id TEXT PRIMARY KEY,
        admin_id TEXT NOT NULL,
        target_id TEXT,
        action TEXT NOT NULL,
        resource TEXT NOT NULL,
        before_json TEXT DEFAULT '{}',
        after_json TEXT DEFAULT '{}',
        reason TEXT,
        ip_address TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_log(admin_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);")

    # 4. Notifications Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        link TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notif_unread ON notifications(user_id, is_read);")


def _migrate_postgres(conn) -> None:
    with conn.cursor() as cur:
        # 1. Ensure user columns in PostgreSQL
        columns_to_add = [
            ("status", "VARCHAR(32) DEFAULT 'active'"),
            ("last_active_ts", "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP"),
            ("block_reason", "TEXT"),
            ("blocked_at", "TIMESTAMPTZ"),
            ("blocked_by", "VARCHAR(64)"),
        ]

        for col_name, col_def in columns_to_add:
            cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def};")

        cur.execute("UPDATE users SET status = 'active' WHERE status IS NULL OR status = '';")

        # 2. Activity Log Table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id VARCHAR(64) PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            actor_id VARCHAR(64),
            action VARCHAR(128) NOT NULL,
            resource_type VARCHAR(64),
            resource_id VARCHAR(128),
            details_json TEXT DEFAULT '{}',
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_activity_actor ON activity_log(actor_id);
        CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action);
        CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at);
        """)

        # 3. Audit Log Table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id VARCHAR(64) PRIMARY KEY,
            admin_id VARCHAR(64) NOT NULL,
            target_id VARCHAR(64),
            action VARCHAR(128) NOT NULL,
            resource VARCHAR(64) NOT NULL,
            before_json TEXT DEFAULT '{}',
            after_json TEXT DEFAULT '{}',
            reason TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_log(admin_id);
        CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id);
        CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);
        """)

        # 4. Notifications Table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id VARCHAR(64) PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR(32) DEFAULT 'info',
            is_read INT DEFAULT 0,
            link TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notif_unread ON notifications(user_id, is_read);
        """)
