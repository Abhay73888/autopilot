<div align="center">

# 🎬 AUTOPILOT

**Ek autonomous agent swarm jo cartoon suspense shorts khud banata hai,
Instagram Reels aur YouTube Shorts pe khud publish karta hai,
performance khud monitor karta hai, aur asli data se seekh kar khud ko behtar karta hai.**

`260 tests` · `11,900 lines` · `3 dependencies` · `₹0/month`

[Shuru karo](#-shuru-karo) · [Ye kya hai](#-ye-kya-hai) · [Kaise kaam karta hai](#-kaise-kaam-karta-hai) · [Imandari](#-imandari-ki-baatein)

</div>

---

## ⚡ Shuru karo

```bash
git clone <tumhara-repo> && cd autopilot
pip install -r requirements.txt
python status.py          # 👈 ye batayega ki agla kadam kya hai
```

`status.py` har baar **sirf ek agla kadam** batata hai — taaki confusion na ho:

```
✅ 1️⃣ MACHINE SETUP    (5/5)
⏳ 2️⃣ CONTENT QUALITY  (0/3)   ← YAHAN HO TUM

👉 TUMHARA AGLA KADAM
   Gemini API key
   aistudio.google.com/apikey → free key → .env mein daalo
```

**Pehli baar? → [`START_HERE.md`](START_HERE.md) padho.** 30 minute mein pehla video ban jaayega.

---

## 🎯 Ye kya hai

Ek command se poora video banta hai — bina kisi manual step ke:

```bash
python run.py
```

```
🎬 VIDEO READY — #4
   output/video_0004/final.mp4
   5.4 MB · 1080x1920 · 28.3s · h264+aac
   ✅ VALIDATE PASS   -14.5 LUFS · TP -1.5 dBTP
```

Aur ek command se **sab kuch apne aap** chalta hai:

```bash
python -m agents.chief --tick     # cron har ghante isse chalata hai
```

### Kya banta hai

| | |
|---|---|
| 🎨 **6-8 cartoon images** | Har image mein **wahi character** — same jacket, same chehra |
| 🎙️ **Hindi narration** | 6 voice profiles rotate hote hain |
| 🎬 **Ken Burns motion** | Slow zoom/pan, direction alternate — slideshow nahi lagta |
| 💬 **Karaoke subtitles** | Har shabd bolte waqt highlight (60% log sound off pe dekhte hain) |
| 🔊 **Sound design** | Drone ambience + whoosh transitions — **100% generated**, koi copyright nahi |
| 🔁 **Loop-perfect ending** | Aakhri frame = pehla frame → re-watch spike |

**Spec:** 1080×1920 · H.264 + AAC · 30fps · **−14 LUFS** · 22-45s

---

## 🧠 Kaise kaam karta hai

### 9 agents

| Agent | Kaam |
|---|---|
| 🔍 **TrendScout** | Topics — apne winners ke keywords + series + LLM. `search.list` **kabhi nahi** (100 units) |
| ✍️ **Writer** | Script + hook. 4 hook types retention ke hisaab se weighted, rotation enforced |
| 🎨 **ArtDirector** | 6-8 scenes. Character description **har prompt mein repeat** = consistency |
| 🎙️ **Voice** | 6 profiles rotate. Word-level timing, reveal se pehle 300ms pause |
| 🎬 **Editor** | ffmpeg — Ken Burns, crossfade, karaoke subs, sound design, loudnorm |
| 📤 **Publisher** | YouTube resumable upload + Instagram 3-step container flow |
| 📊 **Analyst** | 2h/24h/7d metrics, retention thresholds, drop-off point |
| 🧪 **Scientist** | A/B experiments — Welch's t-test, min 5/arm, learning DB |
| 🧭 **Chief** | Orchestrator, cron, daily digest, lock |

### Learning loop — ye band ho chuka hai

```
Publish
   ↓
2h metrics (velocity window — yahi decisive hai)
   ↓
Analyst: retention kya thi? drop-off kahan hua? kaunsa variable?
   ↓
Scientist: A/B experiment (auto-start → auto-conclude)
   ↓
Learning DB: "pov ne question se +61% better kiya, n=10, p=0.0004"
   ↓
Writer / Voice / ArtDirector agli baar ye padhte hain    ← ⭐ LOOP CLOSED
   ↓
Loop
```

**Asli test output:**
```
'pov' ne 'specific_outcome' se +61% behtar kiya (1437 vs 894 views @2h).
p=0.00038 matlab 99.96% chance ye asli farq hai, luck nahi. Confidence: medium (n=5+5).
➜ 'pov' ko prefer karo, par 'specific_outcome' ko rotation mein rehne do.
```

Uske baad Writer khud `pov` ko **33-38% share** dene lagta hai — **100% nahi**,
kyunki same hook har video mein = duplicate-pattern clustering = throttle.

---

## 🖥️ Dashboard

```bash
python -m web.server        # http://localhost:8765
```

- **Approve queue** — video player ke saath, Validate / Approve / Reject
- **Quota bars** — live, 80% pe peela, 90% pe laal
- **Analyst** — baseline, har video ka verdict, variable leaderboard
- **Scientist** — chal raha experiment + champions
- **Warnings** — aaj ke errors

🔒 Sirf `127.0.0.1` pe bind hota hai. Path-traversal protected. Test-enforced.

---

## 🛡️ Safety — yahi system ko zinda rakhta hai

### Quota caps API limits se **kam** hain (jaan-boojh kar)

| Bucket | Hamara cap | Asli limit | Kyun kam |
|---|---|---|---|
| `youtube_uploads` | **5/day** | ~7 (undocumented) | Docs 100 kehte hain, practice mein ~7 pe 429 |
| `youtube_search` | **5/day** | 100 | Har call **100 units** — poora din barbaad ho sakta hai |
| `ig_publishes` | **20/24h** | 50-100 | Sources disagree — safe margin |
| `ig_calls_hour` | **150/h** | 200 | Container polling bhi isi mein ginti hai |

Har API call se **pehle** `quota.can_spend()`. Budget khatam = task queue mein,
**crash nahi**.

### Publish se pehle 4 gates

```
APPROVAL → FILE → VALIDATE → QUOTA
```

`validate.py` wo sab pakadta hai jisse platform reject karega:
H.264/AAC nahi, audio missing, >90s (IG hard limit), placeholder images,
**beech mein kaale frames**, kaala pehla frame, loudness off-target.

### AI disclosure — non-negotiable

Har YouTube upload mein `status.containsSyntheticMedia: true`.
Test isse enforce karta hai. Undisclosed AI content = reduced reach ya removal.

### 🔐 Password kabhi nahi

**Instagram ka password nahi. YouTube ka password nahi.** Sirf OAuth tokens,
jo limited-permission wale hain aur jab chaaho cancel kar sakte ho.
Details: [`DEPLOY.md`](DEPLOY.md)

---

## 📦 Sirf 3 dependencies

```
edge-tts        # free neural TTS (Hindi)
Pillow          # fallback placeholder images
imageio-ffmpeg  # sirf agar system pe ffmpeg install na kar sako
```

**Jo jaan-boojh kar NAHI liye:**

| Package | Size | Kya kiya iski jagah |
|---|---|---|
| `google-generativeai` | 20+ deps | `urllib` se ek HTTP POST |
| `google-auth-oauthlib` + `google-api-python-client` | 8+ deps | OAuth + resumable upload stdlib se, 400 line |
| `scipy` | 60 MB | t-distribution khud likha, numerically verified |
| `pandas` | 50 MB | `statistics` + SQL `GROUP BY` |
| `flask` / `fastapi` | — | `http.server` (Range requests ke saath) |
| `requests` | — | `urllib` (multipart bhi) |
| `mutagen` | — | 40-line MP3 frame parser |
| `pyyaml` | — | 30-line parser (optional use hota hai) |

---

## 🧪 Tests

```bash
python test_all.py       # 260 tests, ~35 second
```

Saare tests **bina kisi API key ke** chalte hain. Kuch highlights:

- ⭐ Quota manager galat time pe call **block** karta hai
- ⭐ Dry-run mein quota kharch **nahi** hota (ye ek asli bug tha)
- ⭐ 5 consecutive videos mein 5 **alag voices** + ≥4 alag templates
- ⭐ Character description **har** image prompt mein repeat hoti hai
- ⭐ Beech mein **kaale frames nahi** (`fadeblack` bug regression)
- ⭐ t-test z-test se **conservative** hai (warna jhoothi learnings save hongi)
- ⭐ Koi significant farq na ho to **koi learning save nahi** hoti
- ⭐ Champion **100% share nahi** leta (clustering se bachav)
- ⭐ `search.list` **kahin use nahi** hota
- ⭐ Poora loop: publish → metrics → experiment → learning → next video

---

## 📁 Structure

```
autopilot/
├── status.py            👈 "ab kya karun?"
├── run.py               ek command = poora video
├── authorize_youtube.py
├── test_all.py          260 tests
│
├── core/                config db ffmpeg hosting llm logbook
│                        mp3 oauth quota stats
├── agents/              trendscout writer artdirector voice imagegen
│                        publisher ig_publisher analyst scientist chief
├── pipeline/            render subtitles validate
├── web/                 server (dashboard)
└── assets/fonts/        Noto Sans Devanagari
```

---

## 📚 Docs

| File | Kis liye |
|---|---|
| [**START_HERE.md**](START_HERE.md) | 👈 **pehle ye** — step by step, aaj kya karna hai |
| [SETUP.md](SETUP.md) | Har step ki poori detail + har error ka Hinglish matlab |
| [DEPLOY.md](DEPLOY.md) | Security (password kyun nahi dena) + server pe daalna |
| [ACCEPTANCE.md](ACCEPTANCE.md) | Kya-kya bana, kya verify hua |

---

## ⚠️ Imandari ki baatein

Ye cheezein main chhupaunga nahi:

**1. Text-to-video free mein available nahi hai.**
Veo, Sora, Runway — sab paid. Isliye ye system **image + TTS + ffmpeg** wala
rasta leta hai. Cartoon suspense content ke liye ye actually **behtar** hai
(style consistent rehti hai), par ye "AI video generation" nahi hai.

**2. edge-tts ke word timestamps dead hain.**
Maine test kiya — `WordBoundary` event ab khaali aata hai. Isliye har line ki
alag MP3 banti hai aur uski **exact duration measure** hoti hai; words ko
syllable-weight se distribute karte hain. Line boundaries **exact**, word
timing **±80ms**. Karaoke ke liye kaafi hai; frame-perfect chahiye to Whisper.

**3. Hindi mein sirf 2 base voices hain.**
edge-tts pe `Swara` + `Madhur`, bas. 6 **profiles** banaye (rate/pitch se) —
sunne mein alag lagte hain, par 6 alag *voice actors* jitna alag nahi.

**4. `zoompan` use nahi kiya.**
ffmpeg ka standard Ken Burns filter is machine pe **4 second ke clip pe 180+
second** le raha tha. `scale=eval=frame` + constant crop se **2.9 second** —
60× tez. Trade-off: zoom+pan simultaneously kam smooth, isliye alag motions.

**5. Instagram per-second retention curve nahi deta.**
YouTube deta hai, Meta nahi. IG ka exact drop-off point pata nahi chalta.

**6. Instagram scheduling "asli" nahi hai.**
Container 24h mein expire hota hai → pehle se schedule possible hi nahi.
Matlab **cron chalu rehna zaroori hai**, warna IG post nahi jayega.

**7. A/B experiments dheere hain.**
10 videos per experiment ÷ 2/day = **5 din per experiment**. Koi shortcut nahi —
`videos_per_day` badhane se clustering risk badhta hai.

**8. Predicted scores heuristics hain, ML nahi.**
Aur code ye chhupata nahi — data kam ho to score **0.5 (neutral) ki taraf
khisak jaata hai**, kyunki bina data ke confident hona jhooth hai.

**9. Ye system abhi asli published data pe test nahi hua.**
Statistics numerically verified hai, pipeline end-to-end kaam karti hai, par
**asli YouTube data ka variance simulation se zyada hoga**. Isliye
`review_first` default hai — pehle 20 videos tum khud dekhoge.

---

## 🚫 Ye kabhi mat karna

| ❌ | Kyun |
|---|---|
| Engagement pods, view bots, fake comments | Detect hota hai → permanent ban |
| Multiple Cloud projects se quota multiply | YouTube ToS violation → saare projects ka access jaata hai |
| Undisclosed AI content | Reduced recommendations ya removal |
| Watermark wala same file dono platforms pe | Turant downrank |
| `.env` GitHub pe push | Bots 60 second mein tokens chura lete hain |
| `data/autopilot.db` delete | Isme saari learnings hain — system ka dimaag |

> Ye guardrails moral lecture nahi hain — inhe todne se growth **rukti** hai.
> Ban hua account = zero growth.

---

<div align="center">

**Abhi shuru karo:**

```bash
python status.py
```

</div>
