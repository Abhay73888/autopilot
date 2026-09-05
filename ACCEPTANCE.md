# ✅ ACCEPTANCE TESTS — Section 12

`python3 test_all.py` → **260 tests, sab green** (3 baar chalake verify kiya).

| # | Acceptance criterion | Status | Proof |
|---|---|---|---|
| 1 | `python test_all.py` — sab green | ✅ | 260/260 |
| 2 | Ek command se end-to-end video, bina manual step | ✅ | `python run.py` → 5.37 MB MP4 |
| 3 | Video: 22-45s, 1080x1920, H.264+AAC, −14 LUFS | ✅ | measured: 22.4s, 1080x1920, h264+aac, **−14.54 LUFS**, TP −1.51 dBTP |
| 4 | Subtitles word-level synced, sound-off pe samajh aaye | ✅ | ASS karaoke `\k` tags, Devanagari, screenshot verified |
| 5 | Consecutive 5 videos: alag voice + alag template | ✅ | test: 5 unique voices, ≥4 unique templates |
| 6 | YouTube upload `private`, AI disclosure ON | ✅ | `containsSyntheticMedia: true` + `privacyStatus: private` |
| 7 | IG container flow polls, timeout handle karta hai | ✅ | 3-step + `POLL_MAX_WAIT=300` + EXPIRED/ERROR handling |
| 8 | Quota manager galat time pe call **block** karta hai | ✅ | `QuotaExceeded` raise, dry-run bhi safe |
| 9 | Har API failure retry (exp backoff) + log | ✅ | `retry()` 1s→2s→4s + jitter, sab logged |
| 10 | Dashboard: approvals, 2h/24h metrics, experiments, quota | ✅ | + Analyst section, tick button |
| 11 | Learning DB mein kam se kam ek conclusion | ✅ | loop test: `pov +61%, p=0.00038, n=10` |
| 12 | Bina kisi API key ke mock mode mein chalta hai | ✅ | `python run.py --dry-run`, saare 243 tests bina key ke |

## Hard constraints (Section 1)

| # | Constraint | Status |
|---|---|---|
| 1 | ₹0 budget, graceful degrade | ✅ Sab free tier. Fallback chains har jagah |
| 2 | Dependencies minimum + justification | ✅ **3 packages**: edge-tts, Pillow, imageio-ffmpeg. Har ek justified |
| 3 | Kabhi silently fail nahi | ✅ Har failure logged + retry + dashboard pe |
| 4 | Har publish se pehle AI disclosure | ✅ Test-enforced, non-negotiable |
| 5 | Rate limits respect | ✅ Caps API limits se kam (uploads 5 vs ~7, IG 20 vs 50) |
| 6 | Copyright-safe | ✅ Audio 100% generated (sine + noise). Test: koi external audio nahi |

## Agent roster (Section 6) — saare 9

| # | Agent | Status |
|---|---|---|
| 1 | TrendScout 🔍 | ✅ apne data ke patterns + series + LLM, `search.list` kabhi nahi |
| 2 | Writer ✍️ | ✅ hook rotation, learnings padhta hai, comment bait |
| 3 | ArtDirector 🎨 | ✅ character consistency, 4 templates, loop ending |
| 4 | Voice 🎙️ | ✅ 6 profiles rotate, word timing, reveal pauses |
| 5 | Editor 🎬 | ✅ `pipeline/render.py` — Ken Burns, karaoke, sound design |
| 6 | Publisher 📤 | ✅ YouTube (resumable + AI flag) + Instagram (3-step container) |
| 7 | Analyst 📊 | ✅ 2h/24h/7d, retention thresholds, drop-off |
| 8 | Scientist 🧪 | ✅ Welch's t-test, min 5/arm, learning DB |
| 9 | Chief 🧭 | ✅ orchestrator, cron, digest, lock |

## Jo bana

```
35 files · ~11,900 lines · 260 tests
core/     config db ffmpeg hosting llm logbook mp3 oauth quota stats
agents/   trendscout writer artdirector voice imagegen publisher
          ig_publisher analyst scientist chief
pipeline/ render subtitles validate
web/      server (dashboard)
```

## Zero-dependency decisions (jahan package bacha)

| Kya | Package jo NAHI liya | Kyun |
|---|---|---|
| Gemini | `google-generativeai` | 20+ deps ek HTTP POST ke liye |
| OAuth + upload | `google-auth-oauthlib`, `google-api-python-client` | 8+ deps; stdlib se 400 line |
| MP3 duration | `mutagen` | 40-line frame parser |
| Stats | `scipy` (60 MB) | t-distribution khud, numerically verified |
| Analytics | `pandas` (50 MB) | `statistics` + SQL GROUP BY |
| Dashboard | `flask`/`fastapi` | `http.server` (Range support ke saath) |
| Config | `pyyaml` | 30-line parser (PyYAML optional) |
| Trends | trending-topics APIs | Sab paid ya scraping (ToS violation + ban risk) |
| HTTP | `requests` | `urllib` (multipart bhi) |
