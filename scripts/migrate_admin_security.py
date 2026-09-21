"""
scripts/migrate_admin_security.py — Safe, Non-Destructive Database Migration for Admin & Multi-User Security.

Invariants:
1. NEVER delete or reset existing data (362 videos, 33 series, 30 episodes).
2. Takes a timestamped backup of data/autopilot.db.
3. Upgrades plaintext admin password to cryptographic PBKDF2-HMAC-SHA256.
4. Ensures admin_abhay is assigned the 'admin' role and linked to ws_admin_abhay.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.security import hash_password


DB_PATH = ROOT / "data" / "autopilot.db"


def run_migration() -> bool:
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return False

    # 1. Take timestamped backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"autopilot.db.backup_{ts}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Safe backup created at: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # 2. Check admin user in users table
        admin_row = conn.execute(
            "SELECT * FROM users WHERE user_id = 'admin_abhay' OR email = 'abhay@autopilot.ai'"
        ).fetchone()

        target_pw = os.environ.get("ADMIN_PASSWORD", "admin_autopilot_2026")
        secure_pw_hash = hash_password(target_pw)

        if admin_row:
            current_hash = admin_row["password_hash"] or ""
            if not current_hash.startswith("pbkdf2_sha256$"):
                print(f"🔄 Upgrading admin password from legacy plaintext to PBKDF2-HMAC-SHA256...")
                conn.execute(
                    """
                    UPDATE users
                    SET password_hash = ?, role = 'admin', full_name = COALESCE(full_name, 'Abhay Maurya (Founder & Admin)'),
                        name = COALESCE(name, 'Abhay Maurya (Founder & Admin)')
                    WHERE id = ?
                    """,
                    (secure_pw_hash, admin_row["id"])
                )
                print("✅ Admin password securely hashed with PBKDF2.")
            else:
                print("ℹ️ Admin password already has valid PBKDF2 hash.")
        else:
            print("🔄 Creating admin account 'admin_abhay'...")
            conn.execute(
                """
                INSERT INTO users (user_id, email, password_hash, full_name, name, role, tier, credits, is_onboarded, created_ts)
                VALUES ('admin_abhay', 'abhay@autopilot.ai', ?, 'Abhay Maurya (Founder & Admin)', 'Abhay Maurya (Founder & Admin)', 'admin', 'enterprise', 10000, 1, ?)
                """,
                (secure_pw_hash, time.strftime("%Y-%m-%dT%H:%M:%SZ"))
            )
            print("✅ Admin user created.")

        # 3. Ensure admin workspaces exist
        admin_ws_id = "ws_admin_abhay"
        admin_org_id = "org_admin_abhay"

        conn.execute(
            """
            INSERT OR IGNORE INTO organizations (id, name, slug, billing_email)
            VALUES (?, 'Abhay Media Holdings', 'abhay-media', 'abhay@autopilot.ai')
            """,
            (admin_org_id,)
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO workspaces (id, organization_id, name, slug, owner_email, is_active)
            VALUES (?, ?, 'Admin Master Studio', 'admin-master-studio', 'abhay@autopilot.ai', 1)
            """,
            (admin_ws_id, admin_org_id)
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO workspaces (id, organization_id, name, slug, owner_email, is_active)
            VALUES ('ws_default_creator', ?, 'Admin Default Creator Studio', 'default-creator', 'abhay@autopilot.ai', 1)
            """,
            (admin_org_id,)
        )

        # 4. Ensure workspace_id column exists on videos and audit ownership
        video_cols = [col[1] for col in conn.execute("PRAGMA table_info(videos)").fetchall()]
        if "workspace_id" not in video_cols:
            print("🔄 Adding 'workspace_id' column to videos table...")
            conn.execute("ALTER TABLE videos ADD COLUMN workspace_id TEXT")
            conn.execute("UPDATE videos SET workspace_id = 'ws_admin_abhay' WHERE user_id = 'admin_abhay'")
            print("✅ 'workspace_id' column added and backfilled for admin videos.")

        v_count = conn.execute("SELECT COUNT(*) FROM videos WHERE user_id = 'admin_abhay'").fetchone()[0]
        total_v = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        print(f"✅ Video ownership audit: {v_count}/{total_v} videos owned by admin_abhay.")

        if v_count < total_v:
            conn.execute("UPDATE videos SET user_id = 'admin_abhay', workspace_id = 'ws_admin_abhay' WHERE user_id IS NULL OR user_id = ''")
            updated_count = conn.execute("SELECT COUNT(*) FROM videos WHERE user_id = 'admin_abhay'").fetchone()[0]
            print(f"✅ Reassigned unowned videos to admin_abhay: now {updated_count}/{total_v}.")

        conn.commit()
        print("🎉 Migration completed successfully with zero data loss!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
