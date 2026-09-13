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
