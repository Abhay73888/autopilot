# 🛠️ AUTOPILOT — SETUP GUIDE (beginner ke liye)

> Ye guide maan kar chal rahi hai ki tumhe **kuch nahi pata**. Har step pe likha hai
> ki **kya dikhna chahiye** aur **error aaye to kya karna hai**.
>
> **Abhi Phase 1 ban chuka hai.** Iske liye tumhe **koi API key nahi chahiye**,
> **koi paisa nahi**, **koi account nahi**. Sirf Python.

---

## 📍 Abhi tak kya bana hai

| Phase | Kya | Status |
|---|---|---|
| **1** | `db.py`, `quota.py`, `logbook.py`, `llm.py` + `test_all.py` | ✅ **DONE** |
| **2** | Writer + ArtDirector + Voice + ImageGen → script + 6-8 images + mp3 | ✅ **DONE** |
| **3** | `render.py` — Ken Burns + karaoke subs + sound design → **MP4** | ✅ **DONE** |
| **4** | `validate.py` (IG code-24 gatekeeper) + **dashboard** | ✅ **DONE** |
| **5** | YouTube OAuth + resumable upload + AI disclosure | ✅ **DONE** |
| **6** | Instagram — 3-step container flow + video hosting | ✅ **DONE** |
| **7** | Analyst — 2h/24h/7d metrics + retention + drop-off | ✅ **DONE** |
| **8** | Scientist — A/B framework + learning loop | ✅ **DONE** |
| **9** | Chief — scheduler, cron, daily digest | ✅ **DONE** |
| **10** | Learning loop **CLOSED** | ✅ **DONE** |

| **+** | TrendScout — topic research (Section 6 agent #1) | ✅ **DONE** |

**🎉 System poora ban chuka hai. Saare 9 agents ban chuke hain.**

---

## STEP 1 — Python install karo

Chahiye: **Python 3.9 ya usse naya** (`zoneinfo` module iske baad hi aaya).

**Check karo:**
```bash
python3 --version
```

**Kya dikhna chahiye:** `Python 3.11.x` (ya 3.9+ koi bhi)

**Agar `command not found` aaye:**
- **Windows:** [python.org/downloads](https://python.org/downloads) → installer chalao →
  ⚠️ **"Add Python to PATH" wala checkbox ZAROOR tick karo** (90% beginners yahi bhoolte hain).
  Windows pe command `python` hai, `python3` nahi.
- **Mac:** `brew install python3` (Homebrew nahi hai to pehle [brew.sh](https://brew.sh))
- **Linux:** `sudo apt install python3 python3-pip`

**Agar `Python 3.8` ya usse purana dikhe:** upgrade karna padega, warna `zoneinfo`
import fail hoga (`ModuleNotFoundError: No module named 'zoneinfo'`).

---

## STEP 2 — Project ko chalao

```bash
cd autopilot
python3 test_all.py
```

**Kya dikhna chahiye** (aakhri lines):
```
==============================================================
  ✅ PASS: 260    ❌ FAIL: 0
==============================================================

🎉 SAARE 10 PHASE GREEN HAIN. System poora ban chuka hai.

📊 QUOTA REPORT
------------------------------------------------------------------------
  youtube_units      ░░░░░░░░░░░░░░░░░░░░      0/10000  reset 14h 1m baad
  ...
```

### ❗ Agar error aaye

| Error | Matlab | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'core'` | Tum galat folder mein ho | `cd autopilot` karo, phir chalao |
| `ModuleNotFoundError: No module named 'zoneinfo'` | Python 3.8 ya purana | Python 3.9+ install karo |
| `sqlite3.OperationalError: database is locked` | Do process ek saath DB likh rahe hain | Baaki terminals band karo |
| `PermissionError` on `logs/` | Folder likhne ki permission nahi | `chmod -R u+w autopilot` |
| Ajeeb `\033[36m` jaise characters dikhein | Purana Windows terminal colours support nahi karta | Windows Terminal ya PowerShell 7 use karo — code sahi chal raha hai |

> **Note:** Phase 1 ka poora code **sirf Python stdlib** pe chalta hai — koi `pip install` nahi.
> Phase 2 ke liye sirf 2 package chahiye (agla step).

---

## STEP 2b — Phase 2 ke 2 packages install karo

```bash
pip install -r requirements.txt
```

Ye sirf 2 cheezein layega (dono free, koi account nahi):
- **edge-tts** — Microsoft ki free neural TTS. Hindi ki sabse acchi awaaz.
- **Pillow** — placeholder images ke liye (jab image API fail ho).

**Check:**
```bash
python3 -c "import edge_tts, PIL; print('OK')"
```

**Agar `pip: command not found`:** `python3 -m pip install -r requirements.txt` try karo.
**Agar `externally-managed-environment` error (naya Linux/Mac):**
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```
(Windows pe activate karne ka command: `.venv\Scripts\activate`)

---

## STEP 3 — Config apne hisaab se bharo

`config.yaml` kholo aur ye 3 lines badlo:

```yaml
brand_name:        "AUTOPILOT"        # <- apna channel naam
instagram_handle:  "@your_handle"     # <- apna IG handle
youtube_channel:   "https://youtube.com/@your_channel"
```

Check karo ki load ho rahi hai:
```bash
python3 core/config.py
```
**Kya dikhna chahiye:** saari settings ki list, jisme tumhara naya `brand_name` ho.

⚠️ **`video_length_sec` ko 22-45 ke beech hi rakhna.** Test isse enforce karta hai.
Sub-15s videos 2026 mein collapse ho gaye (absolute watch-time bar clear nahi hota),
aur 45s+ pe retention threshold miss hone lagta hai.

---

## STEP 4 — `.env` file banao (abhi khaali chalegi)

```bash
cp .env.example .env
```

Phase 1 ke liye isme kuch bharna zaroori **nahi** hai — system mock mode mein chalega.
Phase 2 se pehle sirf ek cheez chahiye hogi:

**Gemini API key (free, credit card nahi):**
1. [aistudio.google.com/apikey](https://aistudio.google.com/apikey) kholo
2. Google account se login karo
3. **"Create API key"** → **"Create API key in new project"**
4. Key copy karo → `.env` mein paste karo: `GEMINI_API_KEY=AIza...`
5. `config.yaml` mein `mock_mode: false` kar do

Test karo:
```bash
python3 core/llm.py
```
- `mock? True` dikhe → key nahi mili ya `mock_mode: true` hai
- `mock? False` + Hindi mein asli script JSON dikhe → ✅ Gemini connected

**Agar `403` aaye:** key galat hai ya us project mein Generative Language API enable nahi hai.
**Agar `429` aaye:** free tier ka rate limit — code khud backoff karke retry karega, ruko.

---

## STEP 5 — ffmpeg install karo ⚠️ **ab ye ZAROORI hai**

Phase 3 se ffmpeg optional nahi hai — video isi se banta hai.

```bash
ffmpeg -version
```
**Kya dikhna chahiye:** `ffmpeg version 6.x ...` ya `7.x`

**Nahi hai to — 2 raaste:**

**Raasta A (recommended) — system install:**
- **Windows:** `winget install Gyan.FFmpeg`
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

Install ke baad **terminal band karke naya kholo** — warna PATH refresh nahi hota.

**Raasta B — admin rights nahi hain / office laptop:**
```bash
pip install imageio-ffmpeg
```
Ye ffmpeg ka binary pip ke through le aata hai, koi sudo nahi chahiye.
Code khud detect kar lega. **Limitation:** isme `ffprobe` nahi hota
(code ka fallback hai, chal jayega) aur `drawtext` filter bhi nahi hota
(hum use hi nahi karte — subtitles `libass` se lagte hain).

### ✅ Check karo ki tumhare ffmpeg mein sab hai

```bash
python3 core/ffmpeg.py
```

**Kya dikhna chahiye:**
```
ffmpeg : /usr/bin/ffmpeg
ffprobe: /usr/bin/ffprobe
caps   :
   ✅ ass          <- subtitles ke liye ZAROORI
   ✅ xfade        <- crossfade transitions
   ✅ loudnorm     <- -14 LUFS normalize
   ✅ libx264      <- ZAROORI (IG H.264 maangta hai)
   ✅ aac          <- ZAROORI (IG AAC maangta hai)
```

| Missing | Kya hoga | Fix |
|---|---|---|
| `libx264` ❌ | Instagram **error code 24** dega, video reject | Poora build install karo, minimal nahi |
| `aac` ❌ | Same — IG reject karega | Same |
| `ass` ❌ | **Subtitles nahi lagenge.** 60% log sound off pe dekhte hain → video unke liye bekaar | Poora build install karo |
| `drawtext` ❌ | Kuch nahi. Hum use hi nahi karte | Ignore karo |
| `ffprobe` ❌ | Kuch nahi. Code ffmpeg stderr se parse kar leta hai | Ignore karo |

---

## STEP 5b — Devanagari font (Hindi subtitles ke liye)

Agar tumhara content **Hindi** mein hai to ye font chahiye, warna subtitles
mein ☐☐☐ boxes dikhenge.

```bash
ls assets/fonts/NotoSansDevanagari-Bold.ttf
```

Nahi hai to download karo:
```bash
curl -L -o assets/fonts/NotoSansDevanagari-Bold.ttf \
  "https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth,wght%5D.ttf"
```
(Ya [fonts.google.com/noto/specimen/Noto+Sans+Devanagari](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari)
se manually download karke `assets/fonts/` mein `NotoSansDevanagari-Bold.ttf` naam se rakh do.)

Font free hai (SIL Open Font License) — commercial use bhi allowed hai.

---

## STEP 5c — YouTube setup (Phase 5 ke liye) — 15-20 minute

Ye ek baar ka kaam hai. Dhyan se karo, warna Phase 5 atak jayega.

### 1️⃣ Google Cloud project banao
1. [console.cloud.google.com](https://console.cloud.google.com) kholo
2. Upar **project dropdown** → **New Project** → naam do (jaise `autopilot`) → Create
3. Project select ho gaya hai ye confirm karo (upar naam dikhega)

### 2️⃣ YouTube Data API v3 enable karo
1. Left menu → **APIs & Services** → **Library**
2. Search: `YouTube Data API v3` → uspe click → **ENABLE**

**Agar ye step bhool gaye:** har API call pe `403` aayega.

### 3️⃣ OAuth consent screen
1. **APIs & Services** → **OAuth consent screen**
2. User Type: **External** → Create
3. App name: kuch bhi (jaise `AUTOPILOT`). Support email + developer email: apni email
4. **Scopes** page: kuch add mat karo, **Save and Continue**
5. **Test users** page: **+ ADD USERS** → **apni wahi email daalo jispe YouTube channel hai**
   ⚠️ Ye step skip mat karna, warna login pe "access_denied" milega
6. Save

> ⚠️ **BAHUT ZAROORI:** Consent screen **"Testing"** mode mein hai to refresh token
> **har 7 din baad expire** ho jayega, aur tumhe dobara authorize karna padega.
> **Permanent fix:** OAuth consent screen pe **"PUBLISH APP"** dabao → **Production**.
> Verification ki zaroorat nahi hai (wo sirf tab chahiye jab 100+ users ho).

### 4️⃣ OAuth client ID banao
1. **APIs & Services** → **Credentials** → **+ CREATE CREDENTIALS** → **OAuth client ID**
2. Application type: **Desktop app** ⚠️ (Web application NAHI)
3. Create → popup mein **DOWNLOAD JSON**
4. Us file ko project folder mein **`client_secret.json`** naam se rakho

```bash
ls client_secret.json    # yahan dikhna chahiye
```

### 5️⃣ Authorize karo
```bash
python3 authorize_youtube.py
```

Browser khulega:
- Apne **YouTube channel wale** Google account se login karo
- ⚠️ **"Google hasn't verified this app"** aaye to → **Advanced** → **Go to AUTOPILOT (unsafe)**
  (Ye tumhara hi app hai. Google ne sirf isliye verify nahi kiya kyunki ye public app nahi hai.)
- Saari permissions pe **Allow**

**Kya dikhna chahiye:**
```
==============================================================
  ✅ YOUTUBE CONNECTED
==============================================================
  Channel      : Tumhara Channel
  Channel ID   : UCxxxxxxxxxxxxxxxxxxxxxx
  Subscribers  : 0
  Uploads list : UUxxxxxxxxxxxxxxxxxxxxxx
```

**Uploads playlist ID copy karke rakh lo** — TrendScout isse tumhare videos ka
data **1 unit** mein padhega (`search.list` 100 units leta hai, 100× mehnga).

### YouTube setup ke errors

| Error | Matlab | Fix |
|---|---|---|
| `client_secret.json nahi mila` | File download nahi hui ya galat naam | Step 4 dobara |
| `'installed' ya 'web' key nahi hai` | Galat type ka client banaya | **Desktop app** type chahiye |
| `access_denied` | Test users mein apni email nahi daali | Step 3.5 |
| `403` har call pe | API enable nahi kiya | Step 2 |
| `invalid_grant` har 7 din baad | App "Testing" mode mein hai | Consent screen → **PUBLISH APP** |
| `Is account pe koi YouTube channel nahi hai` | Sach mein channel nahi hai | youtube.com pe channel banao |
| `refresh_token nahi diya` | App pehle se authorized hai | [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → access hatao → dobara |

---

## 📤 PHASE 5 — YouTube pe upload

**Hamesha pehle dry-run karo** (kuch upload nahi hoga, sirf metadata dikhega):
```bash
python3 -m agents.publisher 1 --dry-run
```

Sab theek lage to asli upload (**private** mein jaayega):
```bash
python3 -m agents.publisher 1
```

Aur options:
```bash
python3 -m agents.publisher --info              # channel info
python3 -m agents.publisher                     # approved videos ki list
python3 -m agents.publisher 1 --schedule        # peak time pe schedule
python3 -m agents.publisher 1 --privacy unlisted
```

### 4 gates — har ek pass hona zaroori hai

```
1. APPROVAL  → status 'approved' hona chahiye (review_first mode)
2. FILE      → final.mp4 exist karti ho
3. VALIDATE  → koi FATAL issue na ho
4. QUOTA     → budget bacha ho (cap 5 uploads/day)
```

Koi bhi gate fail = upload nahi, aur saaf Hinglish mein reason.

> **Quota khatam ho to crash nahi hota** — video `approved` pe wapas chala jaata hai
> aur kal apne aap try hoga (Phase 9 ka scheduler).

### ⭐ AI disclosure — automatic

Har upload mein `status.containsSyntheticMedia: true` jaata hai. Ye YouTube ka
**official** "Altered/Synthetic content" flag hai (API se supported, Oct 2024 se).
Description mein bhi disclosure line jaati hai.

Ye **hard constraint #4** hai — test isse enforce karta hai. Undisclosed AI content
= reduced recommendations ya removal.

### Publish ke baad — 2 manual kaam

1. **Comment PIN karna** — API se pin nahi hota. Video public karne ke baad
   YouTube Studio mein jaakar first comment ko manually pin karo (30 second ka kaam,
   par early engagement velocity ke liye important hai).
2. **Private → Public** — pehla video khud dekho, phir Studio se public karo.
   Confidence aane ke baad `--privacy public` use karna.

### Phase 5 ke errors

| Error | Matlab | Fix |
|---|---|---|
| `status 'rendered' hai, 'approved' nahi` | Dashboard se approve nahi kiya | `python3 -m web.server` → Approve |
| `uploadLimitExceeded` | **Hidden ~7/day limit** hit hua | Kal try karo. `quota.py` ka cap 5 hai — usse mat badhana |
| `quotaExceeded` | 10,000 daily units khatam | Midnight Pacific Time pe reset |
| `youtubeSignupRequired` | Account pe channel nahi hai | Channel banao |
| `thumbnailsNotAvailable` | Channel phone-verified nahi | [youtube.com/verify](https://youtube.com/verify) (2 min) |
| Upload beech mein ruk gaya | Net toota | Resumable hai — dobara chalao, wahin se resume hoga |

---

## ⏰ STEP 6 — ABHI KARO: Instagram App Review submit

> **Ye sabse zaroori manual step hai. Aaj hi shuru karo.**
> Meta App Review mein **2-4 hafte** lagte hain. Us se pehle API sirf
> **max 25 test users** pe kaam karti hai. Agar aaj submit karoge to jab tak
> Phase 6 tak pahuchoge, approval aa chuka hoga. Warna 3 hafte khaali baithoge.

1. Instagram app → Settings → Account type → **Business ya Creator** pe switch karo
   (Personal account API se post **nahi** kar sakta — ye hard block hai)
2. Ek **Facebook Page** banao aur Instagram account usse link karo
3. [developers.facebook.com](https://developers.facebook.com) → **Create App** → type: **Business**
4. App mein **Instagram Graph API** product add karo
5. **Roles → Test Users** mein apna account add karo (approval se pehle isi se test hoga)
6. **App Review → Permissions** mein ye 4 maango:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments` (pinned first comment ke liye)
   - `instagram_manage_insights` (Analyst ke metrics ke liye)
7. Screencast video banani padegi jisme dikhe ki app kya karti hai. **Ab submit kar do.**

YouTube mein ye problem nahi — wahan OAuth turant kaam karta hai (Phase 5).

---

## 🧠 Phase 1 mein kya-kya bana — chhota tour

### `core/config.py`
`config.yaml` padhta hai. Environment variable se override kar sakte ho:
```bash
AUTOPILOT_MOCK_MODE=false python3 test_all.py
```

### `core/logbook.py`
Do jagah log jaata hai: console pe (rangeen, Hinglish) aur `logs/autopilot-YYYY-MM-DD.jsonl`
mein (dashboard isse padhega). Do khaas cheezein:
- **`explain(error)`** — error ko Hinglish mein samjhata hai.
  `403 quotaExceeded` → *"YouTube ka daily quota khatam. Midnight Pacific Time pe reset hoga."*
- **`retry(fn)`** — exponential backoff + jitter. 1s → 2s → 4s. Saari koshishein fail
  hone pe exception raise hoti hai (**silent fail kabhi nahi**).

Dekhna chahte ho? `python3 core/logbook.py`

### `core/db.py`
SQLite, 6 tables: `videos`, `metrics`, `experiments`, `learnings`, `quota_usage`, `events`.

Do function jo baad mein bahut kaam aayenge:
- **`db.pick_rotated("voice_id", options, avoid_last=4)`** — aisi voice chunta hai jo
  pichhle 4 videos mein use na hui ho. YouTube ka **duplicate-pattern clustering**
  (same voice + same template = throttle) isse bachta hai.
- **`db.expire_old_learnings()`** — 90 din purani learning ka confidence apne aap
  `high → medium → low` gir jaata hai. Algorithm badalta rehta hai, purani seekh zeher hai.

### `core/quota.py` ⭐ sabse zaroori
Har API call se **pehle** `quota.can_spend()` poochho.

```python
q.yt_call("videos.insert")      # 100 units + 1 upload slot, dono kat gaye
q.yt_call("playlistItems.list") # sirf 1 unit
q.yt_call("search.list")        # 100 units — warning bhi deta hai
```

Hamare caps **API ki asli limit se kam** hain, jaan-boojh kar:

| Bucket | Hamara cap | Asli | Kyun kam |
|---|---|---|---|
| `youtube_uploads` | **5/day** | ~7 (undocumented) | Docs 100 kehte hain, practice mein ~7 pe 429 aata hai |
| `youtube_search` | **5/day** | 100 | Har call 100 units khaata hai — poora din barbaad ho sakta hai |
| `ig_publishes` | **20/24h** | 50-100 (sources disagree) | Safe margin |
| `ig_calls_hour` | **150/h** | 200 | Container polling bhi isi mein ginti hai |

Report dekho: `python3 core/quota.py`

### `core/llm.py`
Gemini REST API, sirf `urllib` se (koi SDK nahi = koi dependency nahi).
Key nahi mili / quota khatam / API down → **MockLLM** chalu ho jaata hai,
system rukta nahi. `llm.json()` markdown fences aur extra text apne aap saaf karta hai.

---

---

## 🎬 PHASE 2 — pehla content banao

```bash
python3 run_phase2.py
```

Pehli baar mein **3-5 minute** lagenge (7 images generate hoti hain, har ek 20-40s).
Jaldi test karna ho:
```bash
python3 run_phase2.py --dry-run --no-images    # 6 second, koi network nahi
python3 run_phase2.py --topic "Wo train jo kabhi pahunchi hi nahi"
```

**Kya dikhna chahiye:**
```
====================================================================
  ✅ PHASE 2 COMPLETE — video #1
====================================================================
  Title      : ...
  Hook type  : pov
  Template   : Noir Teal  (noir_teal)
  Voice      : hi_f_calm  [hi-IN-SwaraNeural rate=-4% pitch=-2Hz]
  Duration   : 22.39s   (target 32s, sweet spot 22-45s)
  Scenes     : 7   Words: 50
--------------------------------------------------------------------
  📁 output/video_0001
     scene_*.jpg   : 7 files (488 KB)
     narration.mp3 : ✅ 131 KB
     timing.json   : ✅
     manifest.json : ✅
```

**Folder mein kya milega:**

| File | Kya hai |
|---|---|
| `scene_01.jpg` … `scene_07.jpg` | 6-8 cartoon images, same character har image mein |
| `narration.mp3` | poori narration, ek file |
| `lines/line_01.mp3` … | har line ki alag audio (timing measure karne ke liye) |
| `timing.json` | word-level timing — Phase 3 karaoke subtitles isse banayega |
| `manifest.json` | **sab kuch ek jagah** — `render.py` bas yahi padhega |

Images dekhne ke liye folder khol lo. **Sabhi images mein same aadmi dikhna chahiye**
(same jacket, same scarf, same chehra) — yahi character consistency hai.

### Phase 2 ke errors

| Error | Matlab | Fix |
|---|---|---|
| `Saare image providers fail ho gaye` | Internet nahi, ya pollinations down | `--dry-run` se test karo; net check karo |
| `PLACEHOLDER image bani` | pollinations + gemini dono fail | Ye publish layak nahi. Net theek karke dobara chalao |
| `Saare TTS engines fail` | edge-tts install nahi ya net down | `pip install edge-tts` |
| `Pauses lagaye nahi ja sake (ffmpeg missing)` | ffmpeg nahi hai | Normal hai Phase 2 mein. Code khud sync theek kar leta hai. Phase 3 se pehle install kar lena |
| `Narration 19.2s — 22s se chhota` | Script chhoti nikli | Mock mode ka script chhota hota hai. Gemini key daalo, ya `--topic` se bada topic do |

---

## 🧠 Phase 2 mein kya bana — chhota tour

### `agents/writer.py`
Script + hook + caption + title. 4 hook types, **retention ke hisaab se weighted**:
`specific_outcome` 45% > `pov` 42% > `contrarian` 38% > `question` 28%.
`generic_reveal` (12%) **banned** hai — code use hi nahi karne dega.

**Hard rule:** pichhle video ka hook type dobara nahi chalega. Ye clustering se bachav hai.
Writer har run se pehle **learnings DB padhta hai** — jo hook jeeta hua hai use 2× weight.

### `agents/artdirector.py`
Script → 6-8 scenes. Do sabse zaroori cheezein:
- **Character consistency:** har image prompt mein wahi 15-25 shabd ki character
  description **hubahu repeat** hoti hai. Image models ki koi memory nahi hoti —
  consistency ka ek hi tareeka hai, sab dobara likhna.
- **4 templates rotate:** Noir Teal / Moonlit Blue / Sepia Archive / Crimson Alert.
  Pichhle 3 videos wala template dobara nahi aayega.
- **Loop:** aakhri scene = pehla scene ka echo (scene 1 `zoom_in`, aakhri `zoom_out`)
  → re-watch spike.

### `agents/voice.py`
**6 voice profiles** rotate hote hain. Pichhle 4 videos wali voice dobara nahi aayegi.

### `agents/imagegen.py`
`pollinations` → `gemini_image` → `local_placeholder`. Pehla fail ho to agla.
Teeno fail = exception (chupke se aage nahi badhta).

---

## ⚠️ Phase 2 ki 2 ASLI limitations (jhoot nahi bolunga)

### 1. Hindi mein sirf 2 base voices hain
edge-tts ke paas Hindi mein bas `hi-IN-Swara` (female) aur `hi-IN-Madhur` (male) hain.
Section 5 ne 4-6 alag voices maangi thi.

**Jo kiya:** 6 **voice profiles** banaye = 2 base voices × alag rate/pitch.
`hi_f_calm` (-4% rate, -2Hz) aur `hi_f_urgent` (+12%, +6Hz) sunne mein saaf alag lagti hain,
aur audio fingerprint bhi alag ho jaata hai.

**Limitation:** ye 6 alag *voice actors* jitna alag nahi hai. Agar aage jaakar clustering
ka shak ho, to English profiles bhi rotation mein daal sakte ho (`en-IN-Neerja`,
`en-IN-Prabhat`) — code mein `VOICE_PROFILES_EN` already hai.

### 2. Word-level timestamps ASLI nahi, ESTIMATED hain
edge-tts ka `WordBoundary` event ab khaali aata hai — Microsoft ne server-side band
kar diya lagta hai (maine test kiya, July 2026).

**Jo kiya:** har line ki **alag MP3** banate hain aur uski **exact duration measure**
karte hain (`core/mp3.py`). Phir us line ke andar words ko **syllable-weight** se
baant dete hain (lamba shabd = zyada time).

- **Line boundaries: EXACT** ✅ (measured)
- **Line ke andar word timing: ~±80ms** ⚠️ (estimated)

Karaoke subtitles ke liye ye bilkul theek lagta hai. Frame-perfect chahiye to
Whisper chahiye hoga — jo CPU pe slow hai aur ₹0 budget mein GPU nahi hai.

### 3. Mock mode ka content publish layak NAHI hai
Bina Gemini key ke saare scenes ka prompt ek jaisa banta hai → saari images
ek jaisi dikhengi. Character consistency to perfect rahegi, par **variety zero**.
**Phase 3 se pehle Gemini key le lo** (STEP 4).

---

---

## 🎬 PHASE 3 — PEHLA ASLI VIDEO (ek command)

```bash
python3 run.py
```

**Bas. Yahi ek command.** Ye script likhta hai, images banata hai, narration
karta hai, aur MP4 render kar deta hai.

Pehli baar **4-6 minute** lagenge. Jaldi test:
```bash
python3 run.py --dry-run            # ~50 second, koi network nahi
python3 run.py --render-only 1      # video #1 sirf dobara render karo (tez iteration)
python3 run.py --count 2            # 2 videos
python3 run.py --preset slow        # dheema par chhoti file
```

**Kya dikhna chahiye:**
```
🔍 PREFLIGHT CHECK
------------------------------------------------------------
  ✅ ffmpeg          (system)
  ✅ Devanagari font
  ✅ edge-tts
  ✅ Gemini API key
------------------------------------------------------------
...
====================================================================
  🎬 VIDEO READY — #1
====================================================================
  output/video_0001/final.mp4
  5.62 MB · 1080x1920 · 22.39s · h264+aac
--------------------------------------------------------------------
  ✅ Length 22.39s (22-45s sweet spot)
  ✅ Resolution 1080x1920
  ✅ Video codec h264 (H.264 chahiye)
  ✅ Audio codec aac (AAC chahiye)
  ✅ Size 5.62 MB (IG limit ~100MB)
  ✅ Word-level subtitles
  ✅ Cover frame
====================================================================
```

**Ab `output/video_0001/final.mp4` kholo aur dekho.** Video mein ye sab hona chahiye:
- Har image pe **slow zoom ya pan** (Ken Burns) — static slideshow nahi
- Scenes ke beech **crossfade**
- Neeche **karaoke subtitles** — har shabd bolte waqt **golden** highlight hota hai
- Upar pehle 3 second **hook overlay** (golden text)
- Background mein **halki drone awaaz** + har cut pe **whoosh**
- Aakhri frame pehle frame jaisa (loop)

### Phase 3 ke errors

| Error | Matlab | Fix |
|---|---|---|
| `ffmpeg nahi mila` | Install nahi hai ya PATH mein nahi | STEP 5 dekho. Terminal restart karna mat bhoolna |
| `Unknown filter 'ass'` | Minimal ffmpeg build hai | Poora build install karo (`brew`/`apt` wala) |
| `Invalid argument` (libx264) | Filter ko odd dimensions mile | Ye bug hai — report karo (code even-rounding karta hai) |
| Subtitles mein ☐☐☐ boxes | Devanagari font nahi hai | STEP 5b |
| `Narration audio nahi mila` | Phase 2 nahi chala | `python3 run_phase2.py` pehle |
| Render 15 min se zyada | Machine slow ya video lamba | `--preset ultrafast` try karo |
| Video mein awaaz nahi | edge-tts fail hua tha | Log dekho, `pip install edge-tts` |

---

## 🧠 Phase 3 mein kya bana

### `core/ffmpeg.py`
ffmpeg 3 jagah dhoondhta hai: PATH → `imageio-ffmpeg` (pip) → `FFMPEG_BINARY` env.
Har build alag hota hai, isliye `capabilities()` check karta hai ki kaunse filters hain.
`ffprobe` na ho to ffmpeg ke stderr se parse kar leta hai.

### `pipeline/subtitles.py`
**ASS format**, SRT nahi — kyunki SRT sirf static text de sakta hai. ASS mein
`{\k}` karaoke tags hote hain jo har shabd ko uske bolne ke time pe highlight karte hain.
Do layers: hook overlay (upar, 3s) + karaoke subtitles (neeche, poore video mein).
Bonus SRT bhi banti hai — YouTube pe upload karne ke liye (Shorts ab search mein dikhte hain).

### `pipeline/render.py`
6 steps: per-scene clips → crossfade → subtitles → audio mix → loudnorm → cover frame.

**Sound design 100% generated hai** (hard constraint #6 — koi copyrighted music nahi):
- Drone ambience = 55Hz + 110.7Hz sine waves (halka detune = "unease" feel), −32dB
- Whoosh = brown noise + fast fade, har cut pe
- Narration pe compressor (mobile speaker pe clear)
- Sab kuch **−14 LUFS** pe normalize

### `run.py`
Ek command = poora video. Pehle **preflight check** chalta hai jo batata hai
ki kya missing hai, phir Phase 2 + Phase 3.

---

## ⚠️ Phase 3 ka ek ASLI technical faisla (jhoot nahi bolunga)

**ffmpeg ka standard Ken Burns filter `zoompan` hai. Maine use NAHI kiya.**

Kyun? Maine test kiya — `zoompan` is machine pe **4 second ke ek clip pe 180+
second** le raha tha (wo har frame pe poora image dobara rescale karta hai).
7 scenes = 20+ minute per video. Ye unusable hai.

**Jo kiya:** `scale=eval=frame` + constant `crop`. Same visual result,
**2.9 second** mein. ~60× tez. Poora 22s video ab **~50 second** mein render hota hai.

**Limitation:** zoom aur pan ek saath thoda kam smooth hote hain. Isliye hum
zoom AUR pan ko **alag motions** rakhte hain (`zoom_in`, `pan_left`, ...) —
jo actually behtar dikhta hai, dono ek saath karna nauseating lagta hai.

---

---

## 🖥️ PHASE 4 — VALIDATE + DASHBOARD

### `validate.py` — publish se pehle ka gatekeeper

`run.py` ab **khud** validate chalata hai. Alag se bhi chala sakte ho:

```bash
python3 -m pipeline.validate              # aakhri video
python3 -m pipeline.validate --all        # saare videos
python3 -m pipeline.validate --fast       # loudness/black check skip (tez)
python3 -m pipeline.validate --json       # JSON output (scripts ke liye)
```

**Kya dikhna chahiye:**
```
====================================================================
  ✅ PASS — video_0001/final.mp4
====================================================================
  1080x1920 · 22.4s · h264+aac · 30.0fps · 5.37 MB
  Loudness: -14.54 LUFS  ·  True peak: -1.51 dBTP
--------------------------------------------------------------------
  Koi problem nahi mili. 🎉
--------------------------------------------------------------------
  ✅ Publish ke liye ready
====================================================================
```

**Teen severity levels:**

| Level | Matlab |
|---|---|
| ❌ **FATAL** | Publish **mat** karo — platform reject karega |
| ⚠️ **WARN** | Publish ho jayega, par performance kharab hogi |
| ℹ️ **INFO** | Dhyan dene layak, par theek hai |

**Kya-kya check hota hai:**

| Check | Level | Kyun |
|---|---|---|
| Video codec ≠ H.264 | FATAL | **IG error code 24** — format reject |
| Audio codec ≠ AAC | FATAL | **IG error code 24** |
| Audio hai hi nahi | FATAL | IG bina audio ke Reel reject karta hai |
| Horizontal video | FATAL | Reels/Shorts vertical hain |
| fps 23-60 ke bahar | FATAL | IG ki hard limit |
| Duration > 90s | FATAL | **IG API ki hard limit** (app mein 3 min chalta hai, API mein nahi) |
| Size > 100 MB | FATAL | Upload fail |
| **Placeholder images** | FATAL | Gradient cards publish layak nahi |
| Duration > 60s | WARN | YouTube pe Short nahi banega, normal video ban jayega |
| Duration 22s se kam | WARN | Sub-15s 2026 mein collapse ho gaya |
| Loudness −14 LUFS se door | WARN | Platform normalize karega → noisy ya squashed |
| **Beech mein kaale frames** | WARN | Darshak ko lagta hai video khatam → scroll |
| Pehla frame kaala | WARN | 1-second retention YT ka sabse bada signal hai |
| Subtitles nahi | WARN | 60% log sound off pe dekhte hain |
| espeak robotic voice | WARN | Retention girega |

---

### Dashboard

```bash
python3 -m web.server
```
Browser khud khul jayega: **http://localhost:8765**

Ya video banate hi kholo:
```bash
python3 run.py --dashboard
```

**Dashboard pe kya hai:**
- **Approve Queue** — har video ka **player** (seek kar sakte ho), hook, voice,
  template, hashtags, aur 3 buttons: 🔍 Validate · ✅ Approve · ✕ Reject
- **Quota** — har API ka live budget bar (80% pe peela, 90% pe laal)
- **Published** — 2h/24h views aur retention (Phase 7 mein bharenge)
- **Experiment + Learnings** — chal raha A/B test aur ab tak ki seekh
- **Warnings/Errors** — aaj ke sirf WARN/ERROR logs (INFO ka shor nahi)

Har 15 second khud refresh hota hai.

> **`review_first` ka matlab yahi hai:** video ban ke `validated` status pe rukta hai.
> Jab tak tum dashboard se **Approve** nahi karoge, publish nahi hoga.
> Pehle 20 videos ke baad `config.yaml` mein `autonomy: auto_publish` kar dena.

**Reject karte waqt reason zaroor likhna** — wo DB mein save hota hai aur
Phase 8 mein Scientist usse learning banayega.

### 🔒 Dashboard security

- Sirf **`127.0.0.1`** pe bind hota hai — internet pe expose nahi hota
- Isme **koi login nahi hai** (local tool hai). Isliye `0.0.0.0` pe kabhi mat chalana
- Media serving mein path-traversal check hai (`../../etc/passwd` block hota hai)
- Test suite ye teeno cheezein enforce karti hai

### Phase 4 ke errors

| Error | Matlab | Fix |
|---|---|---|
| `Address already in use` | Port 8765 pehle se busy hai | `python3 -m web.server --port 8766` |
| Dashboard khaali dikhta hai | DB mein koi video nahi | `python3 run.py` chalao |
| Video play nahi hota | `final.mp4` missing | `python3 run.py --render-only <id>` |
| `PLACEHOLDER_IMAGES` FATAL | Image API fail hui thi | Net check karke dobara banao |
| `SILENT` FATAL | TTS fail hua tha | `narration.mp3` sun kar dekho, `pip install edge-tts` |

---

---

## 📸 PHASE 6 — INSTAGRAM

### ⚠️ Pehle ye samajh lo — 2 cheezein jo YouTube se BILKUL alag hain

**1. Instagram local file upload NAHI leta.**
Tum sirf ek `video_url` bhejte ho aur **Meta ke server khud usse download karte hain**.
Matlab video ko pehle internet pe kahin public host karna padega. Isliye
`core/hosting.py` banaya.

**2. Container 24 ghante mein expire hota hai.**
Isliye pehle se container bana kar schedule **nahi** kar sakte. Schedule apni DB
mein rakho, aur **publish time pe hi** container banao (3-5 min pehle).

---

## STEP 6b — Video hosting setup (GitHub Releases, 5 minute)

Sabse accha free option: **GitHub Releases** — 2 GB per file, unlimited bandwidth,
CDN pe serve hota hai, permanently free.

1. GitHub pe ek repo banao (**private bhi chalega** — releases phir bhi public rehte hain)
2. [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)**
3. Scope mein **`repo`** tick karo → Generate → token copy karo (`ghp_...`)
4. `.env` mein daalo:
```bash
PUBLIC_HOST_MODE=github_release
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPO=tumhara-username/tumhara-repo
```

**Test karo:**
```bash
python3 -m agents.ig_publisher 1 --host-only
```
Ek URL print hoga. Usse browser mein kholo — video **seedha download/play** hona chahiye.

> ⚠️ **Google Drive aur Dropbox ke normal share links KAAM NAHI karte.** Wo ek HTML
> page dete hain, video file nahi. Code ye pakad leta hai aur saaf batata hai.

**Doosre options:** `PUBLIC_HOST_MODE=catbox` (koi account nahi, par volunteer-run
service hai — maine test kiya to datacenter IP se `412` diya), ya `manual`
(tum khud upload karke URL do).

---

## STEP 6c — Instagram credentials (token + account ID)

**Pehle ye teen cheezein honi chahiye** (STEP 6 mein likhi hain):
- Instagram account **Business ya Creator** pe switched
- Ek **Facebook Page** se linked
- developers.facebook.com pe ek **Business type** app + Instagram Graph API product

Ab token nikalo:

1. [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer) kholo
2. Upar right mein apna **app** select karo
3. **Add a Permission** mein ye 4 tick karo:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_insights`
   - (aur `pages_show_list`, `pages_read_engagement`)
4. **Generate Access Token** → login → Allow
5. Ye short-lived token hai (1 ghanta). Isse **long-lived** (60 din) banao:

```bash
curl -s "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN"
```

6. Ab apna **Instagram Business Account ID** nikalo:

```bash
# pehle Page ID:
curl -s "https://graph.facebook.com/v21.0/me/accounts?access_token=LONG_TOKEN"

# phir us Page se IG account ID:
curl -s "https://graph.facebook.com/v21.0/PAGE_ID?fields=instagram_business_account&access_token=LONG_TOKEN"
```

7. `.env` mein daalo:
```bash
IG_LONG_LIVED_TOKEN=EAAxxxxxxxx
IG_BUSINESS_ACCOUNT_ID=17841400000000000
```

**Verify karo:**
```bash
python3 -m agents.ig_publisher --info
```
Tumhara username, followers count, aur `account_type: BUSINESS` dikhna chahiye.

> ⚠️ **Long-lived token 60 din chalta hai.** Calendar mein reminder laga lo.
> Expire hone pe `code 190` error aayega — code tumhe saaf batayega.

---

## Instagram pe publish karo

```bash
python3 -m agents.ig_publisher 1 --dry-run    # pehle hamesha ye
python3 -m agents.ig_publisher 1              # asli publish
python3 -m agents.ig_publisher --limit        # Meta ka apna posts counter
```

**Kya hota hai (3 steps):**
```
1. Video GitHub Release pe upload  →  public URL
2. POST /media  →  container ID
3. Poll /{container}?fields=status_code  →  FINISHED hone tak (30s - 5 min)
4. POST /media_publish  →  live!
5. First comment post
```

### 4 gates (YouTube jaise hi)
```
APPROVAL → FILE → VALIDATE (+90s check) → QUOTA (cap 20/24h)
```

### Phase 6 ke errors

| Error | Matlab | Fix |
|---|---|---|
| **`code 24`** | **Format reject** | `python3 -m pipeline.validate` — wo pehle hi pakad leta hai |
| `code 190` | Token expire (60 din ho gaye) | STEP 6c dobara — naya long-lived token |
| `code 200` | Permission nahi | App Review approve hua? Ya tum test user ho? |
| `code 9` / `2207042` | Publishing rate limit | `--limit` se check karo, kal try karo |
| `2207052` | Meta video URL fetch nahi kar paaya | URL browser mein khol kar dekho |
| `2207026` | Format supported nahi | H.264 + AAC + 9:16 + <90s |
| Container `ERROR` status | Meta ne video reject kiya | validate chalao, URL check karo |
| Container 5 min mein FINISHED nahi | Meta slow ya video bada | Thodi der baad manually publish (container 24h valid hai) |
| `Personal account` wali error | Account Business/Creator nahi hai | Instagram app → Settings → Account type |

### 📊 Rate limit — polling bhi ginti hai

Instagram: **200 calls/hour** per user+app. **Container polling bhi isi mein ginta hai.**
Ek publish mein ~8-12 calls lagte hain (container + polls + publish + permalink + comment).

Code do tarah se track karta hai:
1. Apna counter (`quota.py`, cap **150/hour** — 200 se safe margin)
2. Meta ke **`X-App-Usage`** headers har response se — 80% cross ho to warning
3. **`content_publishing_limit`** endpoint se Meta ka apna posts counter, jisse
   hum apna DB reconcile karte hain

---

---

## 🔬 PHASE 7 — ANALYST

```bash
python3 -m agents.analyst                  # briefing (plain Hinglish)
python3 -m agents.analyst --due            # kya metrics due hain
python3 -m agents.analyst --run            # jo due hai wo kheencho (cron isse chalayega)
python3 -m agents.analyst --analyze 1      # ek video ka poora analysis
python3 -m agents.analyst --variables      # kaunsa hook/voice/template jeet raha
```

### Kab kya kheencha jaata hai

| Window | Kab | Kyun |
|---|---|---|
| **2h** | publish ke 2 ghante baad | ⭐ **VELOCITY WINDOW — yahi decisive hai.** 2 ghante mein algorithm decide kar leta hai. Iske baad growth sirf spillover hai |
| 24h | 1 din baad | asli performance |
| 7d | 1 hafte baad | long tail |

2h wala data aate hi **turant analysis** chalta hai.

### Kya nikalta hai — example output

```
Video #13 (2h): KAMZOR (-68% vs baseline) — retention threshold miss.
Kyunki views baseline se -68% neeche;
retention 41% hai, 28s video ke liye 65% chahiye — isse neeche distribution ruk jaati hai;
1-second retention sirf 62% — pehla frame aur pehli line kaam nahi kar rahe;
zero comments — comment bait kaam nahi kar raha;
sabse bada drop 1.4s pe (31% viewers gaye).
```

Ye exactly wo hai jo chahiye tha: **"X% baseline se neeche, KYUNKI ___"**

### Retention thresholds (Section 3 se)

| Platform | Threshold | Neeche gaye to |
|---|---|---|
| YouTube, **sub-30s** video | **65%** | distribution ruk jaati hai |
| YouTube, **30-60s** video | **50%** | distribution ruk jaati hai |
| Instagram, **3-second** | **60%** | distribution band |
| YouTube **1-second** | 75%+ chahiye | ye YT ka **sabse bada** signal hai |

### Flags jo lag sakte hain

| Flag | Matlab | Kya karo |
|---|---|---|
| `RETENTION_BELOW_THRESHOLD` | Threshold miss | Script chhoti karo, pacing tez karo |
| `WEAK_FIRST_SECOND` | Pehla frame/line fail | ArtDirector se brighter pattern-interrupt, Writer se stronger hook |
| `EARLY_DROPOFF` | 3s se pehle bade log gaye | Hook promise deliver nahi kar raha |
| `WEAK_3S` | IG ka gate miss | Pehle 3 second mein visual hook |
| `NO_COMMENTS` | Comment bait fail | Zyada specific sawaal poochho |

### Quota discipline

`search.list` **kabhi nahi** (100 units). Sirf `videos.list` (**1 unit**) —
100× sasta. Test isse enforce karta hai.

YouTube **Analytics API** ka apna alag quota hai (Data API ke 10,000 units se
alag) — retention curve wahan se aati hai.

### Phase 7 ke errors

| Error | Matlab | Fix |
|---|---|---|
| `yt-analytics.readonly scope chahiye` | Phase 7 mein naya scope add hua | `rm token.json && python3 authorize_youtube.py` |
| `Analytics 403` | Channel ka data abhi ready nahi | Analytics 24-48h leta hai naye channel pe |
| `Baseline abhi nahi bana` | 3 se kam videos ki metrics hain | Aur videos publish karo |
| IG insights khaali | Reel bahut naya hai | Kuch ghante ruko |

---

---

## 🧪 PHASE 8 — SCIENTIST (ye tumhara asli moat hai)

```bash
python3 -m agents.scientist                # report
python3 -m agents.scientist --suggest      # ab kya test karna chahiye
python3 -m agents.scientist --start        # experiment shuru (auto-pick)
python3 -m agents.scientist --start --variable voice_id
python3 -m agents.scientist --status       # chal rahe experiment ka haal
python3 -m agents.scientist --conclude     # khatam karo + learning save
python3 -m agents.scientist --champions    # abhi kaun jeeta hua hai
```

Dashboard pe bhi buttons hain — **🧪 Experiment shuru karo** aur **🏁 Conclude**.

### Loop kaise chalta hai

```
1. SUGGEST   Scientist khud decide karta hai ab kya test karna chahiye
                (jo variable kabhi test nahi hua > jiski learning 90 din purani
                 ho gayi > jiska result kamzor tha)
2. START     Ek experiment. Ek variable. Arm A (champion) vs Arm B (challenger)
3. ASSIGN    Har naya video A, B, A, B... — ALTERNATE, random nahi
4. EVALUATE  5 videos per arm ke baad Welch's t-test
5. CONCLUDE  Significant hua to learning DB mein save
6. APPLY     Writer/Voice/ArtDirector agli baar champion ko prefer karte hain
```

### Asli test ka output (maine 10 videos simulate kiye)

```
🧪 EXPERIMENT #1  — hook_type
   Arm A: specific_outcome (champion)   Arm B: pov (challenger)
   ⚠️ Is sample size pe sirf ~75%+ ka farq detect ho payega.

... 10 videos, alternate assignment ...

'pov' ne 'specific_outcome' se +61% behtar kiya (1437 vs 894 views @2h).
p=0.00038 matlab 99.96% chance ye asli farq hai, luck nahi. Confidence: medium (n=5+5).
➜ 'pov' ko prefer karo, par 'specific_outcome' ko rotation mein rehne do — sample chhota hai.

✅ Learning save hui: hook_type — 'pov' jeeta (+61%, p=0.00038, medium)
```

Phir Writer apne aap `pov` ko **32-38%** share dene lagta hai (100% nahi — neeche padho).

### ⚠️ Statistics — maine yahan shortcut NAHI liya

**Problem:** n=5 per arm bahut chhota sample hai. Normal distribution (z-test)
use karo to p-value **jhooth** bolta hai — accha dikhata hai jabki farq luck ho
sakta hai. Phir hum galat "learning" save kar dete aur wo permanently
content bigaad deti.

**Jo kiya:** proper **Welch's t-test** + asli **t-distribution** ka p-value.
Python stdlib mein t-distribution nahi hai aur scipy 60 MB ka package hai —
isliye incomplete beta function khud implement kiya (`core/stats.py`, ~50 line
of textbook math). **Numerical integration se verify kiya — 8 decimal places
tak sahi.**

Welch's kyun (Student's nahi)? Dono arms ka variance alag hota hai — ek hook
consistent chalti hai, doosri hit-or-miss. Welch isse handle karta hai.

### Confidence — sirf p-value pe nahi

| Level | Kab milti hai |
|---|---|
| **high** | p<0.05 **AND** n≥8 per arm **AND** effect bada (Cohen's d ≥ 0.5) |
| **medium** | p<0.05 **AND** n≥5 |
| **low** | baaki sab |

**n=5 pe kabhi 'high' nahi milti**, chahe p-value kitna bhi accha ho.

Aur har experiment **MDE (minimum detectable effect)** bhi batata hai:
> *"Is sample size pe sirf ~75%+ ka farq detect ho payega. Chhota farq dikhega hi nahi."*

Ye imandari zaroori hai — warna tum 10% ka asli improvement dhoondhte rahoge
jo is sample size pe kabhi dikhega hi nahi.

### Learning loop — jeete hue variants default ban jaate hain

| Confidence | Winner ko | Loser ko |
|---|---|---|
| **high** | 4× weight (~38% share) | 0.15× (lagbhag hata diya) |
| **medium** | 4× weight (~32% share) | rotation mein rehta hai |
| **low** | kuch nahi | kuch nahi |

⚠️ **Champion ko 100% share kabhi nahi milta.** Kyunki same hook + same voice
har video mein = **duplicate-pattern clustering** = YouTube throttle. Test isse
enforce karta hai (`champion < 40/50`).

### Imandari ka sabse bada test

Agar dono arms mein koi significant farq **nahi** mila, to:
```
NO WINNER — koi significant farq nahi (p=0.42).
Koi learning save nahi hui. Ye theek hai: jhoothi learning
save karne se accha kuch na save karna.
```
Learning DB **khaali** rehti hai. Ye feature hai, bug nahi.

### Phase 8 ke errors

| Message | Matlab | Kya karo |
|---|---|---|
| `Experiment #N pehle se chal raha hai` | Ek time pe ek hi variable | Pehle usse conclude karo |
| `Abhi data kam hai: A=2/5, B=3/5` | Sample chhota | Aur videos publish karo |
| `ABANDONED — data kam tha` | Force conclude kiya | Normal hai, koi learning save nahi hui |
| `Koi experiment suggest nahi hai` | Sab variables test ho chuke | 90 din baad re-test suggest hoga |

---

---

## ⏰ PHASE 9+10 — CHIEF (autonomous scheduler + loop closure)

```bash
python3 -m agents.chief --tick --dry-run   # kuch badlega nahi, sirf batayega
python3 -m agents.chief --tick             # ek asli cycle
python3 -m agents.chief --digest           # daily briefing
python3 -m agents.chief --install-cron     # cron setup guide
python3 -m agents.chief --loop 60          # cron ke bina, har 60 min (testing)
```

Dashboard pe bhi **⏰ Run tick** button hai.

### Ek "tick" mein kya hota hai

```
1. METRICS     jo videos ki 2h/24h/7d metrics due hain, kheencho
                  (2h sabse pehle — velocity window miss nahi hona chahiye)
2. EXPERIMENT  data kaafi hai to conclude karo + learning save
                  koi experiment nahi chal raha to naya shuru karo
3. PUBLISH     approved video, peak window (±45 min) mein, quota check ke saath
4. PRODUCE     aaj ka target poora nahi hua to naya video banao
                  + naye video ko experiment mein assign karo
5. CLEANUP     purani learnings downgrade, rejected videos ki files delete
```

**Order maayne rakhta hai:** pehle data lo → phir seekho → phir publish → phir naya banao.
Test isse enforce karta hai.

### Har step khud decide karta hai

| Kab kya nahi hota | Kyun |
|---|---|
| Target poora ho gaya | `videos_per_day` limit |
| Approve queue mein 5+ pending | Backlog banane ka fayda nahi |
| Publish window nahi hai | Peak time pe hi publish (velocity engineering) |
| Quota khatam | Graceful — kal ho jayega, crash nahi |
| `review_first` mein approve nahi hua | Insaan ka gate |
| 4 se kam published videos | Experiment ka matlab nahi |

### 🔒 Lock — double-run se bachav

Do chief ek saath chal jayein to **double publish** ho jayega (quota + reputation
dono ka nuksaan). Isliye lock file hai. Process crash ho jaye to 90 min baad
lock apne aap hat jaata hai.

### Ek task fail ho to baaki chalte rahenge

Har task apne `try/except` mein hai. YouTube down ho to bhi metrics collect
honge, videos banenge. Har failure DB mein log hota hai aur digest mein dikhta hai.

---

## 📋 DAILY DIGEST

```bash
python3 -m agents.chief --digest
```

```
╔════════════════════════════════════════════════════════════════╗
║ 🎬 AUTOPILOT — DAILY DIGEST — 29 Jul 2026, 08:00 IST           ║
╚════════════════════════════════════════════════════════════════╝

Mode: review_first  (tum approve karoge, tabhi publish hoga)

─── 📦 PRODUCTION ───
  Aaj bane      : 1/2
  Approve queue : 2  ← dashboard pe review karo
  Published     : 14 total

─── 📊 PERFORMANCE ───
  Baseline (2h, n=12): 940 views, retention 58%
  • Video #14 (2h): ACCHA (+34% vs baseline). Kyunki retention 71% ✅ ...

─── 🧪 SCIENCE ───
  Experiment #3: voice_id — hi_f_calm vs hi_f_urgent
  ➜ Abhi data kam hai: A=3/5, B=2/5
  Champions (default ban chuke hain):
    hook_type      = pov                +61% (n=8, high)

─── 📉 QUOTA ───
  youtube_uploads   ██░░░░░░░░     1/5      reset 9h 12m baad

─── ✅ TUMHE KYA KARNA HAI ───
  □ 2 videos approve queue mein hain — dashboard pe review karo
```

Aakhri section sabse zaroori hai — **wahi batata hai ki tumhe kya karna hai.**
Kuch nahi karna ho to likha aata hai: *"Kuch nahi! Sab apne aap chal raha hai. ☕"*

---

## 🔁 STEP 7 — CRON LAGAO (roz apne aap chalne ke liye)

```bash
python3 -m agents.chief --install-cron
```
Ye tumhare system ke hisaab se exact commands print karega.

**Linux/Mac:**
```bash
crontab -e
```
Ye 2 lines daalo:
```
0 * * * * cd /path/to/autopilot && /usr/bin/python3 -m agents.chief --tick >> logs/cron.log 2>&1
0 8 * * * cd /path/to/autopilot && /usr/bin/python3 -m agents.chief --digest >> logs/digest.log 2>&1
```

**Windows:** Task Scheduler → Basic Task → repeat every 1 hour → program `python`,
arguments `-m agents.chief --tick`, start-in = project folder.

### ⚠️ Instagram wali zaroori baat

IG ka container 24 ghante mein expire hota hai, isliye **pehle se schedule
karna possible hi nahi**. Matlab **machine chalu rehni chahiye**, warna IG post
nahi jayega.

YouTube mein ye problem nahi — `publishAt` server-side hai, ek baar upload ho
gaya to YouTube khud time pe public kar dega.

Laptop roz band karte ho? Ek free VPS (Oracle Cloud free tier) ya Raspberry Pi
behtar rahega.

---

## 🔁 LEARNING LOOP — ab band ho chuka hai

```
    Publish
       ↓
    2h metrics (velocity window)  ──→  dead hai to KYUN?
       ↓
    24h + 7d metrics
       ↓
    Analyst: retention, drop-off, kaunsa variable
       ↓
    Scientist: A/B experiment (auto-start, auto-conclude)
       ↓
    Learning DB: "pov ne question se +61% better kiya, n=10, medium"
       ↓
    Writer / Voice / ArtDirector agli baar ye padhte hain   ← ⭐ LOOP CLOSED
       ↓
    Loop
```

Maine ye poora loop test kiya (`test_all.py` mein "POORA LOOP" test):
6 seed videos → Chief khud experiment shuru karta hai → 10 videos assign hote
hain → Chief khud conclude karta hai → learning save hoti hai → Writer champion
ko **33-38% share** dene lagta hai.

**Champion ko 100% kabhi nahi milta** — same hook har video mein =
duplicate-pattern clustering = throttle. Ceiling jaan-boojh kar hai.

---

## ☀️ ROZ KA ROUTINE (system chalne ke baad)

**Subah (2 minute):**
1. Digest padho (email/log mein aa jayega)
2. "TUMHE KYA KARNA HAI" section dekho

**Jab approve queue mein videos hon (5 minute):**
1. `python3 -m web.server`
2. Har video dekho → **Approve** ya **Reject** (reject pe reason likhna — wo learning banta hai)

**Hafte mein ek baar:**
- `python3 -m agents.scientist` — experiment kahan tak pahuncha
- Pehle 20 videos publish ho gaye? `config.yaml` mein `autonomy: auto_publish` kar do

**Mahine mein ek baar:**
- Instagram token 60 din mein expire hota hai — renew karo (STEP 6c)

---

---

## 🔍 TRENDSCOUT — topics ab asli data se aate hain

```bash
python3 -m agents.trendscout              # report
python3 -m agents.trendscout --scout      # 5 topic candidates + score
python3 -m agents.trendscout --patterns   # apne data ke patterns
python3 -m agents.trendscout --sync       # YouTube se data (sirf 3 units)
python3 -m agents.trendscout --best       # ek best topic
```

Pehle topics ek hardcoded list se aate the. Ab teen source hain:

| Source | Kya |
|---|---|
| **Apna data** | Jo topics chale, unke keywords nikalte hain. Jo nahi chale, unke keywords hata diye jaate hain |
| **Series** | `Case #1, #2, #3...` — Section 8 ka binge behaviour. Title mein number dikhta hai |
| **LLM** | Niche ke andar naye clusters, winners ke patterns + learnings ke saath |

### ⭐ Quota math — yahi is agent ka poora design hai

```
search.list         = 100 units/call   ← ek call = 100 din ka apna data
playlistItems.list  =   1 unit/call    ← 100x sasta
videos.list         =   1 unit/call
```

`--sync` apne channel ka **poora data 3 units** mein le aata hai:
`channels.list` (1) → `playlistItems.list` (1) → `videos.list` (1).
`search.list` se yahi kaam 100 units leta.

**Test enforce karta hai ki `search.list` kahin use hi na ho.**

### Score kaise nikalta hai

| Signal | Effect |
|---|---|
| Winner keyword match | +0.07 per hit (max +0.20) |
| Series continuation | +0.15 |
| Concrete number (`14 log`) | +0.10 |
| Topic 6-16 shabd | +0.05 |
| Topic 22+ shabd | −0.10 (32s mein nahi aayega) |

**⚠️ Ye ek HEURISTIC hai, ML model nahi.** Aur code ye chhupata nahi:
jab data kam ho to score **0.5 (neutral) ki taraf khisak jaata hai** —
kyunki bina data ke confident hona jhooth hai.

```
n=0  videos → score 0.51   (lagbhag andaaza)
n=5  videos → score 0.68   (keyword match ke saath)
n=30 videos → score asli patterns pe
```

### Example — asli data ke saath

```
Apna data: 5 videos (confidence: medium), avg 2h views: 1790

Jo chala:  ✅ Wo train jo gayab ho gayi
Jo nahi:   ❌ Ek gaon ki kahani
Winners ke keywords: train, gayab

Agle topic candidates:
  0.65 [series]  Case #5: Wo 14 log jo ek raat mein gayab ho gaye
  0.57 [llm]     Wo 7 log jo ek hi raat mein gayab ho gaye
```

Dhyaan do: `rahasya` jaisa shabd jo **winners aur losers dono** mein ho, wo
keyword list se **hat jaata hai** — kyunki wo koi signal nahi deta.

---

## 🔍 Trade-offs — jahan shortcut liya

Jhoot nahi bolunga, ye limitations hain:

1. **`config.py` ka mini-YAML parser sirf flat `key: value` samajhta hai.**
   Nested config (list/dict) chahiye to `pip install pyyaml` — code apne aap
   use kar lega. Abhi zaroorat nahi.

2. **`quota.py` ka `rolling_24h` window approximate hai.** Hum apne DB se ginte hain,
   Meta ke server se nahi. Isliye cap 20 rakha hai (asli 50-100) — drift ka gap
   safe margin kha jaata hai. `reconcile_from_headers()` asli % se milaata rehta hai.

3. **Quota state hamare SQLite mein hai, Google ke paas nahi.** Agar tum manually
   API console se calls karo, ya DB delete kar do, to hisaab galat ho jayega.
   Isliye `data/autopilot.db` delete mat karna.

4. **MockLLM ka output ghisa-pita hai** — same 3 templates. Wo sirf pipeline test
   karne ke liye hai, publish karne ke liye **nahi**. Phase 2 se pehle Gemini key le lena.

5. **Parallax "asli" nahi hai.** Section 5 ne foreground/background alag speed
   maanga tha. Asli parallax ke liye har image ko depth-map se 2 layers mein todna
   padta — wo ek aur AI model chahiye jo ₹0 mein nahi hai. **Jo kiya:** alternate
   scenes pe motion speed 50% kar di, jisse rhythm mein variation aata hai.
   Farq dikhta hai, par ye 3D parallax nahi hai.

6. **Instagram scheduling "asli" nahi hai.** Container 24h mein expire hota hai,
   isliye pehle se container bana kar schedule karna possible hi nahi. Schedule
   hamari DB mein rehta hai aur Phase 9 ka scheduler publish time pe container
   banayega. Matlab **scheduler chalu rehna chahiye** (cron), warna scheduled
   post nahi jayega. YouTube mein ye problem nahi (wahan `publishAt` server-side hai).

7. **Instagram per-second retention curve NAHI deta.** YouTube deta hai
   (`audienceRetention` report), Instagram nahi. IG ke liye hum
   `ig_reels_avg_watch_time` se average nikalte hain aur `ret_3s` estimate karte
   hain. Matlab IG ka drop-off point exactly pata nahi chalta — sirf overall
   average. Ye Meta ki API ki limitation hai, hamari nahi.

8. **Variable report CORRELATION hai, causation nahi.** Agar `pov` hook wale
   videos zyada chale, ho sakta hai unke topics hi behtar the. Isliye Phase 8
   ka Scientist proper A/B karta hai — ek time pe ek variable, min 5 per arm.

9. **A/B experiments DHEERE hote hain.** 5 videos per arm × 2 arms = 10 videos.
   2 videos/day pe **5 din per experiment**. Ek saal mein ~70 experiments — jo
   theek hai, par ye instant nahi hai. Aur `videos_per_day` badhane se
   clustering ka risk badhta hai, isliye jaldi karne ka koi shortcut nahi hai.

10. **Cron chalu rehna zaroori hai (IG ke liye).** Container 24h mein expire
    hota hai, isliye machine band = IG post nahi. YouTube safe hai.

11. **Chief ek tick mein sirf 1 video banata hai.** 2 videos/day chahiye to
    cron 2 baar peak window mein chalega. Ek saath 2 banane se machine pe
    load aur ffmpeg timeout ka risk badhta hai.

12. **TrendScout koi "trending topics API" use nahi karta.** Google Trends,
    TikTok Creative Center — sab ya paid hain ya scraping (jo ToS violation
    aur ban risk hai). Isliye topics apne data ke patterns + LLM se aate hain.
    Matlab: **naye channel pe TrendScout lagbhag LLM hi hai** — asli power
    tab aati hai jab 10+ videos ka data ho.

13. **Predicted score ek heuristic hai.** Weights maine research ke hisaab se
    set kiye (concrete numbers, series, length), par wo tune nahi hue hain.
    Asli tuning tabhi possible hai jab 50+ videos ka data ho.

14. **Ek time pe ek hi variable test hota hai.** Multivariate testing (2 variables
    ek saath) fast hota par uske liye 4 arms chahiye = 20 videos = 10 din, aur
    interaction effects samajhna chhote sample pe possible nahi. Isliye
    jaan-boojh kar simple A/B rakha.

9. **Catbox hosting reliable nahi hai.** Maine test kiya — datacenter IP se `412`
   deta hai. Wo ek volunteer-run free service hai. `github_release` use karo.

8. **Har cut pe whoosh ek jaisa hai.** Brown noise se banta hai. Alag-alag
   whoosh chahiye to `assets/music/` mein apne free SFX daal sakte ho
   (freesound.org pe CC0 wale) — par phir wo "generated" nahi rahega, licence
   check karna padega.

---

## ▶️ Agla kadam

Ye 3 cheezein karo, phir Phase 2 bolo:

1. `python3 test_all.py` → 260 green dekho
2. `config.yaml` mein `brand_name` bharo
3. `python3 run.py` chalao aur **video dekho**
4. **Instagram App Review submit karo** (STEP 6) — ye 2-4 hafte lega, aaj hi shuru karo

**Ab kya?** Neeche "ROZ KA ROUTINE" section dekho. System taiyaar hai —
ab isse asli data chahiye. Publish shuru karo.
