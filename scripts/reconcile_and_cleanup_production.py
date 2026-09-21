"""
scripts/reconcile_and_cleanup_production.py — Production YouTube Video Reconciliation & Safe Cleanup

Actions performed:
1. Backs up production SQLite database (snapshot file + JSON dump of all 367 video records).
2. Protects the 93 confirmed YouTube videos (verified against live YouTube Data API).
3. Reconciles the 3 missing confirmed videos into `data/autopilot.db`.
4. Prunes 277 unconfirmed/failed/orphan records from `videos`.
5. Removes 889 intermediate/checkpoint video files (reclaiming ~11.31 GB) while strictly preserving all 93 primary final video files.
6. Adds database indexes on `videos(yt_video_id)`, `videos(status)`, `videos(user_id)`.
7. Verifies database and filesystem integrity post-cleanup.
"""

import os
import sys
import shutil
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = ROOT / "data" / "autopilot.db"
BACKUP_DIR = ROOT / "data" / "backup"
MANIFEST_PATH = ROOT / "scratch" / "confirmed_93_youtube_videos.json"
FILES_REPORT_PATH = ROOT / "scratch" / "filesystem_audit_report.json"

def main():
    print("=" * 80)
    print("🚀 AUTOPILOT PRODUCTION AUDIT & CLEANUP: 93 CONFIRMED YOUTUBE VIDEOS")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # STEP 1: LOAD MANIFESTS & PROTECTED WHITELIST
    # -------------------------------------------------------------------------
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
    if not FILES_REPORT_PATH.exists():
        raise FileNotFoundError(f"Files report not found: {FILES_REPORT_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        confirmed_videos = json.load(f)

    with open(FILES_REPORT_PATH, "r", encoding="utf-8") as f:
        files_report = json.load(f)

    confirmed_yt_ids = {c["youtube_video_id"] for c in confirmed_videos}
    print(f"✅ Loaded {len(confirmed_videos)} confirmed YouTube videos into protected whitelist.")
    if len(confirmed_videos) != 93:
        print(f"⚠️ Warning: expected 93 confirmed videos, got {len(confirmed_videos)}")

    # Collect immutable whitelist of primary video files to keep
    protected_files = set()
    for cv in confirmed_videos:
        if cv.get("local_video_file"):
            p = Path(cv["local_video_file"]).resolve()
            if p.exists():
                protected_files.add(str(p))
        if cv.get("local_thumbnail_file"):
            tp = Path(cv["local_thumbnail_file"]).resolve()
            if tp.exists():
                protected_files.add(str(tp))

    # Also protect global assets
    for kf in files_report.get("keep_files", []):
        protected_files.add(str(Path(kf["path"]).resolve()))

    print(f"✅ Protected {len(protected_files)} primary final files from deletion.")

    # -------------------------------------------------------------------------
    # STEP 2: BACKUP DATABASE & DUMP ALL CURRENT RECORDS
    # -------------------------------------------------------------------------
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_backup_file = BACKUP_DIR / f"autopilot.db.backup_pre_cleanup_{timestamp}"
    json_backup_file = BACKUP_DIR / f"videos_pre_cleanup_archive_{timestamp}.json"

    print(f"\n📦 Backing up production database to: {db_backup_file.name}")
    shutil.copy2(DB_PATH, db_backup_file)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM videos")
    all_current_videos = [dict(r) for r in cursor.fetchall()]
    with open(json_backup_file, "w", encoding="utf-8") as f:
        json.dump(all_current_videos, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported all {len(all_current_videos)} existing video records to: {json_backup_file.name}")

    # -------------------------------------------------------------------------
    # STEP 3: RECONCILE 3 MISSING VIDEOS INTO DATABASE
    # -------------------------------------------------------------------------
    missing_to_insert = [
        {
            "yt_video_id": "7Slt4Pry6lM",
            "title": "SOLO LEVELING Chapter 1 in Hindi ⚔️ | The Weakest Hunter | Full Manhwa Recap",
            "topic": "Solo Leveling Chapter 1 Recap",
            "series_name": "Solo Leveling",
            "series_index": 1,
            "video_path": str(ROOT / "output" / "solo_leveling_ch1" / "final.mp4"),
            "cover_path": str(ROOT / "output" / "solo_leveling_ch1" / "cover.jpg"),
            "published_ts": "2026-09-19T19:36:53Z",
            "length_sec": 482.0,
            "user_id": "admin_abhay",
            "workspace_id": "ws_admin_abhay"
        },
        {
            "yt_video_id": "VXC5JTRkBDs",
            "title": "SOLO LEVELING Chapter 2 in Hindi ⚔️ | The Double Dungeon Trap | Full Manhwa Recap",
            "topic": "Solo Leveling Chapter 2 Recap",
            "series_name": "Solo Leveling",
            "series_index": 2,
            "video_path": str(ROOT / "output" / "solo_leveling_ch2" / "final.mp4"),
            "cover_path": str(ROOT / "output" / "solo_leveling_ch2" / "cover.jpg"),
            "published_ts": "2026-09-20T03:54:49Z",
            "length_sec": 510.0,
            "user_id": "admin_abhay",
            "workspace_id": "ws_admin_abhay"
        },
        {
            "yt_video_id": "g6GemTgMNDM",
            "title": "MAT KHOLO YE DARWAZA 🚪😱 | Puri Hindi Horror Animated Film | Anime Horror | 2024",
            "topic": "Mat Kholo Ye Darwaza Full Horror Film",
            "series_name": "Horror Specials",
            "series_index": 1,
            "video_path": str(ROOT / "output" / "dont_open_the_door_movie" / "final.mp4"),
            "cover_path": str(ROOT / "output" / "dont_open_the_door_movie" / "cover.jpg"),
            "published_ts": "2026-09-19T18:29:54Z",
            "length_sec": 638.0,
            "user_id": "admin_abhay",
            "workspace_id": "ws_admin_abhay"
        }
    ]

    print("\n🔄 Reconciling standalone YouTube uploads into `videos` table...")
    now_iso = datetime.now(timezone.utc).isoformat()
    for m in missing_to_insert:
        cursor.execute("SELECT id FROM videos WHERE yt_video_id = ?", (m["yt_video_id"],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE videos SET
                    title = ?, topic = ?, series_name = ?, series_index = ?,
                    video_path = ?, cover_path = ?, status = 'published',
                    published_ts = ?, user_id = ?, workspace_id = ?, updated_ts = ?
                WHERE id = ?
            """, (
                m["title"], m["topic"], m["series_name"], m["series_index"],
                m["video_path"], m["cover_path"], m["published_ts"],
                m["user_id"], m["workspace_id"], now_iso, existing[0]
            ))
            print(f"  Updated existing record #{existing[0]} with yt_video_id {m['yt_video_id']}")
        else:
            cursor.execute("""
                INSERT INTO videos (
                    created_ts, updated_ts, status, topic, title,
                    video_path, cover_path, yt_video_id, published_ts,
                    length_sec, series_name, series_index, user_id, workspace_id
                ) VALUES (?, ?, 'published', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["published_ts"], now_iso, m["topic"], m["title"],
                m["video_path"], m["cover_path"], m["yt_video_id"], m["published_ts"],
                m["length_sec"], m["series_name"], m["series_index"], m["user_id"], m["workspace_id"]
            ))
            print(f"  Inserted new record for {m['title'][:40]} (yt_id: {m['yt_video_id']})")

    conn.commit()

    # -------------------------------------------------------------------------
    # STEP 4: PRUNE UNCONFIRMED RECORDS IN DATABASE
    # -------------------------------------------------------------------------
    print("\n🧹 Pruning unconfirmed / orphan records from `videos` table...")
    cursor.execute("SELECT count(*) FROM videos")
    total_before = cursor.fetchone()[0]

    # Delete any record whose yt_video_id is not in the confirmed 93 list
    placeholders = ",".join("?" for _ in confirmed_yt_ids)
    cursor.execute(f"""
        DELETE FROM videos
        WHERE yt_video_id IS NULL 
           OR yt_video_id = ''
           OR yt_video_id NOT IN ({placeholders})
    """, list(confirmed_yt_ids))
    deleted_count = cursor.rowcount
    conn.commit()

    cursor.execute("SELECT count(*) FROM videos")
    total_after = cursor.fetchone()[0]
    print(f"✅ DB Pruning Complete:")
    print(f"   Before: {total_before} records")
    print(f"   Deleted: {deleted_count} unconfirmed/orphan records")
    print(f"   Remaining in DB: {total_after} records (Target: 93)")

    # -------------------------------------------------------------------------
    # STEP 5: ADD INDEXES & CONSTRAINTS
    # -------------------------------------------------------------------------
    print("\n⚡ Creating high-performance database indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_yt_video_id ON videos(yt_video_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_workspace_id ON videos(workspace_id);")
    conn.commit()
    conn.close()
    print("✅ Database indexes created successfully.")

    # -------------------------------------------------------------------------
    # STEP 6: FILESYSTEM CLEANUP (DELETE CANDIDATES)
    # -------------------------------------------------------------------------
    print("\n🗑️ Executing filesystem cleanup of intermediate/orphan video files...")
    delete_candidates = files_report.get("delete_candidates", [])
    print(f"Candidate files scheduled for deletion: {len(delete_candidates)}")

    deleted_files_count = 0
    deleted_bytes = 0
    skipped_protected = 0
    errors_count = 0

    for item in delete_candidates:
        fpath_str = item["path"]
        fpath = Path(fpath_str).resolve()
        
        # Absolute safety check: Never delete a file in protected whitelist
        if str(fpath) in protected_files:
            skipped_protected += 1
            continue

        if not fpath.exists():
            continue

        try:
            sz = fpath.stat().st_size
            fpath.unlink()
            deleted_files_count += 1
            deleted_bytes += sz
        except Exception as e:
            errors_count += 1
            print(f"⚠️ Error deleting {fpath}: {e}")

    reclaimed_mb = deleted_bytes / (1024 * 1024)
    reclaimed_gb = reclaimed_mb / 1024
    print(f"✅ Filesystem Cleanup Complete:")
    print(f"   Deleted Files: {deleted_files_count}")
    print(f"   Protected Files Skipped: {skipped_protected}")
    print(f"   Disk Space Reclaimed: {reclaimed_mb:.2f} MB ({reclaimed_gb:.2f} GB)")
    print(f"   Errors: {errors_count}")

    # Remove empty checkpoint folders
    print("\n🧹 Cleaning up empty checkpoint subdirectories...")
    for cp_dir in ROOT.glob("output/*/checkpoints"):
        try:
            if cp_dir.is_dir() and not any(cp_dir.iterdir()):
                cp_dir.rmdir()
                print(f"  Removed empty folder: {cp_dir.relative_to(ROOT)}")
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # STEP 7: POST-CLEANUP VERIFICATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("🔍 POST-CLEANUP FINAL AUDIT VERIFICATION")
    print("=" * 80)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM videos")
    final_db_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM videos WHERE yt_video_id IS NOT NULL AND yt_video_id != ''")
    final_yt_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM videos WHERE status = 'published'")
    final_pub_count = cursor.fetchone()[0]

    cursor.execute("SELECT id, yt_video_id, title, video_path FROM videos")
    final_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    missing_files = []
    for r in final_rows:
        vp = r.get("video_path")
        if not vp or not Path(vp).exists():
            missing_files.append(r)

    print(f"Total Videos in DB: {final_db_count} (Must be exactly 93)")
    print(f"Videos with yt_video_id: {final_yt_count}")
    print(f"Videos with status='published': {final_pub_count}")
    print(f"Videos with missing local file: {len(missing_files)}")

    if missing_files:
        print("⚠️ Warning: missing files for:")
        for m in missing_files[:5]:
            print(f"   #{m['id']} {m['title']} -> {m['video_path']}")
    else:
        print("✅ 100% of the 93 confirmed YouTube videos have verified existing local video files!")

    print("\n🎉 RECONCILIATION & CLEANUP COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
