#!/usr/bin/env python3
"""
next_ep.py — AUTOPILOT: Next Episode Auto-Generator CLI

Usage:
    python next_ep.py                         # All series ka next episode generate karo
    python next_ep.py SERIES_1                # Sirf Series 1 (Kaal-Rekha) ka next episode
    python next_ep.py SERIES_6                # Sirf Series 6 (Observer Files) ka next episode
    python next_ep.py SERIES_1 --ep 15        # Force karo specific episode number
    python next_ep.py --list                  # Dekho sab series ka current status
    python next_ep.py SERIES_1 --dry-run      # Sirf dekhna hai, publish mat karo

POLICY (AGENTS.md — PERMANENT):
    selfDeclaredMadeForKids = False   <- comments must ALWAYS remain ON
    privacyStatus            = public
    madeForKids              = False
    comment_bait pinned      = ALWAYS
"""

from __future__ import annotations

import argparse
import re
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

from core.config import CONFIG
from core.db import DB
from core.logbook import Logbook

log = Logbook("next_ep_cli")

# -- Series Registry ------------------------------------------------------------
# Har series ka naam, DB mein store kiya gaya series_name, aur iska runner module
SERIES_REGISTRY = {
    "SERIES_1": {
        "name": "Kaal-Rekha",
        "db_series_name": "SERIES_1",
        "language": "Hindi",
        "genre": "Anime Time-Loop Thriller",
    },
    "SERIES_2": {
        "name": "Jab Pyaar Online Tha",
        "db_series_name": "SERIES_2",
        "language": "Hindi",
        "genre": "Romantic Drama",
    },
    "SERIES_3": {
        "name": "Chintu Ki Jadui Duniya",
        "db_series_name": "SERIES_3",
        "language": "Hindi",
        "genre": "Kids Adventure",
    },
    "SERIES_4": {
        "name": "Dimag Ka Dahi",
        "db_series_name": "SERIES_4",
        "language": "Hindi",
        "genre": "Mind-Bending Riddles",
    },
    "SERIES_5": {
        "name": "Ashwatthama 3049 AD",
        "db_series_name": "SERIES_5",
        "language": "Hindi/English",
        "genre": "Sci-Fi Action",
    },
    "SERIES_6": {
        "name": "The Observer Files",
        "db_series_name": "SERIES_6",
        "language": "English",
        "genre": "Analog Horror Thriller",
    },
    "SERIES_7": {
        "name": "Roblox Vault",
        "db_series_name": "SERIES_7",
        "language": "English",
        "genre": "Gaming Content",
    },
}


def get_series_status(db: DB) -> dict[str, dict]:
    """
    DB se har series ka last published/rendered episode detect karo.
    Returns: { "SERIES_1": {"last_ep": 12, "last_title": "...", "next_ep": 13}, ... }
    """
    status = {}
    for series_code, meta in SERIES_REGISTRY.items():
        rows = db.q(
            """
            SELECT id, title, series_index, status, created_ts
            FROM videos
            WHERE series_name = ?
            ORDER BY id DESC
            LIMIT 20
            """,
            (series_code,),
        )

        max_ep = 0
        last_title = None
        last_status = None

        for r in rows:
            # series_index se episode number lo
            ep_from_index = r["series_index"] or 0

            # title se bhi try karo (fallback)
            ep_from_title = 0
            title_text = r["title"] or ""
            m = re.search(r'(?:Part|Episode|Ep)\s*(\d+)', title_text, re.IGNORECASE)
            if m:
                ep_from_title = int(m.group(1))

            ep_num = max(ep_from_index, ep_from_title)

            if ep_num > max_ep:
                max_ep = ep_num
                last_title = r["title"]
                last_status = r["status"]

        status[series_code] = {
            "series_name": meta["name"],
            "last_ep": max_ep,
            "last_title": last_title,
            "last_status": last_status,
            "next_ep": max_ep + 1 if max_ep > 0 else 1,
        }

    return status


def print_status_table(status: dict) -> None:
    """Pretty table print karo series status ka."""
    print("\n" + "=" * 90)
    print("  AUTOPILOT SERIES STATUS -- Current Episodes")
    print("=" * 90)
    print(f"  {'Series Code':<12} {'Series Name':<28} {'Last Ep':>8} {'Status':<14} {'Next Ep':>8}")
    print("  " + "-" * 86)
    for code, s in status.items():
        last = str(s["last_ep"]) if s["last_ep"] > 0 else "None"
        nxt = str(s["next_ep"])
        st = s["last_status"] or "not started"
        name = s["series_name"]
        print(f"  {code:<12} {name:<28} {last:>8} {st:<14} {nxt:>8}")
    print("=" * 90 + "\n")


def run_next_episode(
    series_code: str,
    episode_num: int | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Ek series ka next episode generate aur publish karo.
    Returns result dict with ok, video_id, title, url
    """
    from series.series_runner import generate_series_episode

    meta = SERIES_REGISTRY.get(series_code)
    if not meta:
        return {"ok": False, "msg": f"Unknown series code: {series_code}"}

    db = DB()

    if episode_num is None:
        status = get_series_status(db)
        episode_num = status[series_code]["next_ep"]

    print("\n" + "=" * 80)
    print(f"  GENERATING NEXT EPISODE")
    print(f"  Series  : {meta['name']} ({series_code})")
    print(f"  Episode : #{episode_num}")
    print(f"  Language: {meta['language']}")
    print(f"  Genre   : {meta['genre']}")
    print(f"  Policy  : selfDeclaredMadeForKids=False | Comments=ON | Public")
    if dry_run:
        print(f"  DRY RUN : Video will be rendered but NOT uploaded to YouTube")
    print("=" * 80)

    t0 = time.time()

    try:
        result = generate_series_episode(
            series_code=series_code,
            episode_num=episode_num,
            dry_run=dry_run,
        )
    except Exception as exc:
        log.error(f"[{series_code} Ep {episode_num}] Generation failed: {exc}")
        return {
            "ok": False,
            "series_code": series_code,
            "episode_num": episode_num,
            "msg": str(exc),
        }

    elapsed = time.time() - t0
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    if result.get("ok"):
        yt_url = result.get("url", "")
        vid = result.get("video_id", "?")
        title = result.get("title", "")
        print("\n" + "=" * 80)
        print(f"  SUCCESS! [{series_code} Ep {episode_num}] PUBLISHED!")
        print(f"  Title    : {title}")
        print(f"  URL      : {yt_url}")
        print(f"  Video ID : #{vid}")
        print(f"  Time     : {mins}m {secs}s")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print(f"  FAILED! [{series_code} Ep {episode_num}]")
        print(f"  Error: {result.get('msg', 'Unknown error')}")
        print("=" * 80 + "\n")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AUTOPILOT Next Episode Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "series",
        nargs="?",
        help=(
            "Series code (e.g. SERIES_1, SERIES_6). "
            "Agar nahi diya toh status table dikhega."
        ),
    )
    parser.add_argument(
        "--ep",
        type=int,
        default=None,
        help="Force karo specific episode number (default: DB se auto-detect)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Sirf status table dikhaao, kuch generate mat karo",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Video render karo lekin YouTube par upload mat karo",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sab registered series ka next episode generate karo",
    )

    args = parser.parse_args()

    db = DB()
    status = get_series_status(db)

    # -- --list mode ------------------------------------------------------------
    if args.list:
        print_status_table(status)
        return

    # -- Single series mode -----------------------------------------------------
    if args.series:
        series_code = args.series.upper().strip()
        if series_code not in SERIES_REGISTRY:
            print(f"\nERROR: Unknown series '{series_code}'")
            print(f"   Valid options: {', '.join(SERIES_REGISTRY.keys())}")
            sys.exit(1)

        s = status[series_code]
        print(
            f"\n  {series_code} | Last published: Ep {s['last_ep'] or 'None'} "
            f"| Generating: Ep {args.ep or s['next_ep']}"
        )

        result = run_next_episode(
            series_code=series_code,
            episode_num=args.ep,  # None = auto-detect
            dry_run=args.dry_run,
        )
        sys.exit(0 if result.get("ok") else 1)

    # -- --all mode: sab series -------------------------------------------------
    if args.all:
        print_status_table(status)
        results = []
        for code in SERIES_REGISTRY:
            r = run_next_episode(
                series_code=code,
                episode_num=None,
                dry_run=args.dry_run,
            )
            results.append((code, r))
            # Consecutive generation ke beech thoda pause
            if not args.dry_run:
                time.sleep(5)

        # Final summary
        print("\n" + "=" * 80)
        print("  BATCH GENERATION SUMMARY")
        print("=" * 80)
        ok_count = sum(1 for _, r in results if r.get("ok"))
        fail_count = len(results) - ok_count
        for code, r in results:
            icon = "OK" if r.get("ok") else "FAIL"
            ep = r.get("episode_num", "?")
            url = r.get("url", r.get("msg", "---"))[:60]
            print(f"  [{icon}] {code} Ep #{ep} -- {url}")
        print(f"\n  Total: {ok_count} success, {fail_count} failed")
        print("=" * 80 + "\n")
        sys.exit(0 if fail_count == 0 else 1)

    # -- No arguments: help + status -------------------------------------------
    print_status_table(status)
    print("USAGE:")
    print("   python next_ep.py SERIES_1              # Kaal-Rekha ka next ep generate karo")
    print("   python next_ep.py SERIES_6              # Observer Files ka next ep generate karo")
    print("   python next_ep.py SERIES_1 --ep 15      # Specific episode force karo")
    print("   python next_ep.py --all                 # Sab series ka next ep generate karo")
    print("   python next_ep.py --list                # Sirf status dekho")
    print("   python next_ep.py SERIES_1 --dry-run    # Render karo lekin upload mat karo")
    print()


if __name__ == "__main__":
    main()
