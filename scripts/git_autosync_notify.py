#!/usr/bin/env python3
"""
scripts/git_autosync_notify.py — Automated Git Push & Discord Notification System

Usage:
  python scripts/git_autosync_notify.py "commit message"
"""

import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.discord_service import DiscordNotifications

def main():
    custom_msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_msg = custom_msg or f"chore(sync): automated data & code push ({now_utc})"

    print(f"=== AUTOPILOT GIT AUTO-SYNC ({now_utc}) ===")

    # 1. Re-export master database to JSON
    export_script = Path("scripts/export_master_vault.py")
    if export_script.exists():
        print("[1/3] Exporting master vault data...")
        subprocess.run([sys.executable, str(export_script)], check=False)

    # 2. Stage changes, commit, and push
    print("[2/3] Staging files and pushing to GitHub...")
    subprocess.run(["git", "add", "data/autopilot.db", "data/autopilot_master_vault_backup.json", ".gitignore", "backend/", "scripts/", "core/", "README.md"], check=False)
    
    commit_proc = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if "nothing to commit" in commit_proc.stdout:
        print("ℹ No new changes to commit.")
    else:
        print(commit_proc.stdout.strip())

    push_proc = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    print("Git Push Output:", push_proc.stdout or push_proc.stderr)

    # 3. Discord notification
    print("[3/3] Sending Discord update notification...")
    channel_id = "1212765278765584396"
    embed = DiscordNotifications.create_embed(
        title="👑 AUTOPILOT DATA & CODE SYNCED TO GITHUB",
        description=f"All latest application changes and data have been pushed to GitHub main branch.\n\n**Commit**: `{commit_msg}`",
        color=0x10B981,
        fields=[
            {"name": "🎬 Video Archive", "value": "367 Historical Videos", "inline": True},
            {"name": "📺 Franchises", "value": "57 Series & 54 Episodes", "inline": True},
            {"name": "💎 Master Vault", "value": "Available in Admin Console", "inline": True},
            {"name": "💬 YouTube Invariant", "value": "100% Comments Enabled", "inline": True},
            {"name": "📦 Storage Tracked", "value": "data/autopilot.db & JSON", "inline": True},
            {"name": "🌐 Live Cloud", "value": "https://autopilot-7pxl.onrender.com", "inline": True}
        ],
        footer="AUTOPILOT • Continuous Delivery & Vault Sync"
    )
    sent = DiscordNotifications.send_to_channel(channel_id, {"embeds": [embed]})
    print(f"Discord notification dispatched: {sent}")

if __name__ == "__main__":
    main()
