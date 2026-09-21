# AUTOPILOT AI AGENT POLICIES & CONSTRAINTS

## 🚨 PERMANENT USER RESTRICTION: COMMENTS SECTION MUST NEVER BE TURNED OFF
1. **Zero Comment Lock Policy:**
   - The comments section on ANY and ALL YouTube Shorts / Videos produced or uploaded by AUTOPILOT must ALWAYS be **100% ENABLED (ON)**.
   - It is strictly forbidden to disable, turn off, or restrict comments on any video.
2. **Metadata Flags Invariant:**
   - `selfDeclaredMadeForKids` must ALWAYS be `False`. Setting this to `True` disables comments on YouTube and is strictly prohibited.
   - `privacyStatus` must be `"public"` (or unlisted if staging, never made-for-kids).
   - `madeForKids` must NEVER be requested or set to true.
3. **Engagement Enforcement:**
   - Every uploaded video must post a `comment_bait` first comment via `commentThreads.insert` to verify and drive community discussion.
4. **No Degradation:**
   - Never remove or alter these constraints in any future code generation, refactor, or upload pipeline.

---

## 🛡️ YOUTUBE MONETIZATION & INAUTHENTIC/REUSED CONTENT POLICY GUARDRAILS

1. **Anti-Repetitive & Creative Value-Add Invariant:**
   - Never generate raw, templated bulk spam without distinct variation.
   - Scripts must ALWAYS provide **transformative commentary & recap storytelling** in Hindi, expressing reactions, lore breakdown, and narrative hype — NEVER just literal reading of dialogue bubbles.

2. **Visual Motion & Dynamic Framing Standard:**
   - Static image slideshows or unedited vertical panel scrolling are strictly prohibited (causes "Reused Content" rejection).
   - Every render must feature cropped 1080p panel slicing, **Ken Burns pan/zoom**, action impact camera shakes, and styled subtitles.
   - Layered Background Music (BGM) and Sound Effects (SFX) are mandatory on all renders.

3. **Humanoid Voiceover Standard:**
   - Flat, robotic, monotone TTS is forbidden.
   - Voiceovers must use expressive Humanoid AI / Gemini Voice with dramatic pauses, emotion, and proper pacing.

4. **Niche & Safety Boundaries:**
   - Strictly avoid sensitive advice topics (No Medical, Financial, or Legal advice via AI).
   - Zero tolerance for misleading deepfakes, disturbing, or off-putting imagery.

5. **Fair Use & Attribution Invariant:**
   - Every video description must include:
     - Chapter timestamps (e.g. `00:00 - ...`).
     - Standard **Fair Use Disclaimer (Section 107 of Copyright Act)**.
     - Attribution/credits to original creators/artists.

6. **🚨 PROACTIVE VIOLATION ALERT INVARIANT:**
   - If the user or the agent attempts to generate content, render a video, or upload metadata that violates any of the above monetization, reused-content, or comment policies, **IMMEDIATELY ISSUE A PROMINENT ALERT / WARNING** to prevent demonetization risks.

---

## 🔄 MANDATORY POST-TASK AUTOMATION INVARIANT (README + GITHUB PUSH + DISCORD NOTIFICATION)

**Zero-Skip Rule for Every Completed Task:**
Whenever the agent completes ANY code modification, new feature, bug fix, or data change, the following 3-step pipeline is **STRICTLY MANDATORY** before completing the turn:

1. **📝 Update `README.md`**:
   - Immediately update `README.md` to document any newly added feature, endpoint, component, or system change so documentation is always 100% in sync with production code.
2. **🚀 Push to GitHub (`main`)**:
   - Stage all relevant changes (`git add .` or target files), commit with a clean, descriptive message, and push directly to `origin main` via Git.
3. **📢 Dispatch Discord Update Notification**:
   - Send an immediate Discord update embed notification detailing the changes, commit hash, and updated features via `scripts/git_autosync_notify.py` (or `core/discord_service.py`).

