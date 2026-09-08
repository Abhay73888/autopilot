"""
agents/writer.py — Script + hook + caption + title banata hai.

Section 3 ke research se bandhe hue rules:
  * 3-layer hook pehle 1.5 second mein: visual + spoken line + text overlay
  * Hook type ROTATE karo — pichhle 20 videos se alag (duplicate-pattern clustering)
  * Hook types ki asli retention: specific_outcome 45%, pov 42%,
    contrarian 38%, question 28%, generic_reveal 12% (ye BANNED hai)
  * Loop-friendly ending — aakhri line pehli line se connect kare (re-watch spike)
  * Comment bait jo 5+ SHABD ka jawab maange (chhote comments algorithm ignore karta hai)
  * 3 hashtag, zyada nahi

Writer har run se pehle learnings DB padhta hai — jo jeeta hua variant hai
usse zyada weight milta hai. Yahi "self-improving" ka pehla hissa hai.
"""

from __future__ import annotations

import json
import random
import re

from core.config import CONFIG
from core.db import DB
from core.llm import LLM
from core.logbook import Logbook

log = Logbook("writer")

# Section 3 ki table — number = measured retention. generic_reveal jaan-boojh kar bahar hai.
HOOK_TYPES = {
    "specific_outcome": {
        "retention": 0.45,
        "desc": "Ek concrete, chaunkane wala natija pehle hi bata do. "
                "Example: '14 log ek raat mein gayab ho gaye.'",
    },
    "pov": {
        "retention": 0.42,
        "desc": "Darshak ko scene ke andar khada kar do, present tense. "
                "Example: 'Tum us kamre mein ho, aur darwaza andar se band hai.'",
    },
    "contrarian": {
        "retention": 0.38,
        "desc": "Jo sab maante hain usse ulta bolo. "
                "Example: 'Ye case solve ho chuka tha — police ne chhupa liya.'",
    },
    "question": {
        "retention": 0.28,
        "desc": "Curiosity-gap sawaal. Sabse kamzor allowed type — kam use karo.",
    },
}
BANNED_HOOKS = ["generic_reveal"]  # 12% retention = distribution suicide
VALID_EMOTIONS = {
    "neutral", "curious", "serious", "nervous", "trembling",
    "whispers", "panicked", "gasp", "sighs", "amazed", "cold", "urgent"
}


class Writer:
    def __init__(self, db: DB | None = None, llm: LLM | None = None):
        self.db = db or DB()
        self.llm = (llm.for_agent("writer") if hasattr(llm, "for_agent") else llm) if llm else LLM(agent_name="writer")

    # ------------------------------------------------------------------
    def pick_hook_type(self) -> str:
        """
        Hook type chuno:
          1. Pichhle 20 videos ke hook types dekho
          2. Jo type 20 mein 6+ baar aaya, usse skip karo (clustering se bacho)
          3. Learnings DB mein koi jeeta hua hook hai to usse 2x weight do
          4. Baaki retention ke hisaab se weighted random
        """
        # ⭐ PHASE 8: agar koi A/B experiment hook_type pe chal raha hai to
        # rotation override ho jaata hai — Scientist decide karta hai.
        try:
            from agents.scientist import Scientist
            forced = Scientist(self.db).forced_value("hook_type")
            if forced and forced in HOOK_TYPES:
                log.info(f"Experiment chal raha hai — hook type forced: {forced}")
                return forced
        except Exception as e:  # noqa: BLE001
            log.debug(f"Scientist check skip: {str(e)[:80]}")

        recent = self.db.recent_values("hook_type", 20)
        counts = {h: recent.count(h) for h in HOOK_TYPES}

        # Jeete/haare hook types (Scientist ne A/B se nikale)
        winners, losers = [], []
        for r in self.db.active_learnings("hook_type"):
            if r["confidence"] in ("medium", "high"):
                winners.append(r["winner"])
                if r["confidence"] == "high" and r["loser"]:
                    losers.append(r["loser"])

        # ⭐ HARD RULE: pichhle video ka hook type dobara nahi chalega.
        blocked = set(recent[:1])
        candidates = [h for h in HOOK_TYPES if h not in blocked] or list(HOOK_TYPES)

        weights = {}
        for h in candidates:
            w = HOOK_TYPES[h]["retention"]
            # Overuse penalty — duplicate-pattern clustering se bachav.
            if counts.get(h, 0) >= 6:
                w *= 0.25
            if h in winners:
                w *= 2.5
            if h in losers:
                w *= 0.3
            weights[h] = max(0.05, w)

        pick = random.choices(list(weights), weights=list(weights.values()))[0]
        log.info(f"Hook type chuna: {pick}", last20=counts, winners=winners or None)
        return pick

    # ------------------------------------------------------------------
    def _learnings_block(self) -> str:
        """Active learnings ko prompt mein daalne layak text bana do."""
        rows = self.db.active_learnings()
        if not rows:
            return "(Abhi koi learning nahi hai — ye shuruaati videos hain.)"
        lines = []
        for r in rows[:8]:
            lines.append(f"- {r['variable']}: '{r['winner']}' ne '{r['loser']}' se "
                         f"{r['lift_pct']:+.0f}% better perform kiya "
                         f"(n={r['sample_size']}, confidence={r['confidence']})")
        return "\n".join(lines)

    def _recent_topics(self, n: int = 15) -> list[str]:
        return [r["topic"] for r in self.db.recent_videos(n) if r["topic"]]

    # ------------------------------------------------------------------
    def write(self, topic: str, hook_type: str | None = None,
              length_sec: int | None = None) -> dict:
        """Ek poora script package banao. Hamesha valid dict lautata hai."""
        hook_type = hook_type or self.pick_hook_type()
        if hook_type in BANNED_HOOKS:
            raise ValueError(f"'{hook_type}' banned hai — sirf 12% retention deta hai")

        length = length_sec or CONFIG["video_length_sec"]
        # ~2.6 Hindi shabd/second natural narration speed pe (pauses ke saath)
        target_words = int(length * 2.6)

        prompt = f"""Tum ek viral short-form video scriptwriter ho jo {CONFIG['language']} mein likhta hai.

NICHE: {CONFIG['niche']}
AUDIENCE: {CONFIG['target_audience']}
TOPIC: {topic}
VIDEO LENGTH: {length} seconds (~{target_words} shabd, isse zyada BILKUL nahi)
HOOK TYPE (compulsory): {hook_type} — {HOOK_TYPES[hook_type]['desc']}

ALGORITHM RULES (2026 research, multi-voice dialogue):
1. Narrator aur characters ka gender ALTERNATE hona chahiye — narrator male to kam se kam ek char female, vice versa. Har video mein male + female dono awaazein hon.
2. Dialogue share: 30-50% lines characters ki hon, baaki narrator.
3. Hook line aur ending HAMESHA narrator bolega. Reveal narrator ya character bol sakta hai.
4. Pehli spoken line 1.5 second mein khatam honi chahiye aur emotional trigger honi chahiye.
5. Text overlay 5-8 shabd ka, curiosity-gap wala (60% log sound off pe dekhte hain).
6. Aakhri line aisi ho jo PEHLI line se judti ho — loop banna chahiye taaki re-watch ho.
7. Comment bait ek SPECIFIC sawaal ho jiska jawab 5+ shabd ka hoga (5 shabd se chhote comments algorithm ginta nahi).
8. Max 2 characters (narrator + char_a, optional char_b).
9. emotion sirf in mein se ho: neutral, curious, serious, nervous, trembling, whispers, panicked, gasp, sighs, amazed, cold, urgent.
10. Sirf 3 hashtag.

JO PEHLE SEEKHA HAI (isse follow karo):
{self._learnings_block()}

YE TOPICS HAAL HI MEIN USE HO CHUKE HAIN — inse alag jao:
{json.dumps(self._recent_topics(), ensure_ascii=False)}

Sirf JSON return karo, ye exact shape:
{{
  "title": "YouTube title, 60 char se kam, curiosity-gap wala",
  "hook_text_overlay": "5-8 shabd, screen pe dikhega",
  "hook_visual": "pattern-interrupt visual ka ek line description",
  "cast": {{
    "narrator": {{"gender": "male", "persona": "gambhir crime-doc narrator, dheemi awaaz"}},
    "char_a": {{"name": "Ravi", "gender": "female", "persona": "darawani aawaz, ghabrahat"}},
    "char_b": {{"name": "Meera", "gender": "female", "persona": "..."}}
  }},
  "lines": [
    {{"speaker": "narrator", "text": "...", "emotion": "curious", "role": "hook"}},
    {{"speaker": "char_a", "text": "...", "emotion": "nervous", "role": "body"}},
    {{"speaker": "narrator", "text": "...", "emotion": "serious", "role": "body"}},
    {{"speaker": "char_a", "text": "...", "emotion": "whispers", "role": "reveal"}},
    {{"speaker": "narrator", "text": "...", "emotion": "serious", "role": "ending"}}
  ],
  "comment_bait": "specific sawaal jo lamba jawab maange",
  "caption": "Instagram caption, 2 line",
  "hashtags": ["#tag1", "#tag2", "#tag3"]
}}"""

        data = self.llm.json(prompt)
        return self._normalize(data, topic, hook_type, length)

    # ------------------------------------------------------------------
    def _normalize(self, data: dict, topic: str, hook_type: str, length: int) -> dict:
        """
        LLM ka output kabhi bharosemand nahi hota. Yahan har field ko
        check karke theek karte hain taaki aage ki pipeline kabhi crash na ho.
        """
        out = {
            "topic": topic,
            "hook_type": hook_type,
            "target_length_sec": length,
            "title": str(data.get("title") or topic)[:95],
            "hook_text_overlay": str(data.get("hook_text_overlay") or "Sach ab tak chhupa hai"),
            "hook_visual": str(data.get("hook_visual") or "close-up of a locked door, harsh shadow"),
            "comment_bait": str(data.get("comment_bait")
                                or "Tumhe kya lagta hai iska asli reason kya tha? Detail mein batao."),
            "caption": str(data.get("caption") or topic),
        }

        # ---- CAST NORMALIZATION ----
        raw_cast = data.get("cast") or {}
        if not isinstance(raw_cast, dict):
            raw_cast = {}

        narrator_data = raw_cast.get("narrator") or {}
        if not isinstance(narrator_data, dict):
            narrator_data = {}
        narr_gender = str(narrator_data.get("gender") or "male").strip().lower()
        if narr_gender not in ("male", "female"):
            narr_gender = "male"
        narr_persona = str(narrator_data.get("persona") or "gambhir crime-doc narrator, dheemi awaaz")

        cast = {
            "narrator": {"gender": narr_gender, "persona": narr_persona}
        }

        # Extra characters (max 2 characters: char_a, char_b)
        char_keys = [k for k in raw_cast if k != "narrator"]
        kept_chars = {}
        for idx, k in enumerate(char_keys[:2]):
            c = raw_cast[k]
            if isinstance(c, dict):
                c_name = str(c.get("name") or f"Character {idx+1}").strip()
                c_gender = str(c.get("gender") or ("female" if narr_gender == "male" else "male")).strip().lower()
                if c_gender not in ("male", "female"):
                    c_gender = "female" if narr_gender == "male" else "male"
                c_persona = str(c.get("persona") or "darawani aawaz")
                kept_chars[f"char_{chr(97+idx)}"] = {"name": c_name, "gender": c_gender, "persona": c_persona}

        # Gender alternation rule: Narrator aur characters ka gender ALTERNATE hona chahiye.
        if kept_chars:
            char_genders = {c["gender"] for c in kept_chars.values()}
            if len(char_genders) == 1 and narr_gender in char_genders:
                narr_gender = "female" if narr_gender == "male" else "male"
                cast["narrator"]["gender"] = narr_gender
                log.warn("Narrator aur character ka gender identical tha — narrator gender flip kiya",
                         new_narrator_gender=narr_gender)

        cast.update(kept_chars)
        valid_speakers = set(cast.keys())
        # Also map character display names to their keys
        name_to_key = {c["name"].lower(): k for k, c in kept_chars.items()}

        # ---- LINES NORMALIZATION ----
        raw_lines = data.get("lines")
        norm_lines = []

        if isinstance(raw_lines, list) and raw_lines:
            for item in raw_lines:
                if isinstance(item, dict):
                    spk = str(item.get("speaker") or "narrator").strip().lower()
                    if spk not in valid_speakers:
                        spk = name_to_key.get(spk, "narrator")
                    txt = str(item.get("text") or "").strip()
                    emo = str(item.get("emotion") or "neutral").strip().lower()
                    if emo not in VALID_EMOTIONS:
                        emo = "neutral"
                    role = str(item.get("role") or "body").strip().lower()
                    if txt:
                        norm_lines.append({"speaker": spk, "text": txt, "emotion": emo, "role": role})

        # Fallback if lines missing or legacy shape
        if not norm_lines:
            hook_txt = str(data.get("hook_line") or f"{topic} — sach kuch aur hai.").strip()
            norm_lines.append({"speaker": "narrator", "text": hook_txt, "emotion": "curious", "role": "hook"})

            body_items = data.get("body") or []
            if isinstance(body_items, str):
                body_items = [s.strip() for s in re.split(r"(?<=[।.!?])\s+", body_items) if s.strip()]
            for b in body_items:
                btxt = str(b).strip()
                if btxt:
                    norm_lines.append({"speaker": "narrator", "text": btxt, "emotion": "serious", "role": "body"})

            if len(norm_lines) == 1:
                norm_lines.append({"speaker": "narrator", "text": "Us raat kya hua, koi nahi jaanta.", "emotion": "serious", "role": "body"})
                norm_lines.append({"speaker": "narrator", "text": "Jo saboot mile, wo ulta sawaal khada karte the.", "emotion": "serious", "role": "body"})

            end_txt = str(data.get("ending") or "Aur jawab aaj tak nahi mila.").strip()
            norm_lines.append({"speaker": "narrator", "text": end_txt, "emotion": "serious", "role": "ending"})

        # Enforce hook and ending rules
        norm_lines[0]["speaker"] = "narrator"
        norm_lines[0]["role"] = "hook"
        if norm_lines[0]["emotion"] == "neutral":
            norm_lines[0]["emotion"] = "curious"

        norm_lines[-1]["speaker"] = "narrator"
        norm_lines[-1]["role"] = "ending"
        if norm_lines[-1]["emotion"] == "neutral":
            norm_lines[-1]["emotion"] = "serious"

        out["cast"] = cast
        out["lines"] = norm_lines

        # Backward compatibility: populate hook_line, body, ending
        out["hook_line"] = norm_lines[0]["text"]
        out["body"] = [l["text"] for l in norm_lines[1:-1]]
        out["ending"] = norm_lines[-1]["text"]

        # hashtags: exactly 3
        tags = data.get("hashtags") or []
        if isinstance(tags, str):
            tags = tags.split()
        tags = ["#" + str(t).lstrip("#").strip() for t in tags if str(t).strip()]
        while len(tags) < 3:
            tags.append(["#unsolvedmystery", "#suspense", "#storytime"][len(tags)])
        out["hashtags"] = tags[:3]

        # text overlay 5-8 shabd — zyada ho to kaat do
        words = out["hook_text_overlay"].split()
        if len(words) > 8:
            out["hook_text_overlay"] = " ".join(words[:8])
            log.warn("Text overlay 8 shabd se bada tha — kaat diya")

        # ---- QC checks: fail nahi karte, sirf warn karte hain ----
        out["warnings"] = []
        full = self.full_narration(out)
        wc = len(full.split())
        est = wc / 2.6
        if est > length * 1.25:
            out["warnings"].append(f"Script lambi hai (~{est:.0f}s vs target {length}s) — trim hoga")
        if est < length * 0.6:
            out["warnings"].append(f"Script chhoti hai (~{est:.0f}s vs target {length}s)")
        if len(out["comment_bait"].split()) < 5:
            out["warnings"].append("Comment bait bahut chhota — lamba jawab invite nahi karega")
        if len(out["hook_line"].split()) > 12:
            out["warnings"].append("Hook line 1.5s mein nahi bolі ja sakegi — chhoti karo")
        for w in out["warnings"]:
            log.warn(w)

        out["word_count"] = wc
        out["est_sec"] = round(est, 1)
        return out

    # ------------------------------------------------------------------
    @staticmethod
    def full_narration(script: dict) -> str:
        """Saari spoken lines ek string mein — TTS ko yahi jaata hai."""
        if "lines" in script and isinstance(script["lines"], list) and script["lines"]:
            parts = [l["text"] if isinstance(l, dict) else str(l) for l in script["lines"]]
        else:
            parts = [script.get("hook_line", ""), *(script.get("body") or []), script.get("ending", "")]
        return " ".join(p.strip() for p in parts if p and p.strip())

    @staticmethod
    def lines(script: dict) -> list[dict | str]:
        """Spoken lines ki list — objects agar available hain, warna strings."""
        if "lines" in script and isinstance(script["lines"], list) and script["lines"]:
            return script["lines"]
        return [p.strip() for p in [script.get("hook_line", ""),
                                    *(script.get("body") or []),
                                    script.get("ending", "")] if p and p.strip()]


if __name__ == "__main__":
    w = Writer()
    s = w.write("Ek gaon jahan se 14 log ek raat mein gayab ho gaye")
    print(json.dumps(s, indent=2, ensure_ascii=False))
