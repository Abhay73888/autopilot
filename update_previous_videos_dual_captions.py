#!/usr/bin/env python3
"""
update_previous_videos_dual_captions.py — Upload English and Hindi Closed Captions (CC)
to the recently published YouTube Shorts:
1. Video #234 (W1nCjlXOItE) — Series 2 Ep 6 (Jab Pyaar Online Tha)
2. Video #235 (cWNlv-WIb7c) — Series 3 Ep 4 (Chintu Ki Jadui Kahani)
3. Video #236 (CUDgNziz-wk) — Series 4 Ep 4 (Dimag Ka Dahi)
Enables the 1-Tap "CC" multi-language language switcher on screen for all viewers.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.oauth import authorize
from core.logbook import Logbook

log = Logbook("update_captions")

VIDEOS = [
    {
        "id": 234,
        "yt_id": "W1nCjlXOItE",
        "title": "Series 2 Ep 6: Terminal 3 Airport Climax",
        "srt_en": """1
00:00:00,000 --> 00:00:05,500
The departures board flashed in red: Flight BA-142 to London... Last Call For Boarding!

2
00:00:05,500 --> 00:00:11,500
Breathless and drenched in the rain, my eyes desperately searched the crowd for Meera.

3
00:00:11,500 --> 00:00:17,500
At the boarding gate, she suddenly dropped her bag in disbelief: 'Aarav... are you crazy?!'

4
00:00:17,500 --> 00:00:23,500
I held her trembling hands: 'We spent years loving online... I won't let you leave without a hug!'

5
00:00:23,500 --> 00:00:29,500
Tears streamed down her face: 'But my flight... my career... everything is there!'

6
00:00:29,500 --> 00:00:36,500
Will Meera stay or will she leave? What would you do? Vote in the comments!
""",
        "srt_hi": """1
00:00:00,000 --> 00:00:05,500
डिस्प्ले बोर्ड पर लाल अक्षरों में लिखा था: फ्लाइट BA-142 लंदन... लास्ट कॉल फॉर बोर्डिंग!

2
00:00:05,500 --> 00:00:11,500
सांस फूली हुई थी, कमीज़ भीगी थी... पर मेरी नज़र सिर्फ मीरा को ढूंढ रही थी।

3
00:00:11,500 --> 00:00:17,500
बोर्डिंग गेट पर उसने बैग गिरा दिया और कांपती आवाज़ में बोली: 'आरव... तुम पागल हो क्या?!'

4
00:00:17,500 --> 00:00:23,500
मैंने उसका हाथ थामा: 'सालों ऑनलाइन प्यार किया... बिना गले लगाए जाने नहीं दूंगा!'

5
00:00:23,500 --> 00:00:29,500
उसकी आंखों से आंसू छलक पड़े: 'पर मेरी फ्लाइट... मेरा करियर... सब वहां है!'

6
00:00:29,500 --> 00:00:36,500
क्या मीरा रुकेगी या चली जाएगी? आप होते तो क्या करते? कमेंट में वोट करें!
"""
    },
    {
        "id": 235,
        "yt_id": "cWNlv-WIb7c",
        "title": "Series 3 Ep 4: Chintu Found a Tiny Alien in His Lunchbox",
        "srt_en": """1
00:00:00,000 --> 00:00:05,500
As soon as Chintu opened his lunchbox during recess... his eyes popped wide open!

2
00:00:05,500 --> 00:00:11,000
Sitting right on his sandwich was a tiny 4-inch glowing blue alien, happily eating cheese!

3
00:00:11,000 --> 00:00:16,500
Golu screamed: 'Chintu, let's take a selfie with it and go viral!'

4
00:00:16,500 --> 00:00:22,000
The alien blinked its cute laser eyes, and Golu's heavy backpack started floating in mid-air!

5
00:00:22,000 --> 00:00:27,500
Books started flying across the whole classroom as the alien gave Chintu a cheerful thumbs up!

6
00:00:27,500 --> 00:00:35,000
If you found this tiny alien, what snack would you share? Pizza or Burger? Tell us in the comments!
""",
        "srt_hi": """1
00:00:00,000 --> 00:00:05,500
चिंटू ने रिसेस में जैसे ही अपना लंचबॉक्स खोला... उसकी आंखें फटी की फटी रह गईं!

2
00:00:05,500 --> 00:00:11,000
सैंडविच के ऊपर एक 4-इंच का चमकता हुआ नीला एलियन बैठ कर चीज़ खा रहा था!

3
00:00:11,000 --> 00:00:16,500
गोलू चिल्लाया: 'चिंटू भाई, इसके साथ सेल्फी लेकर वायरल करते हैं!'

4
00:00:16,500 --> 00:00:22,000
एलियन ने अपनी लेज़र आंखें झपकाईं और गोलू का स्कूल बैग हवा में उड़ने लगा!

5
00:00:22,000 --> 00:00:27,500
पूरी क्लास में किताबें तैरने लगीं और एलियन ने चिंटू को थम्स अप दे दिया!

6
00:00:27,500 --> 00:00:35,000
अगर आपको यह एलियन मिलता तो आप क्या खिलाते? पिज़्ज़ा या बर्गर? कमेंट करें!
"""
    },
    {
        "id": 236,
        "yt_id": "CUDgNziz-wk",
        "title": "Series 4 Ep 4: 99% of People Get This Wrong in 5 Seconds",
        "srt_en": """1
00:00:00,000 --> 00:00:05,000
Today's riddle will blow the minds of even the smartest people!

2
00:00:05,000 --> 00:00:10,500
What has a head and a tail... but has no body at all?

3
00:00:10,500 --> 00:00:16,500
You only have 5 seconds... countdown starts now! 5, 4, 3, 2, 1!

4
00:00:16,500 --> 00:00:21,500
If you guessed a snake or a lizard... you are completely wrong!

5
00:00:21,500 --> 00:00:26,500
The correct answer is... A COIN! Which has a Head and a Tail!

6
00:00:26,500 --> 00:00:31,000
Did you guess it before the timer ended? Be honest and tell us in the comments!
""",
        "srt_hi": """1
00:00:00,000 --> 00:00:05,000
आज की पहेली सुनकर बड़े-बड़े टॉपर्स का दिमाग हिल जाएगा!

2
00:00:05,000 --> 00:00:10,500
ऐसी कौन सी चीज़ है जिसका एक हेड और एक टेल है... पर कोई शरीर नहीं?

3
00:00:10,500 --> 00:00:16,500
आपके पास हैं सिर्फ 5 सेकंड... काउंटडाउन शुरू! पांच, चार, तीन, दो, एक!

4
00:00:16,500 --> 00:00:21,500
अगर आपने सोचा था सांप या छिपकली... तो आप बिल्कुल गलत हैं!

5
00:00:21,500 --> 00:00:26,500
सही जवाब है... एक सिक्का (A Coin)! जिसमें हेड और टेल दोनों होते हैं!

6
00:00:26,500 --> 00:00:31,000
कितने लोगों ने टाइमर खत्म होने से पहले सोचा था? सच-सच कमेंट में बताएं!
"""
    }
]

def upload_caption_track(token: str, yt_id: str, srt_text: str, lang: str, name: str) -> bool:
    boundary = f"===CAPTION_UPLOAD_{int(time.time()*1000)}==="
    metadata = json.dumps({
        "snippet": {
            "videoId": yt_id,
            "language": lang,
            "name": name,
            "isDraft": False
        }
    }).encode("utf-8")

    srt_bytes = srt_text.strip().encode("utf-8")
    body = (
        b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata +
        b"\r\n--" + boundary.encode() + b"\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n" +
        srt_bytes +
        b"\r\n--" + boundary.encode() + b"--\r\n"
    )

    url = "https://www.googleapis.com/upload/youtube/v3/captions?part=snippet&uploadType=multipart"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"    ✅ Uploaded {lang.upper()} ({name}) track: {data.get('id', 'OK')}")
            return True
    except Exception as e:
        print(f"    ❌ Failed to upload {lang} track: {e}")
        return False

def main():
    print("\n" + "=" * 75)
    print("  🚀 AUTOPILOT: UPDATING PREVIOUS VIDEOS WITH DUAL CC CAPTIONS")
    print("  Adding English & Hindi Tracks for 1-Tap Language Switch")
    print("=" * 75 + "\n")

    creds = authorize()
    token = creds.data.get("access_token")

    for v in VIDEOS:
        print(f"\n🎬 Video #{v['id']} ({v['yt_id']}): {v['title']}")
        print(f"  URL: https://youtube.com/shorts/{v['yt_id']}")

        # 1. Upload English
        upload_caption_track(token, v["yt_id"], v["srt_en"], "en", "English")
        time.sleep(1)

        # 2. Upload Hindi
        upload_caption_track(token, v["yt_id"], v["srt_hi"], "hi", "Hindi")
        time.sleep(1)

    print("\n" + "=" * 75)
    print("  🎉 ALL 3 VIDEOS UPDATED WITH DUAL-LANGUAGE (HINDI + ENGLISH) CC!")
    print("  Viewers can now tap the 'CC' button on screen to switch between Hindi & English!")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
