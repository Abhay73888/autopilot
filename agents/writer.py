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


class Writer:
    def __init__(self, db: DB | None = None, llm: LLM | None = None):
        self.db = db or DB()
        self.llm = llm or LLM()

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
        # (Soft penalty kaafi nahi thi — random se repeat ho jaata tha, aur
        #  lagatar same hook = duplicate-pattern clustering ka seedha invite hai.)
        blocked = set(recent[:1])
        candidates = [h for h in HOOK_TYPES if h not in blocked] or list(HOOK_TYPES)

        weights = {}
        for h in candidates:
            w = HOOK_TYPES[h]["retention"]
            # Overuse penalty — duplicate-pattern clustering se bachav.
            # ⚠️ Champion ke liye limit ZYADA hai (10 vs 6): wo jeeta hua hai,
            # isliye usse zyada chalna CHAHIYE. Par 20 mein se 10 se zyada
            # nahi — warna clustering ka risk. Ye ceiling jaan-boojh kar hai.
            overuse_limit = 10 if h in winners else 6
            if counts.get(h, 0) >= overuse_limit:
                w *= 0.25
            if h in recent[1:3]:               # 2-3 video pehle tha = kam chance
                w *= 0.35
            if h in winners:
                # ⭐ A/B ka winner. Boost bada hai par INFINITE nahi —
                # kyunki 100% ek hi hook = duplicate-pattern clustering = throttle.
                # Target: champion ~35-40% share le, 100% nahi.
                w *= 4.0
            if h in losers:
                # high-confidence pe haara hua — lagbhag hata do (poora nahi,
                # kyunki algorithm badal sakta hai aur re-test karna padega)
                w *= 0.15
            weights[h] = w

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

ALGORITHM RULES (2026 research, inhe todna mana hai):
1. Pehli spoken line 1.5 second mein khatam honi chahiye aur emotional trigger honi chahiye.
2. Text overlay 5-8 shabd ka, curiosity-gap wala (60% log sound off pe dekhte hain).
3. Aakhri line aisi ho jo PEHLI line se judti ho — loop banna chahiye taaki re-watch ho.
4. Comment bait ek SPECIFIC sawaal ho jiska jawab 5+ shabd ka hoga
   (5 shabd se chhote comments algorithm ginta hi nahi).
5. Koi clickbait jhoot nahi — jo hook promise kare, wo body deliver kare.
6. Sirf 3 hashtag.

JO PEHLE SEEKHA HAI (isse follow karo):
{self._learnings_block()}

YE TOPICS HAAL HI MEIN USE HO CHUKE HAIN — inse alag jao:
{json.dumps(self._recent_topics(), ensure_ascii=False)}

Sirf JSON return karo, ye shape:
{{
  "title": "YouTube title, 60 char se kam, curiosity-gap wala",
  "hook_line": "pehli spoken line, {CONFIG['language']} mein, 1.5s mein boli ja sake",
  "hook_text_overlay": "5-8 shabd, screen pe dikhega",
  "hook_visual": "pattern-interrupt visual ka ek line description",
  "body": ["spoken line 2", "spoken line 3", "..."],
  "ending": "aakhri spoken line — pehli line se loop bane",
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
            "hook_line": str(data.get("hook_line") or f"{topic} — sach kuch aur hai."),
            "hook_text_overlay": str(data.get("hook_text_overlay") or "Sach ab tak chhupa hai"),
            "hook_visual": str(data.get("hook_visual") or "close-up of a locked door, harsh shadow"),
            "ending": str(data.get("ending") or "Aur jawab aaj tak nahi mila."),
            "comment_bait": str(data.get("comment_bait")
                                or "Tumhe kya lagta hai iska asli reason kya tha? Detail mein batao."),
            "caption": str(data.get("caption") or topic),
        }

        # body ko hamesha list of non-empty strings banao
        body = data.get("body") or []
        if isinstance(body, str):
            body = [s.strip() for s in re.split(r"(?<=[।.!?])\s+", body) if s.strip()]
        out["body"] = [str(b).strip() for b in body if str(b).strip()][:12]
        if not out["body"]:
            out["body"] = ["Us raat kya hua, koi nahi jaanta.",
                           "Jo saboot mile, wo ulta sawaal khada karte the."]

        # hashtags: exactly 3
        tags = data.get("hashtags") or []
        if isinstance(tags, str):
            tags = tags.split()
        tags = ["#" + str(t).lstrip("#").strip() for t in tags if str(t).strip()]
        while len(tags) < 3:
            tags.append(["#unsolvedmystery", "#suspense", "#storytime"][len(tags)])
        out["hashtags"] = tags[:3]

        # text overlay 5-8 shabd — zyada ho to kaat do (padhne ka time nahi milta)
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
        parts = [script["hook_line"], *script["body"], script["ending"]]
        return " ".join(p.strip() for p in parts if p and p.strip())

    @staticmethod
    def lines(script: dict) -> list[str]:
        """Spoken lines ki list — scene split aur pacing ke liye."""
        return [p.strip() for p in [script["hook_line"], *script["body"], script["ending"]]
                if p and p.strip()]


if __name__ == "__main__":
    w = Writer()
    s = w.write("Ek gaon jahan se 14 log ek raat mein gayab ho gaye")
    print(json.dumps(s, indent=2, ensure_ascii=False))
