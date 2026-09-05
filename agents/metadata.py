"""
agents/metadata.py — AI Publishing Layer (Phase 5).

Ye agent upload se PEHLE ka poora "packaging" kaam karta hai:
  * 5 title variations (SEO, <100 char, no clickbait)
  * SEO description (CTA + hashtags + social links + credits + timestamps)
  * 15-30 tags — dedupe + relevance rank (YouTube ka 500-char limit enforce)
  * Thumbnail metadata (title/subtitle/colors/concept/emotion/hook) — JSON
  * Category detection -> YouTube categoryId
  * Language detection -> defaultLanguage / defaultAudioLanguage
  * Metadata validation (title/desc/tags/thumbnail/video file)
  * SEO score /100 + deductions + suggestions
  * Sab kuch logs/ mein (Logbook JSONL) + optional metadata JSON file

Design rules (baaki codebase jaisa hi):
  * Sirf stdlib. LLM = core.llm.LLM (mock-safe, quota-checked, retry built-in).
  * LLM output pe KABHI bharosa nahi — har field _normalize hoti hai,
    fallback deterministic heuristics hain (mock mode mein bhi kaam kare).
  * Dict-based contracts (dataclass nahi) — poora codebase dicts pe chalta hai.
  * DI: db/llm constructor se inject hote hain (tests inject karte hain).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from core.config import CONFIG
from core.db import DB
from core.llm import LLM
from core.logbook import Logbook

log = Logbook("metadata")

# ---------------------------------------------------------------------
# YouTube category IDs (official videoCategories.list se — US region).
# Sirf assignable categories yahan hain.
# ---------------------------------------------------------------------
CATEGORIES = {
    "film & animation": "1",
    "autos & vehicles": "2",
    "music": "10",
    "pets & animals": "15",
    "sports": "17",
    "travel & events": "19",
    "gaming": "20",
    "people & blogs": "22",
    "comedy": "23",
    "entertainment": "24",
    "news & politics": "25",
    "howto & style": "26",
    "education": "27",
    "science & technology": "28",
    "nonprofits & activism": "29",
}

# Keyword -> category ka deterministic fallback (LLM na ho / galat bole to).
# Order maayne rakhta hai — pehla match jeet-ta hai, isliye specific pehle.
_CATEGORY_KEYWORDS = [
    (("programming", "python", "javascript", "coding", "code", "software",
      "ai", "artificial intelligence", "machine learning", "tech", "computer",
      "gadget", "smartphone", "science"), "science & technology"),
    (("gaming", "gameplay", "minecraft", "gta", "pubg", "valorant", "esports"), "gaming"),
    (("tutorial", "how to", "learn", "course", "exam", "study", "finance",
      "investing", "stock", "trading", "history", "facts", "education"), "education"),
    (("comedy", "funny", "prank", "meme"), "comedy"),
    (("music", "song", "cover", "remix"), "music"),
    (("news", "politics", "election"), "news & politics"),
    (("vlog", "daily", "lifestyle", "routine"), "people & blogs"),
    (("mystery", "suspense", "story", "horror", "crime", "kahani"), "entertainment"),
]

# Language detect ke liye script-range heuristic (LLM-free, deterministic)
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# YouTube ke hard limits — validation inke against hoti hai
LIMITS = {
    "title_max": 100,
    "desc_max": 5000,
    "tags_total_chars": 500,   # saare tags jod kar (YouTube ka asli limit)
    "tag_max_chars": 100,
    "tags_max": 30,
    "thumb_max_bytes": 2 * 1024 * 1024,
}

CLICKBAIT_WORDS = ["you won't believe", "gone wrong", "shocking truth exposed",
                   "!!!", "100% real", "must watch", "viral video"]


class MetadataError(RuntimeError):
    """Metadata validation fail — message mein exact fix likha hota hai."""


# =====================================================================
class MetadataAgent:
    """
    Upload-ready metadata package banata hai.

        agent = MetadataAgent()
        pkg = agent.build(topic="...", script_text="...")
        # pkg mein: titles[5], title, description, tags, thumbnail_meta,
        #           category_id, language, seo (score/deductions/suggestions)
    """

    def __init__(self, db: DB | None = None, llm: LLM | None = None):
        self.db = db or DB()
        self.llm = llm or LLM()

    # ==================================================================
    # 1. TITLES — 5 variations
    # ==================================================================
    def titles(self, topic: str, script_text: str = "") -> list[str]:
        """5 SEO-friendly titles, <100 char, no clickbait. Pehla = best."""
        data = self.llm.json(
            f"""Tum YouTube SEO expert ho. Is video ke liye 5 title variations do.

TOPIC: {topic}
LANGUAGE: {CONFIG.get('language', 'Hindi')}
SCRIPT (context): {script_text[:600]}

RULES:
- Har title 100 character se KAM (ideal 50-70)
- Front-load keywords (pehle 40 char sabse important — search mein wahi dikhte hain)
- Curiosity gap YES, jhooth/clickbait NO ("you won't believe" type banned)
- Number ya specific detail ho to better

JSON: {{"titles": ["t1", "t2", "t3", "t4", "t5"]}}""")
        raw = data.get("titles") or []
        titles = []
        for t in raw:
            t = str(t).strip()
            if not t:
                continue
            t = t[:LIMITS["title_max"] - 5]  # thodi saans ki jagah
            if t not in titles:
                titles.append(t)
        while len(titles) < 5:               # LLM kam de to topic se bhar do
            n = len(titles) + 1
            titles.append(f"{topic}"[:90] + (f" — Part {n}" if n > 1 else ""))
        log.info("5 titles ready", best=titles[0][:60])
        return titles[:5]

    # ==================================================================
    # 2. DESCRIPTION
    # ==================================================================
    def description(self, topic: str, title: str, script_text: str = "",
                    tags: list[str] | None = None,
                    timestamps: list[tuple[str, str]] | None = None) -> str:
        """
        SEO description: hook para + timestamps + CTA + social links +
        credits + hashtags. Sab config se aata hai, kuch hardcode nahi.
        """
        data = self.llm.json(
            f"""YouTube video description ka sirf OPENING paragraph likho (2-3 sentences).
TOPIC: {topic}
TITLE: {title}
LANGUAGE: {CONFIG.get('language', 'Hindi')}
Pehli line mein main keyword aaye (search snippet mein dikhti hai).
JSON: {{"opening": "..."}}""")
        opening = str(data.get("opening") or f"{title} — poori kahani is video mein.").strip()

        parts = [opening, ""]

        # ---- timestamps (chapters) — diye ho to hi ----
        if timestamps:
            parts.append("⏱️ Chapters:")
            for ts, label in timestamps:
                parts.append(f"{ts} {label}")
            parts.append("")

        # ---- CTA ----
        parts += ["👉 Aisi hi videos ke liye SUBSCRIBE karo aur bell 🔔 dabao!",
                  "Comment mein batao — aage kaunsi kahani suno-ge?", ""]

        # ---- social links (config se; TODO-placeholder skip) ----
        links = []
        ig = str(CONFIG.get("instagram_handle") or "")
        yt = str(CONFIG.get("youtube_channel") or "")
        if ig and "your_handle" not in ig:
            links.append(f"📸 Instagram: https://instagram.com/{ig.lstrip('@')}")
        if yt and "your_channel" not in yt:
            links.append(f"▶️ Channel: {yt}")
        if links:
            parts += links + [""]

        # ---- credits + AI disclosure (hard constraint #4 description mein bhi) ----
        brand = CONFIG.get("brand_name", "AUTOPILOT")
        parts += [f"🎬 Created by {brand}",
                  "⚠️ Ye video AI-assisted hai (AI narration/illustration).", ""]

        # ---- hashtags (pehle 3 title ke upar dikhte hain) ----
        tag_line = " ".join(f"#{t.lstrip('#').replace(' ', '')}" for t in (tags or [])[:5])
        if tag_line:
            parts.append(tag_line)

        desc = "\n".join(parts)[:LIMITS["desc_max"] - 100]
        log.info("Description ready", chars=len(desc))
        return desc

    # ==================================================================
    # 3. TAGS — 15-30, dedupe, relevance-ranked
    # ==================================================================
    def tags(self, topic: str, title: str, script_text: str = "") -> list[str]:
        """15-30 tags. Dedupe (case-insensitive), relevance rank, 500-char cap."""
        data = self.llm.json(
            f"""YouTube tags do is video ke liye (SEO).
TOPIC: {topic}
TITLE: {title}
LANGUAGE: {CONFIG.get('language', 'Hindi')}
25-30 tags — sabse relevant PEHLE. Mix: exact keywords, long-tail phrases,
{CONFIG.get('language', 'Hindi')} + English dono. Har tag 3 shabd se kam ho to behtar.
JSON: {{"tags": ["tag1", "tag2", ...]}}""")
        raw = [str(t).strip().lstrip("#") for t in (data.get("tags") or [])]

        # dedupe — order preserve (order hi relevance rank hai, LLM ne ranked diye)
        seen: set[str] = set()
        tags: list[str] = []
        for t in raw:
            k = t.lower()
            if t and k not in seen and len(t) <= LIMITS["tag_max_chars"]:
                seen.add(k)
                tags.append(t)

        # fallback padding — topic ke shabdon se (mock/LLM-fail mein bhi 15+ mile)
        if len(tags) < 15:
            for w in re.findall(r"\w{4,}", f"{topic} {title}".lower()):
                if w not in seen:
                    seen.add(w)
                    tags.append(w)
                if len(tags) >= 15:
                    break

        # 500-char total cap — YouTube poora set reject kar deta hai isse upar
        out, total = [], 0
        for t in tags[:LIMITS["tags_max"]]:
            cost = len(t) + 2   # YouTube quotes/commas bhi ginta hai approx
            if total + cost > LIMITS["tags_total_chars"]:
                break
            out.append(t)
            total += cost
        log.info(f"{len(out)} tags ready", chars=total)
        return out

    # ==================================================================
    # 4. THUMBNAIL METADATA
    # ==================================================================
    def thumbnail_meta(self, topic: str, title: str) -> dict:
        """Thumbnail design brief — structured JSON (ArtDirector/insaan ke liye)."""
        data = self.llm.json(
            f"""Ek YouTube thumbnail ka design brief do.
TOPIC: {topic}
TITLE: {title}
STYLE: {CONFIG.get('visual_style', 'flat 2D cartoon')}
Thumbnail text 3-5 shabd (mobile pe padhna hai). Emotion strong ho.
JSON: {{"thumbnail_title": "3-5 shabd", "thumbnail_subtitle": "chhota supporting text",
"colors": ["#hex1", "#hex2", "#hex3"], "visual_concept": "ek line — kya dikhe",
"emotion": "curiosity|fear|surprise|joy", "hook": "kyun click karega"}}""")
        out = {
            "thumbnail_title": str(data.get("thumbnail_title") or title.split("—")[0])[:40],
            "thumbnail_subtitle": str(data.get("thumbnail_subtitle") or "")[:60],
            "colors": [str(c) for c in (data.get("colors") or
                                        ["#0d1117", "#e05d2d", "#2da3a8"])][:4],
            "visual_concept": str(data.get("visual_concept")
                                  or f"{CONFIG.get('visual_style', '')} — {topic}")[:200],
            "emotion": str(data.get("emotion") or "curiosity"),
            "hook": str(data.get("hook") or "curiosity gap")[:120],
        }
        log.info("Thumbnail brief ready", emotion=out["emotion"])
        return out

    # ==================================================================
    # 5. CATEGORY DETECTION
    # ==================================================================
    def detect_category(self, topic: str, title: str = "",
                        script_text: str = "") -> tuple[str, str]:
        """
        Return: (category_name, category_id).
        Pehle deterministic keywords (free, instant), phir LLM tie-break.
        """
        text = f"{topic} {title} {script_text[:300]}".lower()
        for keywords, cat in _CATEGORY_KEYWORDS:
            if any(k in text for k in keywords):
                log.info(f"Category (keyword match): {cat}", id=CATEGORIES[cat])
                return cat, CATEGORIES[cat]

        # keywords se nahi mila — LLM se poochho
        data = self.llm.json(
            f"""Is YouTube video ki category batao.
TOPIC: {topic}
TITLE: {title}
Options: {", ".join(CATEGORIES)}
JSON: {{"category": "exact option text"}}""")
        cat = str(data.get("category") or "").strip().lower()
        if cat not in CATEGORIES:
            cat = "entertainment"   # niche ka safe default
        log.info(f"Category (LLM): {cat}", id=CATEGORIES[cat])
        return cat, CATEGORIES[cat]

    # ==================================================================
    # 6. LANGUAGE DETECTION
    # ==================================================================
    @staticmethod
    def detect_language(text: str) -> str:
        """
        BCP-47 code lautao. Script-range heuristic — LLM ki zaroorat nahi
        (deterministic, free, offline). Devanagari >15% -> 'hi', warna 'en'.
        Hinglish (roman Hindi) 'hi-Latn' hota hai par YouTube 'hi' hi leta hai.
        """
        if not text:
            return "en"
        dev = len(_DEVANAGARI.findall(text))
        ratio = dev / max(1, len(re.sub(r"\s", "", text)))
        lang = "hi" if ratio > 0.15 else "en"
        cfg_lang = str(CONFIG.get("language", "")).lower()
        # config Hindi/Hinglish bole aur text roman ho — phir bhi 'hi' audio hai
        if lang == "en" and cfg_lang.startswith("hi") and dev == 0:
            lang = "hi" if cfg_lang == "hindi" else "en"
        return lang

    # ==================================================================
    # 7. SCHEDULING (timezone-aware)
    # ==================================================================
    @staticmethod
    def schedule_time(when: str | None = None, tz: str | None = None) -> str | None:
        """
        Human input -> ISO 8601 UTC (YouTube publishAt format).
          None / "now"           -> None (immediate)
          "2026-08-06 18:30"     -> config timezone (ya tz) maan kar UTC
          "+3h" / "+45m" / "+2d" -> ab se relative
          ISO with offset        -> pass-through (UTC mein convert)
        """
        if not when or str(when).lower() in ("now", "immediate", ""):
            return None
        s = str(when).strip()
        zone = ZoneInfo(tz or str(CONFIG.get("timezone", "UTC")))

        m = re.fullmatch(r"\+(\d+)([mhd])", s)
        if m:                                     # relative: +3h
            n, unit = int(m.group(1)), m.group(2)
            delta = {"m": timedelta(minutes=n), "h": timedelta(hours=n),
                     "d": timedelta(days=n)}[unit]
            dt = datetime.now(timezone.utc) + delta
        else:
            try:
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            except ValueError as e:
                raise MetadataError(
                    f"Schedule time samajh nahi aaya: '{when}'.\n"
                    f"Formats: '2026-08-06 18:30' (local), '+3h', '+30m', '+2d', ISO 8601"
                ) from e
            if dt.tzinfo is None:                 # naive = config timezone
                dt = dt.replace(tzinfo=zone)
            dt = dt.astimezone(timezone.utc)

        if dt <= datetime.now(timezone.utc) + timedelta(minutes=2):
            raise MetadataError(
                f"Schedule time past/abhi ka hai: {dt.isoformat()}. "
                f"Future time do (kam se kam 15 min aage rakhna safe hai).")
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ==================================================================
    # 9. VALIDATION
    # ==================================================================
    @staticmethod
    def validate(meta: dict, video_path: str | Path | None = None,
                 thumbnail: str | Path | None = None) -> list[str]:
        """
        Upload se pehle sab check karo. Return: problems list (khaali = sab OK).
        Raise nahi karta — caller decide kare block karna hai ya warn.
        """
        problems: list[str] = []
        title = meta.get("title") or ""
        desc = meta.get("description") or ""
        tags = meta.get("tags") or []

        if not title.strip():
            problems.append("Title khaali hai")
        if len(title) > LIMITS["title_max"]:
            problems.append(f"Title {len(title)} chars — max {LIMITS['title_max']}")
        if "<" in title or ">" in title:
            problems.append("Title mein < > allowed nahi (YouTube reject karega)")
        if len(desc) > LIMITS["desc_max"]:
            problems.append(f"Description {len(desc)} chars — max {LIMITS['desc_max']}")
        if len(tags) > LIMITS["tags_max"]:
            problems.append(f"{len(tags)} tags — max {LIMITS['tags_max']}")
        total = sum(len(t) + 2 for t in tags)
        if total > LIMITS["tags_total_chars"]:
            problems.append(f"Tags total {total} chars — max {LIMITS['tags_total_chars']}")
        for w in CLICKBAIT_WORDS:
            if w in title.lower():
                problems.append(f"Clickbait phrase title mein: '{w}'")

        if video_path is not None:
            p = Path(video_path)
            if not p.exists():
                problems.append(f"Video file nahi mili: {p}")
            elif p.stat().st_size == 0:
                problems.append(f"Video file khaali hai: {p}")
            elif p.suffix.lower() not in (".mp4", ".mov", ".m4v"):
                problems.append(f"Video format '{p.suffix}' YouTube pe nahi jaata")

        if thumbnail is not None:
            t = Path(thumbnail)
            if not t.exists():
                problems.append(f"Thumbnail nahi mili: {t}")
            elif t.stat().st_size > LIMITS["thumb_max_bytes"]:
                problems.append(f"Thumbnail {t.stat().st_size/1024/1024:.1f}MB — max 2MB")
            elif t.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                problems.append(f"Thumbnail format '{t.suffix}' — jpg/png chahiye")

        return problems

    # ==================================================================
    # 10. SEO SCORE
    # ==================================================================
    @staticmethod
    def seo_score(meta: dict) -> dict:
        """
        Deterministic SEO score /100 — HEURISTIC hai, ranking guarantee nahi
        (jo cheez hum control karte hain sirf wahi ginte hain).
        Return: {"score", "deductions": [(points, reason)], "suggestions": [...]}
        """
        title = meta.get("title") or ""
        desc = meta.get("description") or ""
        tags = meta.get("tags") or []
        deductions: list[tuple[int, str]] = []
        suggestions: list[str] = []

        # ---- title (40 points ka hissa) ----
        if not 20 <= len(title) <= 70:
            deductions.append((10, f"Title {len(title)} chars (ideal 20-70)"))
            suggestions.append("Title 50-70 char rakho — search mein poora dikhega")
        if not re.search(r"\d", title):
            deductions.append((5, "Title mein koi number nahi"))
            suggestions.append("Number/specific detail CTR badhata hai ('14 log', '3 raaz')")
        first_tag = (tags[0].lower() if tags else "")
        if first_tag and first_tag not in title.lower():
            deductions.append((8, "Main keyword (tag #1) title mein nahi"))
            suggestions.append(f"'{tags[0]}' ko title mein laao — search match strong hoga")

        # ---- description (30 points ka hissa) ----
        if len(desc) < 200:
            deductions.append((10, f"Description sirf {len(desc)} chars (min 200 accha)"))
            suggestions.append("Description 200+ chars karo — pehli 2 line search snippet hai")
        if "subscribe" not in desc.lower():
            deductions.append((5, "CTA (subscribe) missing"))
        if "#" not in desc:
            deductions.append((5, "Description mein hashtags nahi"))

        # ---- tags (30 points ka hissa) ----
        if len(tags) < 15:
            deductions.append((10, f"Sirf {len(tags)} tags (15-30 chahiye)"))
            suggestions.append("15+ tags do — long-tail phrases bhi (2-3 shabd wale)")
        long_tail = sum(1 for t in tags if " " in t)
        if tags and long_tail < len(tags) * 0.3:
            deductions.append((5, "Long-tail tags kam hain (multi-word)"))
            suggestions.append("30%+ tags multi-word rakho — competition kam, match zyada")

        score = max(0, 100 - sum(p for p, _ in deductions))
        return {"score": score, "deductions": deductions, "suggestions": suggestions,
                "note": "HEURISTIC score hai — ranking ki guarantee nahi, checklist hai"}

    # ==================================================================
    # BUILD — sab kuch ek saath (upload-ready package)
    # ==================================================================
    def build(self, topic: str, script_text: str = "",
              timestamps: list[tuple[str, str]] | None = None,
              save: bool = True) -> dict:
        """
        Poora metadata package banao. Har step apna fallback rakhta hai —
        LLM down ho to bhi valid (heuristic) package milta hai.
        """
        titles = self.titles(topic, script_text)
        title = titles[0]
        tags = self.tags(topic, title, script_text)
        description = self.description(topic, title, script_text, tags, timestamps)
        cat_name, cat_id = self.detect_category(topic, title, script_text)
        language = self.detect_language(script_text or f"{topic} {title}")
        thumb = self.thumbnail_meta(topic, title)

        pkg = {
            "topic": topic,
            "title": title,
            "titles": titles,
            "description": description,
            "tags": tags,
            "category": cat_name,
            "category_id": cat_id,
            "language": language,
            "thumbnail_meta": thumb,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "llm_backend": self.llm.backend.name,
        }
        pkg["seo"] = self.seo_score(pkg)
        pkg["validation"] = self.validate(pkg)

        log.audit("metadata_built", topic=topic[:60], seo=pkg["seo"]["score"],
                  category=cat_name, language=language, tags=len(tags))
        if save:
            self._save(pkg)
        return pkg

    def _save(self, pkg: dict) -> Path:
        """Package ko logs/metadata/ mein JSON file mein rakho (audit + reuse)."""
        out_dir = Path(CONFIG["log_dir"]) / "metadata"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r"\W+", "_", pkg["topic"].lower())[:40].strip("_") or "video"
        path = out_dir / f"{stamp}_{slug}.json"
        path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"Metadata save hua: {path.name}")
        return path

    # ==================================================================
    # SEO REPORT (insaan ke padhne layak)
    # ==================================================================
    @staticmethod
    def seo_report(pkg: dict) -> str:
        seo = pkg.get("seo") or {}
        lines = [f"📊 SEO SCORE: {seo.get('score', '?')}/100  ({seo.get('note', '')})", ""]
        if seo.get("deductions"):
            lines.append("Kata kahan:")
            lines += [f"  -{p:>2}  {r}" for p, r in seo["deductions"]]
        else:
            lines.append("  Koi deduction nahi — full marks!")
        if seo.get("suggestions"):
            lines.append("\nSudhaar:")
            lines += [f"  💡 {s}" for s in seo["suggestions"]]
        if pkg.get("validation"):
            lines.append("\n⚠️ Validation problems:")
            lines += [f"  ❌ {v}" for v in pkg["validation"]]
        return "\n".join(lines)


def generate_thumbnail(
    out_path: Path | str,
    title_text: str,
    subtitle_text: str = "",
    base_image_path: Path | str | None = None,
    colors: list[str] | None = None,
) -> Path:
    """
    1280x720 (16:9) high-CTR YouTube thumbnail banata hai.
    Pillow + Devanagari bold font overlay with high contrast.
    """
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    target_w, target_h = 1280, 720
    canvas = None

    if base_image_path and Path(base_image_path).exists():
        try:
            from PIL import Image
            img = Image.open(base_image_path).convert("RGB")
            bw, bh = img.size
            scale = max(target_w / bw, target_h / bh)
            nw, nh = int(bw * scale), int(bh * scale)
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - target_w) // 2
            top = (nh - target_h) // 2
            canvas = resized.crop((left, top, left + target_w, top + target_h))
        except Exception as e:
            log.warn(f"Base image load fail: {e}")
            canvas = None

    if canvas is None:
        from PIL import Image, ImageDraw
        bg_col = (13, 17, 23)
        canvas = Image.new("RGB", (target_w, target_h), color=bg_col)
        draw_temp = ImageDraw.Draw(canvas)
        draw_temp.rectangle([0, 0, target_w, 8], fill="#e05d2d")
        draw_temp.rectangle([0, target_h - 8, target_w, target_h], fill="#2da3a8")

    # Dark gradient banner on lower portion for text readability
    from PIL import Image, ImageDraw, ImageFont
    banner = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(banner)
    for y in range(360, target_h):
        alpha = int(220 * ((y - 360) / (target_h - 360)))
        bdraw.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))
    canvas.paste(banner, (0, 0), banner)

    # Devanagari bold font
    font_file = Path(CONFIG.get("_root", ".")) / "assets" / "fonts" / "NotoSansDevanagari-Bold.ttf"
    title_font = None
    sub_font = None
    if font_file.exists():
        try:
            title_font = ImageFont.truetype(str(font_file), 58)
            sub_font = ImageFont.truetype(str(font_file), 36)
        except Exception:
            pass
    if title_font is None:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw = ImageDraw.Draw(canvas)
    text = (title_text or "AUTOPILOT").strip()
    words = text.split()
    lines = []
    if len(words) > 6:
        lines.append(" ".join(words[:5]))
        lines.append(" ".join(words[5:10]))
    else:
        lines.append(text)

    start_y = target_h - 180 - (len(lines) * 65)
    if start_y < 350:
        start_y = 350

    curr_y = start_y
    for line in lines:
        draw.text(
            (60, curr_y),
            line,
            font=title_font,
            fill="#FFE500",
            stroke_width=5,
            stroke_fill="#000000"
        )
        curr_y += 65

    if subtitle_text:
        sub_line = subtitle_text[:45]
        draw.text(
            (62, curr_y + 10),
            sub_line,
            font=sub_font,
            fill="#FFFFFF",
            stroke_width=3,
            stroke_fill="#000000"
        )

    canvas.save(out_p, format="JPEG", quality=88, optimize=True)
    return out_p


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="AI metadata package banao (Phase 5)")
    ap.add_argument("topic", help="video ka topic")
    ap.add_argument("--script", default="", help="script text (context ke liye)")
    a = ap.parse_args()
    agent = MetadataAgent()
    p = agent.build(a.topic, a.script)
    print(json.dumps(p, indent=2, ensure_ascii=False))
    print("\n" + agent.seo_report(p))
