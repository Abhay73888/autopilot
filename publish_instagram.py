#!/usr/bin/env python3
r"""
publish_instagram.py — AUTOPILOT: Instagram Reels Publishing Automation Engine.

Publishes rendered/validated/approved/published videos to Instagram as Reels
via the Meta Graph API v21.0 3-step publishing protocol:
  1. POST /{ig_user_id}/media (create container with public video URL)
  2. Poll /{container_id} until status is FINISHED
  3. POST /{ig_user_id}/media_publish (publish Reel)
  4. Post transformative first-comment / comment_bait (engagement drive)

Usage:
    python publish_instagram.py                   # Publish all pending eligible Reels
    python publish_instagram.py --list            # Inspect videos pending Instagram publish
    python publish_instagram.py --ids 1000056     # Publish specific video ID(s)
    python publish_instagram.py --series LEONARDO # Publish pending videos of a series
    python publish_instagram.py --limit 3         # Limit number of posts
    python publish_instagram.py --delay 30        # Wait 30s between posts (rate limit safety)
    python publish_instagram.py --dry-run         # Dry-run validation & simulation
    python publish_instagram.py --info            # Check Instagram Business Account profile
    python publish_instagram.py --limit-check     # Inspect Meta 24h publishing quota
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# -- Windows UTF-8 terminal configuration -------------------------------------
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.db import DB
from core.logbook import Logbook
from agents.ig_publisher import InstagramPublisher, IGError, IG_MAX_SEC

log = Logbook("publish_instagram")

# Eligible statuses for Instagram Reels
ELIGIBLE_STATUSES = ("rendered", "validated", "approved", "published")


def get_pending_instagram_videos(db: DB, series_filter: str | None = None) -> list[dict]:
    """
    Retrieves videos from SQLite DB ready for Instagram publication:
    - status IN ('rendered', 'validated', 'approved', 'published')
    - ig_media_id IS NULL OR ig_media_id = ''
    - video_path is present and file exists on disk
    - length_sec <= 90s (Instagram API hard constraint)
    """
    placeholders = ",".join("?" * len(ELIGIBLE_STATUSES))
    params: list = list(ELIGIBLE_STATUSES)

    series_clause = ""
    if series_filter:
        series_clause = "AND series_name = ?"
        params.append(series_filter.upper())

    rows = db.q(
        f"""
        SELECT
            id, title, series_name, series_index,
            status, video_path, length_sec, caption,
            hashtags, script_json, public_url, created_ts
        FROM videos
        WHERE status IN ({placeholders})
          AND (ig_media_id IS NULL OR ig_media_id = '')
          AND video_path IS NOT NULL
          {series_clause}
        ORDER BY series_name, series_index, id
        """,
        params,
    )

    valid = []
    for r in rows:
        d = dict(r)
        vpath = d.get("video_path", "") or ""

        # Ignore legacy broken Linux paths on Windows
        if vpath.startswith("/home/") or vpath.startswith("/tmp/"):
            log.warn(f"Skipping #{d['id']}: incompatible path on Windows: {vpath}")
            continue

        p = Path(vpath)
        if not p.exists():
            rp = ROOT / vpath.lstrip("/\\")
            if rp.exists():
                d["video_path"] = str(rp)
            else:
                log.warn(f"Skipping #{d['id']}: video file missing on disk: {vpath}")
                continue

        # Check duration constraint
        dur = float(d.get("length_sec") or 0.0)
        if dur > IG_MAX_SEC:
            log.debug(f"Skipping #{d['id']}: duration {dur:.1f}s exceeds Instagram API limit ({IG_MAX_SEC}s)")
            continue

        valid.append(d)

    return valid


def print_pending_table(videos: list[dict]):
    """Prints a structured table of pending Instagram Reels."""
    print("\n" + "=" * 90)
    print(f"  INSTAGRAM REELS PENDING QUEUE — {len(videos)} video(s) eligible")
    print("=" * 90)
    if not videos:
        print("  Koi video pending nahi hai jo Instagram ke liye ready ho.")
        print("  (Notes: Reels must have duration <= 90s, existing file, and ig_media_id is null)")
        print("=" * 90 + "\n")
        return

    print(f"  {'ID':<9} {'SERIES':<18} {'EP':<5} {'DUR':<7} {'STATUS':<11} {'TITLE'}")
    print("  " + "-" * 86)
    for v in videos:
        sid = f"#{v['id']}"
        series = str(v.get("series_name") or "-")[:16]
        ep = str(v.get("series_index") or "-")[:4]
        dur_val = float(v.get("length_sec") or 0.0)
        dur = f"{dur_val:.1f}s"
        status = str(v.get("status") or "")[:10]
        title = str(v.get("title") or "")[:35]
        print(f"  {sid:<9} {series:<18} {ep:<5} {dur:<7} {status:<11} {title}")
    print("=" * 90 + "\n")


def publish_single_reel(publisher: InstagramPublisher, video: dict) -> dict:
    """Publishes a single video to Instagram Reels."""
    vid_id = video["id"]
    series = video.get("series_name", "?")
    ep = video.get("series_index", "?")
    title = video.get("title", "")
    t0 = time.time()

    print(f"\n🚀 Publishing #{vid_id} [{series} Ep {ep}] to Instagram...")
    try:
        res = publisher.publish(vid_id)
        elapsed = round(time.time() - t0, 1)

        if res.get("status") in ("published", "dry_run"):
            ig_id = res.get("ig_media_id") or "DRY_RUN_ID"
            permalink = res.get("permalink") or "(dry-run)"
            print(f"  ✅ SUCCESS: {title[:55]} ({elapsed}s)")
            print(f"     IG Media ID : {ig_id}")
            print(f"     Permalink   : {permalink}")
            return {
                "ok": True,
                "id": vid_id,
                "series": series,
                "ep": ep,
                "title": title,
                "ig_media_id": ig_id,
                "permalink": permalink,
                "elapsed": elapsed,
            }
        else:
            reason = res.get("reason", "unknown")
            print(f"  ⚠️ DEFERRED / QUEUED: {reason}")
            return {
                "ok": False,
                "id": vid_id,
                "series": series,
                "ep": ep,
                "title": title,
                "error": reason,
                "elapsed": elapsed,
            }

    except IGError as e:
        elapsed = round(time.time() - t0, 1)
        print(f"  ❌ FAILED: {str(e)[:250]}")
        return {
            "ok": False,
            "id": vid_id,
            "series": series,
            "ep": ep,
            "title": title,
            "error": str(e),
            "elapsed": elapsed,
        }
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        print(f"  ❌ UNEXPECTED ERROR: {e}")
        return {
            "ok": False,
            "id": vid_id,
            "series": series,
            "ep": ep,
            "title": title,
            "error": str(e),
            "elapsed": elapsed,
        }


def main():
    parser = argparse.ArgumentParser(
        description="AUTOPILOT — Instagram Reels Publishing Automation Engine"
    )
    parser.add_argument("--list", action="store_true", help="List all pending videos ready for Instagram")
    parser.add_argument("--dry-run", action="store_true", help="Simulate publishing without calling Instagram API")
    parser.add_argument("--info", action="store_true", help="Display connected Instagram account details")
    parser.add_argument("--limit-check", action="store_true", help="Inspect Meta 24h content publishing limits")
    parser.add_argument("--host-only", action="store_true", help="Only upload video to public hosting and print URL")
    parser.add_argument("--series", type=str, default=None, help="Filter by series name (e.g. --series LEONARDO)")
    parser.add_argument("--ids", nargs="+", type=int, default=None, help="Publish specific video DB IDs")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of reels to publish")
    parser.add_argument("--delay", type=int, default=30, help="Delay between consecutive uploads in seconds (default: 30)")

    args = parser.parse_args()
    db = DB()

    # -- Mode: Account Info ---------------------------------------------------
    if args.info:
        ig = InstagramPublisher(db=db, dry_run=args.dry_run)
        try:
            info = ig.account_info()
            print("\n" + "=" * 60)
            print("  INSTAGRAM ACCOUNT PROFILE")
            print("=" * 60)
            print(json.dumps(info, indent=2, ensure_ascii=False))
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error fetching account info: {e}\n")
            sys.exit(1)
        return

    # -- Mode: Publishing Limit Check -----------------------------------------
    if args.limit_check:
        ig = InstagramPublisher(db=db, dry_run=args.dry_run)
        try:
            limit_data = ig.publishing_limit()
            print("\n" + "=" * 60)
            print("  META 24-HOUR PUBLISHING LIMIT REPORT")
            print("=" * 60)
            print(json.dumps(limit_data, indent=2, ensure_ascii=False))
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error checking publishing limits: {e}\n")
            sys.exit(1)
        return

    # -- Mode: Host Only ------------------------------------------------------
    if args.host_only:
        if not args.ids:
            print("Error: --host-only requires --ids <video_id>")
            sys.exit(1)
        from core.hosting import upload as host_upload
        for vid_id in args.ids:
            row = db.get_video(vid_id)
            if not row:
                print(f"Video #{vid_id} not found in DB")
                continue
            path = Path(row["video_path"] or "")
            if not path.exists():
                print(f"Video file missing: {path}")
                continue
            print(f"Uploading #{vid_id} ({path.name}) to public host...")
            url = host_upload(path)
            db.update_video(vid_id, public_url=url)
            print(f"Public URL: {url}")
        return

    # -- Resolve videos to publish --------------------------------------------
    if args.ids:
        videos = []
        for vid_id in args.ids:
            row = db.get_video(vid_id)
            if not row:
                print(f"  WARNING: Video #{vid_id} DB mein nahi mila, skip kar rahe hain.")
                continue
            d = dict(row)
            p = Path(d.get("video_path") or "")
            if not p.exists():
                print(f"  WARNING: Video file #{vid_id} disk par nahi hai: {p}")
                continue
            dur = d.get("length_sec") or 0.0
            if dur > IG_MAX_SEC:
                print(f"  WARNING: Video #{vid_id} duration ({dur:.1f}s) > {IG_MAX_SEC}s, IG reject karega.")
                continue
            videos.append(d)
        if not videos:
            print("  Koi valid video nahi mila.")
            sys.exit(1)
    else:
        videos = get_pending_instagram_videos(db, series_filter=args.series)

    # -- List Mode ------------------------------------------------------------
    if args.list:
        print_pending_table(videos)
        return

    if not videos:
        print_pending_table(videos)
        sys.exit(0)

    print_pending_table(videos)

    if args.limit and args.limit < len(videos):
        print(f"  --limit={args.limit} set hai, sirf pehle {args.limit} reels publish karenge.")
        videos = videos[: args.limit]

    # -- Confirmation / Summary -----------------------------------------------
    dry_tag = " [DRY-RUN SIMULATION]" if args.dry_run else ""
    series_label = f" [{args.series}]" if args.series else ""
    print(f"  {len(videos)} reel(s){series_label} publish hone wale hain{dry_tag}.")
    print(f"  Delay between uploads: {args.delay}s")
    print(f"  Protocol: 3-Step Meta Container -> Poll -> Publish -> Comment Bait")
    print(f"  Policy: Max duration <= {IG_MAX_SEC}s | Comments ON | High engagement")
    print()

    pub = InstagramPublisher(db=db, dry_run=args.dry_run)
    results = []
    t_batch_start = time.time()

    for i, video in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}]", end=" ")
        res = publish_single_reel(pub, video)
        results.append(res)

        if i < len(videos) and args.delay > 0 and not args.dry_run:
            print(f"  Waiting {args.delay}s before next upload...")
            time.sleep(args.delay)

    # -- Batch Completion Report ----------------------------------------------
    total_elapsed = round(time.time() - t_batch_start, 1)
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    print("\n" + "=" * 80)
    print("  INSTAGRAM PUBLISHING — BATCH COMPLETE")
    print("=" * 80)
    for r in results:
        icon = "OK  " if r["ok"] else "FAIL"
        series = r.get("series", "?")
        ep = r.get("ep", "?")
        info = r.get("permalink") or r.get("error", "unknown")
        elapsed = r.get("elapsed", 0)
        print(f"  [{icon}] {series} Ep {ep}  ({elapsed}s)  {str(info)[:55]}")

    print(f"\n  Total: {ok_count} published, {fail_count} failed")
    print(f"  Total time: {int(total_elapsed // 60)}m {int(total_elapsed % 60)}s")
    print("=" * 80 + "\n")

    db.close()
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
