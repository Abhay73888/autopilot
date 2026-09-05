#!/usr/bin/env python3
"""
authorize_youtube.py — YouTube se connect karne ke liye ek baar chalao.

    python authorize_youtube.py

Kya hoga:
  1. Browser khulega -> Google login -> Allow
  2. token.json ban jayega (ye hamesha ke liye kaam karta hai)
  3. Tumhare channel ka naam print hoga = connection confirm

Dobara chalane ki zaroorat nahi, jab tak:
  - token.json delete na kar do
  - Google account ka password na badlo
  - OAuth app 'Testing' mode mein ho (tab har 7 din baad token expire hota hai —
    isliye SETUP.md kehta hai ki app ko 'Production' mein publish kar do)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.oauth import OAuthError, api_request, authorize  # noqa: E402


def main() -> int:
    force = "--force" in sys.argv

    try:
        creds = authorize(force=force)
    except OAuthError as e:
        print(f"\n❌ Authorization fail hui:\n\n{e}\n")
        return 1
    except KeyboardInterrupt:
        print("\nCancel kar diya.")
        return 1

    # ---- verify: channel info kheencho ----
    st, data, _ = api_request(
        creds,
        "https://www.googleapis.com/youtube/v3/channels"
        "?part=snippet,contentDetails,statistics&mine=true")

    if st != 200:
        print(f"\n❌ Channel info nahi mili (HTTP {st}).")
        if st == 403:
            print("   → YouTube Data API v3 enable kiya hai? "
                  "console.cloud.google.com -> APIs & Services -> Library")
        print(f"   Response: {data}\n")
        return 1

    if not data.get("items"):
        print("\n❌ Is Google account pe koi YouTube channel nahi hai.")
        print("   → youtube.com pe jao aur pehle channel banao, phir dobara chalao.\n")
        return 1

    it = data["items"][0]
    sn, cd, stt = it["snippet"], it["contentDetails"], it.get("statistics", {})

    print("\n" + "=" * 62)
    print("  ✅ YOUTUBE CONNECTED")
    print("=" * 62)
    print(f"  Channel      : {sn['title']}")
    print(f"  Channel ID   : {it['id']}")
    print(f"  Subscribers  : {stt.get('subscriberCount', '?')}")
    print(f"  Videos       : {stt.get('videoCount', '?')}")
    print(f"  Uploads list : {cd['relatedPlaylists']['uploads']}")
    print("-" * 62)
    print("  💡 Uploads playlist ID yaad rakho — TrendScout isse apne videos")
    print("     ka data 1 unit mein padhega (search.list 100 units leta hai).")
    print("=" * 62)
    print("\n  Agla step — ek video private mein upload karo:")
    print("     python -m agents.publisher <video_id> --dry-run    # pehle dry run")
    print("     python -m agents.publisher <video_id>              # asli upload (private)\n")

    # .env mein channel id suggest karo
    env = Path(__file__).parent / ".env"
    if env.exists() and "YT_CHANNEL_ID=" in env.read_text(encoding="utf-8"):
        print(f"  💡 .env mein ye line update kar do:")
        print(f"     YT_CHANNEL_ID={it['id']}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
