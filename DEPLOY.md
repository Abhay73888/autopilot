# 🔐 SECURITY + 🚀 DEPLOYMENT — tumhare 2 sawaalon ka jawab

---

# PART 1 — "Kya mujhe Instagram ka ID/password dena hoga?"

## ❌ NAHI. Kabhi nahi. Aur ye bahut important hai.

**Tumhara Instagram password. Tumhara YouTube password. Tumhara Google password.
In teeno mein se KOI BHI is system ko nahi dena hai.**

Maine code check kiya — kahin bhi password maanga hi nahi jaata:

```bash
grep -rn "getpass\|password" *.py core/ agents/
# → sirf comments mein, koi input field nahi
```

## Toh phir kaam kaise karta hai? — OAuth aur Tokens

Sochо ki tumhare ghar ki **master chaabi** tumhara password hai. Wo kisi ko nahi dete.
Uski jagah tum ek **duplicate chaabi** banate ho jo sirf ek darwaza kholti hai,
aur jab chaaho usse cancel kar sakte ho. Wahi "token" hai.

### YouTube pe kya hota hai

```
1. Tum `python authorize_youtube.py` chalate ho
2. Tumhara BROWSER khulta hai — google.com pe
3. Tum GOOGLE KI WEBSITE pe apna password daalte ho
   ⚠️ Ye page Google ka hai, mera nahi. Password Google ke server pe jaata hai.
4. Google poochta hai: "AUTOPILOT ko video upload karne ki permission do?"
5. Tum "Allow" dabate ho
6. Google ek TOKEN deta hai → wo token.json mein save hota hai
```

**Tumhara password kabhi is computer pe type hi nahi hota.** Wo Google ke
page pe jaata hai. Code sirf token dekhta hai.

Token mein kya-kya kar sakte ho:
- ✅ Video upload
- ✅ Analytics padhna
- ✅ Comment post karna
- ❌ Password badalna
- ❌ Account delete karna
- ❌ Email padhna
- ❌ Paise nikalna
- ❌ Koi doosri Google service

**Kabhi bhi cancel kar sakte ho:** [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
→ AUTOPILOT → **Remove Access**. Token turant mar jaata hai.

### Instagram pe kya hota hai

Aur bhi safe. Tum **Facebook Developer** site pe jaate ho, wahan se ek
**Access Token** copy karte ho, aur usse `.env` file mein paste karte ho.

Instagram ka password kahin aata hi nahi. Token mein sirf 4 permissions hain:
`instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`,
`instagram_manage_insights`.

Cancel karna: Instagram app → Settings → Apps and Websites → Remove.

## Ek line mein

| Cheez | Dena hai? |
|---|---|
| Instagram password | ❌ **KABHI NAHI** |
| YouTube/Google password | ❌ **KABHI NAHI** |
| Gemini API key | ✅ (free key, aistudio se) |
| YouTube OAuth token | ✅ (browser se khud banta hai) |
| Instagram access token | ✅ (Facebook developer site se) |
| GitHub token | ✅ (video hosting ke liye) |

Saare tokens **cancel-able** hain, **limited-permission** wale hain, aur
**tumhare apne computer** pe rehte hain.

## ⚠️ Agar koi tumse Instagram password maange — wo SCAM hai

Bahut saare "auto-posting tools" password maangte hain. Wo:
- Tumhara account chura sakte hain
- Instagram unhe detect karke **tumhara account ban** kar deta hai
- Password change karo to unka tool band ho jaata hai (matlab wo password store kar rahe the)

Meta ne isliye hi official API banayi hai. Hum wahi use kar rahe hain.

---

# PART 2 — "GitHub pe push karke deploy karun to chalne lagega?"

## ⚠️ Half sach. Push karo — haan. Par 3 cheezein pehle samajh lo.

### ❌ Galatfehmi 1: "Deploy karne se apne aap chalne lagega"

Ye ek **normal website nahi** hai. Ye ek **background worker** hai.

| Website (Vercel/Netlify) | AUTOPILOT |
|---|---|
| Koi visit kare tab chalti hai | Har ghante khud chalta hai |
| Har request 10 second mein khatam | Ek video 5-6 minute leta hai |
| Kuch store nahi karti | SQLite DB + video files |
| CPU chhota | ffmpeg ko asli CPU chahiye |

**Vercel, Netlify, GitHub Pages pe ye NAHI chalega.** Wo serverless hain —
wahan 10-60 second ke baad process mar jaata hai, aur ffmpeg install hi nahi hota.

### ❌ Galatfehmi 2: "GitHub pe push karne se deploy ho jaayega"

GitHub sirf **code rakhne** ki jagah hai. Wo code **chalata nahi**.
Deploy ek alag step hai.

### 🚨 Galatfehmi 3 (SABSE KHATARNAK): ".env bhi push ho jaayegi"

**Agar tumhare tokens GitHub pe chale gaye to:**
- Bots 60 second ke andar public GitHub scan karke tokens chura lete hain (ye sach hai, ye roz hota hai)
- Koi tumhare channel pe kuch bhi upload kar sakta hai
- Google/Meta token detect karke **turant kill** kar dete hain

**Maine `.gitignore` pehle se bana rakhi hai** — `.env`, `token.json`,
`client_secret.json` sab blocked hain. Par **push karne se pehle khud verify karo**
(neeche STEP 2 mein bataya hai).

---

## ✅ SAHI TAREEKA — 5 steps

### STEP 0 — Pehle apne laptop pe 1 hafta chalao

**Deploy ki jaldi mat karo.** Pehle ye karo:

```bash
python3 run.py                    # 5-10 videos banao
python3 -m web.server             # dekho, approve/reject karo
python3 -m agents.publisher 1     # ek video private upload karo
```

Jab tak tum khud 10 videos dekh nahi lete, deploy karne ka matlab nahi —
kyunki tumhe pata hi nahi hoga ki content acha hai ya nahi.

**Deploy tabhi karo jab:**
- [ ] 10+ videos ban chuke hon aur tumhe pasand aaye hon
- [ ] YouTube pe 2-3 upload ho chuke hon (private mein)
- [ ] Instagram App Review approve ho chuka ho
- [ ] Tum `python3 -m agents.chief --tick` roz manually chala chuke ho

---

### STEP 1 — Git repo banao

```bash
cd autopilot
git init
git add .
git commit -m "AUTOPILOT initial"
```

---

### STEP 2 — 🚨 SECRETS CHECK (ye step SKIP MAT KARNA)

```bash
git status --porcelain
```

**In teen naamon mein se koi bhi list mein NAHI dikhna chahiye:**
- `.env`
- `token.json`
- `client_secret.json`

Double-check:
```bash
git ls-files | grep -E "\.env$|token\.json|client_secret"
```
👉 **Output khaali hona chahiye.** Kuch bhi aaye to `.gitignore` check karo.

Teesra check — commit ke andar tokens to nahi?
```bash
git grep -iE "AIza|ghp_|EAA[A-Za-z0-9]{20}" $(git rev-parse HEAD) || echo "✅ SAAF"
```

**Agar galti se push ho gaya:** file delete karna kaafi NAHI hai (history mein
rehti hai). Turant:
1. Google: [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → Remove
2. Meta: developers.facebook.com → app → token invalidate
3. GitHub: settings/tokens → Delete
4. Naye tokens banao
5. Repo **delete** karke naya banao

---

### STEP 3 — Repo PRIVATE rakho

```bash
gh repo create autopilot --private --source=. --push
```

Ya github.com pe manually — **"Private" select karo**.

Public kyun nahi? Kyunki:
- Galti se token push hone ka risk (private mein bot scan nahi karte)
- Tumhara content strategy publicly visible ho jaayega

---

### STEP 4 — Kahan deploy karein

#### 🥇 Option A: Apna purana laptop / PC (BEST, ₹0)

Sach mein sabse accha option. Koi purana laptop ghar pe pada hai? Bas usse
chalu rehne do.

```bash
# Linux/Mac
crontab -e
0 * * * * cd /home/tum/autopilot && /usr/bin/python3 -m agents.chief --tick >> logs/cron.log 2>&1
0 8 * * * cd /home/tum/autopilot && /usr/bin/python3 -m agents.chief --digest >> logs/digest.log 2>&1
```

**Laptop sleep na ho:**
- Windows: Settings → Power → Sleep = **Never**
- Mac: `sudo pmset -a sleep 0` (ya `caffeinate -s`)
- Ubuntu: Settings → Power → Automatic Suspend = Off

**Fayda:** ₹0, poora CPU, koi limit nahi
**Nuksaan:** bijli jaaye ya net jaaye to ruk jaata hai

---

#### 🥈 Option B: Oracle Cloud Free Tier (₹0, hamesha free)

Oracle **"Always Free"** deta hai — trial nahi, hamesha ke liye:
- 4 CPU cores (ARM), 24 GB RAM 😮
- 200 GB storage

Ye AUTOPILOT ke liye **overkill** hai. ffmpeg easily chalega.

```bash
# 1. cloud.oracle.com pe signup (card verification lagta hai, charge nahi hota)
# 2. Create VM → Ampere A1 (ARM) → Ubuntu 22.04 → 2 OCPU, 12 GB
# 3. SSH karo:
ssh ubuntu@<tumhara-ip>

# 4. Setup:
sudo apt update && sudo apt install -y python3-pip ffmpeg git
git clone https://github.com/tum/autopilot.git   # private repo = token maangega
cd autopilot
pip3 install -r requirements.txt

# 5. .env BANAO (git se nahi aayi — yahi to point hai)
nano .env      # tokens paste karo

# 6. YouTube authorize — ⚠️ server pe browser nahi hota!
#    Isliye pehle apne LAPTOP pe authorize karo, phir token.json copy karo:
#    (apne laptop se chalao)
scp token.json client_secret.json ubuntu@<ip>:~/autopilot/

# 7. Test:
python3 test_all.py
python3 -m agents.chief --tick --dry-run

# 8. Cron:
crontab -e
```

⚠️ **Oracle free VMs kabhi-kabhi "out of capacity" dete hain.** Ek-do din try
karte raho, mil jaata hai.

---

#### 🥉 Option C: Raspberry Pi (₹4000 ek baar)

Pi 4 (4GB) 24×7 chalta hai, 5 watt bijli (~₹40/mahina).
ffmpeg chalega par **dheema** — ek video 5 min ki jagah 12-15 min lega.
2 videos/day ke liye kaafi hai.

---

#### ❌ Ye MAT use karna

| Platform | Kyun nahi |
|---|---|
| Vercel / Netlify | Serverless — 10-60s timeout, ffmpeg nahi |
| GitHub Pages | Sirf static files, code chalta hi nahi |
| GitHub Actions | 6h limit + secrets rotation dikkat + ToS grey area |
| Heroku free | Free tier band ho chuka |
| Replit free | Sleep ho jaata hai, ffmpeg unreliable |
| Koi bhi ₹0 serverless | ffmpeg + SQLite + background = fit nahi hota |

---

### STEP 5 — Deploy ke baad

```bash
# 1. Sab kaam kar raha hai?
python3 test_all.py                          # 260 green

# 2. Preflight
python3 run.py --dry-run

# 3. Ek asli tick
python3 -m agents.chief --tick

# 4. Digest
python3 -m agents.chief --digest

# 5. Cron laga do
python3 -m agents.chief --install-cron       # exact commands print karega
```

**Dashboard server pe kholna ho (SSH tunnel se — safe tareeka):**
```bash
# apne laptop se:
ssh -L 8765:localhost:8765 ubuntu@<server-ip>
# phir browser mein: http://localhost:8765
```
⚠️ Dashboard ko kabhi `0.0.0.0` pe mat chalana — usme login nahi hai.

---

## 🔄 Code update kaise karein

```bash
# laptop pe
git add . && git commit -m "change" && git push

# server pe
cd autopilot && git pull && python3 test_all.py
```

`.env`, `token.json`, `data/autopilot.db` — ye kabhi overwrite nahi honge
(gitignore mein hain). Tumhara data safe rehta hai.

---

## 💾 Backup — ye ZAROOR karo

`data/autopilot.db` mein **saari learnings** hain. Wo gayi to system ka
poora "dimaag" gaya.

```bash
# cron mein ye bhi daal do — roz raat 2 baje backup
0 2 * * * cd /path/autopilot && cp data/autopilot.db data/backup-$(date +\%u).db
```
(`%u` = din ka number, matlab 7 din ka rotating backup)

---

## ✅ FINAL CHECKLIST

**Deploy se pehle:**
- [ ] Laptop pe 10+ videos bana ke dekhe
- [ ] `git ls-files | grep -E "\.env$|token\.json"` → **khaali**
- [ ] Repo **private** hai
- [ ] Instagram App Review approved
- [ ] `python3 test_all.py` → 260 green

**Deploy ke baad:**
- [ ] `.env` server pe manually banai (git se nahi aayi)
- [ ] `token.json` laptop se `scp` kiya
- [ ] `--tick` manually chala kar dekha
- [ ] Cron laga (tick + digest + backup)
- [ ] Machine sleep nahi hoti

**Roz:**
- [ ] Digest padho
- [ ] Approve queue clear karo

---

## 🎯 Sabse imaandar salaah

**Abhi deploy mat karo.**

Pehle 2-4 hafte apne laptop pe chalao. Kyunki:

1. **Instagram App Review** waise bhi 2-4 hafte lega — tab tak deploy ka fayda nahi
2. **Pehle 20 videos manually review karne hain** (`review_first` isliye default hai)
3. **Content tune karna padega** — hooks, voice, pacing. Server pe ye karna mushkil hai
4. **Server ka matlab tabhi hai jab system apne aap chal sake** — abhi wo stage nahi hai

Deploy ek **optimization** hai, requirement nahi. Laptop pe cron laga do,
wahi kaafi hai jab tak channel chal na pade.
