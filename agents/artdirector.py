"""
agents/artdirector.py — Script ko 6-8 scenes mein todta hai + image prompts banata hai.

Do sabse zaroori cheezein (Section 5):

1. CHARACTER CONSISTENCY — har image prompt mein WAHI character description
   shabd-ba-shabd repeat hoti hai. Pollinations/Gemini ke paas memory nahi hoti;
   consistency ka ek hi tareeka hai — prompt mein sab kuch dobara likhna.

2. TEMPLATE ROTATION — kam se kam 4 visual templates. Har video ek alag template.
   Kyun? YouTube 2026 mein "duplicate-pattern clustering" karta hai: same voice +
   same visual look har video mein = throttle. Rotation isse todta hai.

Motion directions bhi yahi decide karta hai (Ken Burns) — direction ALTERNATE hoti hai
(zoom in -> pan left -> zoom out -> pan right), taaki slideshow jaisa na lage.
"""

from __future__ import annotations

import json
import re

from core.config import CONFIG
from core.db import DB
from core.llm import LLM
from core.logbook import Logbook

log = Logbook("artdirector")

# ---------------------------------------------------------------------
# 4 VISUAL TEMPLATES — har ek ka apna alag look.
# Ye sirf "style" nahi hain, poora colour + lighting + composition system hai.
# ---------------------------------------------------------------------
TEMPLATES = {
    "noir_teal": {
        "name": "Noir Teal",
        "style": ("flat 2D cartoon illustration, heavy noir shadows, muted teal and "
                  "burnt orange palette, thick black ink outlines, film grain texture"),
        "lighting": "single hard key light from one side, deep black shadows",
        "camera": "low angle, dramatic perspective",
    },
    "moonlit_blue": {
        "name": "Moonlit Blue",
        "style": ("flat 2D cartoon illustration, cold moonlit blue and pale silver palette, "
                  "soft misty gradients, minimal thin outlines, subtle vignette"),
        "lighting": "cool moonlight from above, long soft shadows, fog haze",
        "camera": "wide establishing shot, centered composition",
    },
    "sepia_archive": {
        "name": "Sepia Archive",
        "style": ("flat 2D cartoon illustration, aged sepia and dusty amber palette, "
                  "paper grain, faded edges, old case-file aesthetic, halftone dots"),
        "lighting": "flat diffused daylight, slightly overexposed",
        "camera": "eye level, documentary framing",
    },
    "crimson_alert": {
        "name": "Crimson Alert",
        "style": ("flat 2D cartoon illustration, deep charcoal with crimson red accent "
                  "palette, high contrast, sharp geometric shadows, bold graphic shapes"),
        "lighting": "harsh red rim light, everything else near-black",
        "camera": "extreme close-up, tight crop, off-center subject",
    },
}

# Ken Burns motions — cycle mein chalte hain taaki do lagatar scene same na lagein
MOTIONS = ["zoom_in", "pan_left", "zoom_out", "pan_right", "zoom_in_slow", "pan_up"]

# Har image prompt ke end mein ye jaata hai — 9:16 aur "no text" enforce karne ke liye.
NEGATIVE = ("vertical 9:16 composition, no text, no letters, no watermark, no signature, "
            "no photorealism, no real photograph, no logo")

CONSISTENCY_KEYWORDS = "same character as previous scene, identical facial features, consistent costume"


def build_visual_anchor(name: str, gender: str = "male", age: int = 32,
                        costume: str | None = None, features: dict | None = None) -> dict:
    """
    Phase D: Visual Identity Anchor generator.
    Produces deterministic, hyper-specific physical anchor and costume.
    """
    gender_norm = "female" if str(gender).lower() in ("female", "f", "woman") else "male"
    man_woman = "woman" if gender_norm == "female" else "man"

    if gender_norm == "male":
        hair = (features and features.get("hair")) or "short textured black hair"
        facial = (features and features.get("facial")) or "sharp jawline, tired intense dark eyes"
        marks = (features and features.get("marks")) or "thin scar on left cheekbone, rectangular metal-rimmed glasses"
        default_costume = costume or (features and features.get("costume")) or "dark brown woolen trench coat over maroon high-neck sweater"
    else:
        hair = (features and features.get("hair")) or "dark wavy hair tied back in low ponytail"
        facial = (features and features.get("facial")) or "sharp defined cheekbones, intense watchful dark brown eyes"
        marks = (features and features.get("marks")) or "thin faint scar near temple, rectangular dark-rimmed glasses"
        default_costume = costume or (features and features.get("costume")) or "dark charcoal woolen trench coat over emerald green high-neck sweater"

    feat = {
        "name": name,
        "gender": gender_norm,
        "age": age,
        "ethnicity": "South Asian",
        "hair": hair,
        "facial": facial,
        "marks": marks,
        "costume": default_costume,
    }
    anchor = f"Same {age}-year-old South Asian {man_woman} with {facial}, {hair}, {marks}, wearing {default_costume}"
    return {
        "name": name,
        "anchor": anchor,
        "costume": default_costume,
        "features": feat,
        "keywords": CONSISTENCY_KEYWORDS,
    }


class ArtDirector:
    def __init__(self, db: DB | None = None, llm: LLM | None = None):
        self.db = db or DB()
        self.llm = (llm.for_agent("artdirector") if hasattr(llm, "for_agent") else llm) if llm else LLM(agent_name="artdirector")

    # ------------------------------------------------------------------
    def pick_template(self) -> str:
        """Aisa template chuno jo pichhle 3 videos mein use na hua ho."""
        options = list(TEMPLATES)

        # ⭐ PHASE 8: chal raha experiment rotation ko override karta hai
        try:
            from agents.scientist import Scientist
            sci = Scientist(self.db)
            forced = sci.forced_value("template_id")
            if forced and forced in TEMPLATES:
                log.info(f"Experiment chal raha hai — template forced: {forced}")
                return forced
            for bad in sci.losers().get("template_id", []):
                if bad in options and len(options) > 2:
                    options.remove(bad)
        except Exception as e:  # noqa: BLE001
            log.debug(f"Scientist check skip: {str(e)[:80]}")

        tpl = self.db.pick_rotated("template_id", options, avoid_last=3)
        log.info(f"Visual template chuna: {TEMPLATES[tpl]['name']}",
                 last3=self.db.recent_values("template_id", 3))
        return tpl

    # ------------------------------------------------------------------
    def pick_pacing(self) -> str:
        """
        Scientist experiment ya Analyst drop-off recommendation ke mutabiq pacing chuno.
        Return: 'standard' | 'dynamic_fast'
        """
        try:
            from agents.scientist import Scientist
            sci = Scientist(self.db)
            forced = sci.forced_value("scene_pacing")
            if forced:
                log.info(f"Experiment chal raha hai — scene_pacing forced: {forced}")
                return forced
        except Exception as e:
            log.debug(f"Scientist pacing check skip: {e}")

        try:
            from agents.analyst import Analyst
            an = Analyst(self.db)
            rec = an.detect_pacing_dropoff()
            if rec.get("recommended_pacing") == "dynamic_fast":
                log.info("Analyst drop-off alert: mid-story dropoff detect hua — dynamic_fast pacing chuni")
                return "dynamic_fast"
        except Exception as e:
            log.debug(f"Analyst pacing dropoff check skip: {e}")

        return "standard"

    # ------------------------------------------------------------------
    def direct(self, script: dict, template_id: str | None = None,
               n_scenes: int | None = None, pacing: str | None = None,
               video_id: int | None = None) -> dict:
        """
        Script -> scene list.
        Har scene mein: image prompt, motion, aur wo spoken line jo us par chalegi.
        """
        template_id = template_id or self.pick_template()
        pacing = pacing or self.pick_pacing()
        tpl = TEMPLATES[template_id]

        lines = _script_lines(script)
        # Scene count: har scene ~4-5s. 32s video = ~7 scenes. Clamp 6-8.
        if n_scenes is None:
            n_scenes = max(6, min(8, round(script.get("target_length_sec", 32) / 4.5)))
        n_scenes = max(6, min(8, n_scenes))

        prompt = f"""Tum ek art director ho jo cartoon suspense shorts banata hai.

STORY (spoken lines, kramvaar):
{json.dumps(lines, ensure_ascii=False, indent=2)}

VISUAL STYLE (har scene mein ye exact style honi chahiye):
{tpl['style']}
Lighting: {tpl['lighting']}
Camera: {tpl['camera']}

KAAM:
1. Ek MAIN CHARACTER design karo — usse ek chhoti, THOS description do
   (umar, kapde, baal, ek yaad rehne wali detail). Ye description har scene
   mein HUBAHU repeat hogi, isliye 15-25 shabd mein rakhna.
2. Story ko theek {n_scenes} scenes mein todo.
3. Scene 1 ek PATTERN-INTERRUPT visual ho — chaunkane wala, pehle frame ke liye.
4. AAKHRI SCENE PEHLE SCENE JAISA DIKHNA CHAHIYE (loop banega, re-watch badhega).
5. Har scene ka image prompt English mein, 25-45 shabd, THOS visual detail —
   abstract concepts nahi (image model "dhokha" draw nahi kar sakta,
   "ek aadmi kaanpte haath se darwaza kholta hua" draw kar sakta hai).
6. Kisi bhi prompt mein TEXT/letters mat maango.

Sirf JSON return karo:
{{
  "character": "15-25 shabd ki thos character description",
  "setting": "8-15 shabd ka jagah ka description",
  "scenes": [
    {{"n": 1, "beat": "is scene mein kya ho raha hai (Hindi mein 1 line)",
      "image_prompt": "English visual description, 25-45 shabd, koi text nahi"}}
  ]
}}"""

        data = self.llm.json(prompt)
        return self._build(data, script, template_id, n_scenes, lines, pacing=pacing, video_id=video_id)

    # ------------------------------------------------------------------
    def _build(self, data: dict, script: dict, template_id: str,
               n_scenes: int, lines: list[str], pacing: str = "standard",
               video_id: int | None = None) -> dict:
        tpl = TEMPLATES[template_id]
        character = str(data.get("character") or
                        "a 30-year-old Indian man in a worn grey jacket, tired eyes, "
                        "short black hair, a red scarf around his neck")[:220]
        setting = str(data.get("setting") or "an abandoned village house at night")[:160]

        # Phase D: Cast identification & Visual Identity Anchors
        cast = script.get("cast") if isinstance(script.get("cast"), list) else []
        char_anchors: dict[str, dict] = {}

        if cast:
            for member in cast:
                cname = str(member.get("name") or "protagonist").strip()
                cgender = str(member.get("gender") or "male").strip()
                # Check DB for existing character
                existing = self.db.get_character(cname) if hasattr(self.db, "get_character") else None
                if existing and CONFIG.get("effects", {}).get("character_consistency", {}).get("reuse_existing", True):
                    features = json.loads(existing["features_json"]) if existing["features_json"] else {}
                    char_anchors[cname.lower()] = {
                        "name": cname,
                        "anchor": existing["visual_anchor"],
                        "costume": existing["costume"],
                        "features": features,
                        "keywords": CONSISTENCY_KEYWORDS,
                    }
                    log.info(f"Existing character visual anchor reused: {cname}")
                else:
                    anchor_info = build_visual_anchor(cname, gender=cgender)
                    char_anchors[cname.lower()] = anchor_info
                    if hasattr(self.db, "save_character"):
                        self.db.save_character(
                            name=cname,
                            visual_anchor=anchor_info["anchor"],
                            video_id=video_id,
                            costume=anchor_info["costume"],
                            features=anchor_info["features"],
                        )
        else:
            # Single character fallback
            default_name = "protagonist"
            existing = self.db.get_character(default_name) if hasattr(self.db, "get_character") else None
            if existing and CONFIG.get("effects", {}).get("character_consistency", {}).get("reuse_existing", True):
                features = json.loads(existing["features_json"]) if existing["features_json"] else {}
                char_anchors[default_name] = {
                    "name": default_name,
                    "anchor": existing["visual_anchor"],
                    "costume": existing["costume"],
                    "features": features,
                    "keywords": CONSISTENCY_KEYWORDS,
                }
            else:
                anchor_info = build_visual_anchor(default_name, gender="male")
                char_anchors[default_name] = anchor_info
                if hasattr(self.db, "save_character"):
                    self.db.save_character(
                        name=default_name,
                        visual_anchor=anchor_info["anchor"],
                        video_id=video_id,
                        costume=anchor_info["costume"],
                        features=anchor_info["features"],
                    )

        # Primary anchor (first in cast or protagonist)
        primary_key = list(char_anchors.keys())[0]
        primary_anchor = char_anchors[primary_key]["anchor"]

        raw_scenes = data.get("scenes") or []
        if not isinstance(raw_scenes, list):
            raw_scenes = []

        cfg_eff = CONFIG.get("effects", {}).get("character_consistency", {})
        neg_extra = cfg_eff.get("negative_prompt_extra", "different face, inconsistent clothing, different actor")
        full_negative = f"{NEGATIVE}, {neg_extra}"

        scenes = []
        for i in range(n_scenes):
            src = raw_scenes[i] if i < len(raw_scenes) and isinstance(raw_scenes[i], dict) else {}
            base = str(src.get("image_prompt") or "").strip()
            if not base:
                # LLM ne kam scenes diye — fallback prompt bana lo, ruko mat
                base = f"the character stands still in {setting}, tense atmosphere"
                log.warn(f"Scene {i+1} ka prompt LLM se nahi mila — fallback use kiya")

            # Determine character for this scene
            active_key = primary_key
            for cname in char_anchors:
                if cname in base.lower() or (i < len(lines) and cname in lines[i].lower()):
                    active_key = cname
                    break
            active_info = char_anchors[active_key]

            # Anchor prepended at the START of prompt with consistency keywords
            anchor_prefix = f"{active_info['anchor']}, {CONSISTENCY_KEYWORDS}. "

            # ⭐ CHARACTER CONSISTENCY: Har prompt mein wahi visual anchor + character + style + negatives
            full_prompt = (
                f"{anchor_prefix}"
                f"{tpl['style']}. "
                f"CHARACTER (must look identical in every image): {character}. "
                f"SCENE: {base}. "
                f"SETTING: {setting}. "
                f"Lighting: {tpl['lighting']}. Camera: {tpl['camera']}. "
                f"{full_negative}"
            )

            scenes.append({
                "n": i + 1,
                "beat": str(src.get("beat") or "")[:200],
                "image_prompt": _clean(full_prompt),
                "motion": MOTIONS[i % len(MOTIONS)],   # alternate, kabhi lagatar same nahi
                "parallax": i % 2 == 1,
                "line": lines[i] if i < len(lines) else "",
                "file": f"scene_{i+1:02d}.jpg",
                "character_name": active_info["name"],
                "visual_anchor": active_info["anchor"],
            })

        # Loop enforce: aakhri scene = pehle scene ka echo (Section 8: loop-perfect ending)
        scenes[-1]["image_prompt"] = scenes[0]["image_prompt"]
        scenes[-1]["beat"] = (scenes[-1]["beat"] or "") + " [loop frame — scene 1 ka echo]"
        scenes[-1]["motion"] = "zoom_out"   # scene 1 zoom_in tha -> perfect loop

        if pacing == "dynamic_fast" and len(scenes) >= 5:
            scenes[3]["beat"] = (scenes[3]["beat"] or "") + " [mini-reveal — fast twist to prevent drop-off]"
            scenes[3]["pacing"] = "fast"
            scenes[4]["pacing"] = "fast"

        out = {
            "template_id": template_id,
            "template_name": tpl["name"],
            "pacing": pacing,
            "character": character,
            "characters": list(char_anchors.values()),
            "character_anchors": {k: v["anchor"] for k, v in char_anchors.items()},
            "setting": setting,
            "scenes": scenes,
            "n_scenes": len(scenes),
        }
        log.ok(f"{len(scenes)} scenes ready ({pacing} pacing)", template=tpl["name"],
               character=character[:50] + "...")
        return out


# ---------------------------------------------------------------------
def _clean(text: str) -> str:
    """Extra spaces/newlines hatao — URL mein jaayega isliye saaf hona chahiye."""
    return re.sub(r"\s+", " ", text).strip()


def _script_lines(script: dict) -> list[str]:
    return [p.strip() for p in [script.get("hook_line", ""),
                                *(script.get("body") or []),
                                script.get("ending", "")] if p and p.strip()]


if __name__ == "__main__":
    from agents.writer import Writer
    s = Writer().write("Ek gaon jahan se 14 log ek raat mein gayab ho gaye")
    print(json.dumps(ArtDirector().direct(s), indent=2, ensure_ascii=False))
