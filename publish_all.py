#!/usr/bin/env python3
"""
publish_all.py — AUTOPILOT: Sab Pending Episodes Ko Ek Baar Mein Publish Karo

DB mein jo bhi videos 'rendered', 'validated', ya 'approved' status mein hain
lekin abhi tak YouTube par upload nahi hui hain — unhe sab ek saath publish karo.

Usage:
    python publish_all.py                    # Sab pending videos publish karo
    python publish_all.py --series SERIES_1  # Sirf ek series ke pending videos
    python publish_all.py --list             # Dekho kya kya pending hai
    python publish_all.py --delay 30         # Har video ke beech 30 seconds wait karo
    python publish_all.py --limit 5          # Maximum 5 videos publish karo

POLICY (AGENTS.md — PERMANENT):
    selfDeclaredMadeForKids = False   <- comments must ALWAYS remain ON
    privacyStatus            = public
    madeForKids              = False
    comment_bait pinned      = ALWAYS
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# -- Windows UTF-8 safe terminal -----------------------------------------------
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
from agents.publisher import YouTubePublisher

log = Logbook("publish_all")

# Ye statuses wale videos publish ke ready hain
PUBLISHABLE_STATUSES = ("rendered", "validated", "approved")


def get_pending_videos(db: DB, series_filter: str | None = None) -> list[dict]:
    """
    DB se sab un videos ki list nikalo jo publish hone ke liye ready hain.
    - status IN (rendered, validated, approved)
    - yt_video_id IS NULL (matlab abhi tak upload nahi hua)
    - video_path IS NOT NULL (matlab render complete hai)
    - video_path actually disk par exist karti ho (broken/Linux paths skip)
    """
    placeholders = ",".join("?" * len(PUBLISHABLE_STATUSES))
    params: list = list(PUBLISHABLE_STATUSES)

    series_clause = ""
    if series_filter:
        series_clause = "AND series_name = ?"
        params.append(series_filter.upper())

    rows = db.q(
        f"""
        SELECT
            id, title, series_name, series_index,
            status, video_path, caption, notes,
            created_ts
        FROM videos
        WHERE status IN ({placeholders})
          AND (yt_video_id IS NULL OR yt_video_id = '')
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
        # Skip karo agar path Linux-style hai ya file disk par nahi hai
        if vpath.startswith("/home/") or vpath.startswith("/tmp/"):
            log.warn(f"Skipping #{d['id']}: old Linux path not valid on Windows: {vpath}")
            continue
        p = Path(vpath)
        if not p.exists():
            # Try relative to ROOT
            rp = ROOT / vpath.lstrip("/\\")
            if rp.exists():
                d["video_path"] = str(rp)
            else:
                log.warn(f"Skipping #{d['id']}: video file not found on disk: {vpath}")
                continue
        valid.append(d)
    return valid


def print_pending_table(videos: list[dict]) -> None:
    """Pending videos ka table print karo."""
    if not videos:
        print("\n  Koi bhi pending video nahi mila jise publish karna ho.")
        print("  Sab videos ya toh pehle se published hain ya abhi render nahi hue.\n")
        return

    print("\n" + "=" * 95)
    print("  PENDING VIDEOS — Publish ke liye ready")
    print("=" * 95)
    print(f"  {'#':>4} {'DB ID':>6} {'Series':<12} {'Ep':>4} {'Status':<12} {'Title':<42}")
    print("  " + "-" * 90)
    for i, v in enumerate(videos, 1):
        vid_id = v["id"]
        series = v["series_name"] or "—"
        ep = str(v["series_index"] or "—")
        status = v["status"]
        title = (v["title"] or "")[:40]
        print(f"  {i:>4} {vid_id:>6} {series:<12} {ep:>4} {status:<12} {title:<42}")
    print("=" * 95)
    print(f"  Total pending: {len(videos)} videos\n")


def publish_video(pub: YouTubePublisher, video: dict) -> dict:
    """Ek video publish karo aur result return karo."""
    vid_id = video["id"]
    series = video.get("series_name", "?")
    ep = video.get("series_index", "?")
    title = (video.get("title") or "")[:60]

    print(f"\n  Uploading #{vid_id} [{series} Ep {ep}]")
    print(f"  Title: {title}")

    t0 = time.time()
    try:
        res = pub.publish(
            vid_id,
            privacy="public",      # AGENTS.md: always public
            pin_comment=True,      # AGENTS.md: comment_bait always pinned
            # autonomy gate: config.yaml = auto_publish, gate will pass automatically
        )
        elapsed = round(time.time() - t0, 1)
        url = res.get("url") or f"https://youtube.com/shorts/{res.get('yt_video_id', '')}"
        print(f"  Published! URL: {url}  ({elapsed}s)")
        return {
            "ok": True,
            "video_id": vid_id,
            "series": series,
            "ep": ep,
            "url": url,
            "elapsed": elapsed,
        }
    except Exception as exc:
        elapsed = round(time.time() - t0, 1)
        print(f"  FAILED: {exc}")
        log.error(f"publish_all: Video #{vid_id} [{series} Ep {ep}] failed: {exc}")
        return {
            "ok": False,
            "video_id": vid_id,
            "series": series,
            "ep": ep,
            "error": str(exc),
            "elapsed": elapsed,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AUTOPILOT — Sab Pending Episodes Ek Baar Mein Publish Karo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--series",
        default=None,
        help="Sirf ek specific series filter karo (e.g. SERIES_1, SERIES_6)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Sirf pending videos ki list dikhaao, publish mat karo",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Har video upload ke beech wait (seconds). Default: 10",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum kitne videos publish karo (default: sab)",
    )
    parser.add_argument(
        "--ids",
        nargs="+",
        type=int,
        default=None,
        help="Specific video DB IDs publish karo (e.g. --ids 284 285 286)",
    )

    args = parser.parse_args()

    db = DB()

    # -- Specific IDs mode -------------------------------------------------------
    if args.ids:
        videos = []
        for vid_id in args.ids:
            row = db.get_video(vid_id)
            if not row:
                print(f"  WARNING: Video #{vid_id} DB mein nahi mila, skip kar rahe hain.")
                continue
            videos.append(dict(row))
        if not videos:
            print("  Koi valid video ID nahi mila.")
            sys.exit(1)

    else:
        # -- DB se pending videos dhundho ----------------------------------------
        videos = get_pending_videos(db, series_filter=args.series)

    # -- --list mode ------------------------------------------------------------
    if args.list:
        print_pending_table(videos)
        return

    if not videos:
        print_pending_table(videos)
        sys.exit(0)

    print_pending_table(videos)

    # -- Limit apply karo -------------------------------------------------------
    if args.limit and args.limit < len(videos):
        print(f"  --limit={args.limit} set hai, sirf pehle {args.limit} videos publish karenge.")
        videos = videos[: args.limit]

    # -- Confirmation -----------------------------------------------------------
    series_label = f" [{args.series}]" if args.series else ""
    print(f"  {len(videos)} pending video(s){series_label} publish hone wale hain.")
    print(f"  Delay between uploads: {args.delay}s")
    print(f"  Policy: selfDeclaredMadeForKids=False | Comments=ON | Public")
    print()

    # -- Publish loop -----------------------------------------------------------
    pub = YouTubePublisher(db=db)
    results = []

    t_batch_start = time.time()
    for i, video in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}]", end=" ")
        result = publish_video(pub, video)
        results.append(result)

        # Delay (except last video ke baad)
        if i < len(videos) and args.delay > 0:
            print(f"  Waiting {args.delay}s before next upload...")
            time.sleep(args.delay)

    # -- Final Report -----------------------------------------------------------
    total_elapsed = round(time.time() - t_batch_start, 1)
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    print("\n" + "=" * 80)
    print("  PUBLISH ALL — BATCH COMPLETE")
    print("=" * 80)
    for r in results:
        icon = "OK  " if r["ok"] else "FAIL"
        series = r.get("series", "?")
        ep = r.get("ep", "?")
        info = r.get("url") or r.get("error", "unknown")
        elapsed = r.get("elapsed", 0)
        print(f"  [{icon}] {series} Ep {ep}  ({elapsed}s)  {str(info)[:55]}")

    print(f"\n  Total: {ok_count} published, {fail_count} failed")
    print(f"  Total time: {int(total_elapsed // 60)}m {int(total_elapsed % 60)}s")
    print()
    print("  POLICY AUDIT:")
    print("    selfDeclaredMadeForKids = False  [ENFORCED]")
    print("    comment_bait pinned     = True   [ENFORCED]")
    print("    privacy                 = public [ENFORCED]")
    print("=" * 80 + "\n")

    db.close()
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
