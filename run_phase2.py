#!/usr/bin/env python3
"""
run_phase2.py — Phase 2 ka end-to-end runner.

Kya karta hai:
    topic -> Writer (script) -> ArtDirector (scenes) -> ImageGen (JPGs)
          -> Voice (narration + timing) -> ek folder disk pe

Phase 2 ka "done" ka matlab (Section 10):
    "Ek folder mein 8 images + 1 mp3"   ✅ yahi banta hai

Chalao:
    python run_phase2.py                          # topic khud maang lega/mock
    python run_phase2.py --topic "koi kahani"
    python run_phase2.py --dry-run                # koi network nahi, sab placeholder
    python run_phase2.py --no-images              # sirf script + voice (tez)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.artdirector import ArtDirector, TEMPLATES  # noqa: E402
from agents.trendscout import TrendScout                # noqa: E402
from agents.imagegen import ImageGen                   # noqa: E402
from agents.voice import Voice                         # noqa: E402
from agents.writer import Writer                       # noqa: E402
from core.config import CONFIG                         # noqa: E402
from core.db import DB                                 # noqa: E402
from core.llm import LLM                               # noqa: E402
from core.logbook import Logbook                       # noqa: E402

log = Logbook("chief")

# Fallback topics — TrendScout fail ho jaye tabhi use hote hain
SEED_TOPICS = [
    "Ek gaon jahan se chaudah log ek hi raat mein gayab ho gaye",
    "Wo train jo 1911 mein nikli aur kabhi pahunchi hi nahi",
    "Ek chithi jo likhi jaane se pehle hi mil gayi thi",
    "Wo kamra jise 40 saal se kisi ne khola nahi",
    "Ek phone number jo har raat 3:33 baje call karta tha",
]


def make_video(topic: str | None = None, *, dry_run: bool = False,
               with_images: bool = True, voice: str | None = None) -> dict:
    t0 = time.time()
    db = DB()
    llm = LLM(force_mock=True if dry_run else None)

    # ---------- topic: TrendScout se ----------
    series = None
    if not topic:
        try:
            scout = TrendScout(db, llm)
            cands = scout.scout(3)
            if cands:
                best = cands[0]
                series = best.get("series")
                topic = best.get("topic")
                if not topic and series:
                    # series continuation — topic LLM se, par series naam ke saath
                    nxt = [c for c in cands if c.get("topic")]
                    topic = nxt[0]["topic"] if nxt else scout._fallback_topic()
                log.info(f"🔍 TrendScout: score {best['score']:.2f} "
                         f"[{best['source']}] — {best.get('why', '')[:60]}")
        except Exception as e:  # noqa: BLE001
            log.warn(f"TrendScout fail — seed topic use kar rahe hain: {str(e)[:120]}")
        if not topic:
            used = {r["topic"] for r in db.recent_videos(30)}
            topic = next((t for t in SEED_TOPICS if t not in used), SEED_TOPICS[0])
    log.info(f"📌 Topic: {topic}")

    # ---------- 1. WRITER ----------
    log.info("✍️  Writer chal raha hai...")
    writer = Writer(db, llm)
    script = writer.write(topic)
    if series:
        # Section 8: series ka number TITLE mein dikhna chahiye — tabhi darshak
        # ko pata chalta hai ki aur episodes hain (binge behaviour).
        prefix = f"{series['name']} #{series['index']}"
        if prefix.lower() not in script["title"].lower():
            script["title"] = f"{prefix}: {script['title']}"[:95]
    log.ok(f"Script ready: '{script['title']}'",
           hook=script["hook_type"], words=script["word_count"], est=f"{script['est_sec']}s")

    # ---------- DB entry ----------
    vid = db.create_video(
        topic, title=script["title"], caption=script["caption"],
        hashtags=script["hashtags"], hook_type=script["hook_type"],
        script_json=script, length_sec=script["est_sec"], status="planned",
        series_name=(series or {}).get("name"),
        series_index=(series or {}).get("index"))
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"📁 Folder: {out_dir}")

    # ---------- 2. ART DIRECTOR ----------
    log.info("🎨 ArtDirector scenes bana raha hai...")
    ad = ArtDirector(db, llm)
    art = ad.direct(script)
    db.update_video(vid, template_id=art["template_id"])
    log.ok(f"{art['n_scenes']} scenes, template = {art['template_name']}")

    # ---------- 3. VOICE ----------
    log.info("🎙️  Voice narration bana rahi hai...")
    voice_agent = Voice(db)
    narration = voice_agent.narrate(writer.lines(script), out_dir, profile_id=voice)
    db.update_video(vid, voice_id=narration["voice_id"],
                    length_sec=narration["duration_sec"])

    # ---------- 4. IMAGES ----------
    scenes = art["scenes"]
    if with_images:
        log.info(f"🖼️  {len(scenes)} images bana rahe hain (thoda time lagega)...")
        providers = ["local_placeholder"] if dry_run else None
        scenes = ImageGen(providers).generate_all(scenes, out_dir, seed_base=vid * 100)
    else:
        log.warn("--no-images: images skip ki gayi")

    # ---------- 5. SCENE TIMING (image ko audio se match karo) ----------
    scenes = assign_scene_timing(scenes, narration)

    # ---------- 6. MANIFEST — Phase 3 (render.py) isse padhega ----------
    manifest = {
        "video_id": vid,
        "topic": topic,
        "script": script,
        "art": {k: v for k, v in art.items() if k != "scenes"},
        "scenes": scenes,
        "narration": {k: v for k, v in narration.items() if k != "words"},
        "words": narration["words"],
        "render_spec": {   # Section 5 ka spec — Phase 3 yahi follow karega
            "resolution": CONFIG["resolution"], "fps": 30, "crf": 21,
            "vcodec": "libx264", "pix_fmt": "yuv420p",
            "acodec": "aac", "abitrate": "128k", "ar": 44100,
            "loudness_lufs": -14,
        },
        "built_in_sec": round(time.time() - t0, 1),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    db.set_status(vid, "scripted", note=f"Phase 2 done: {len(scenes)} scenes")
    db.log_event("phase2_done", "chief", vid, folder=str(out_dir))

    report(manifest, out_dir)
    db.close()
    return manifest


def assign_scene_timing(scenes: list[dict], narration: dict) -> list[dict]:
    """
    Har scene ko ek time window do.

    Rule (Section 5 #2): "beat-matched cuts — narration ke natural pause pe cut karo,
    fixed timing pe nahi." Isliye cut points line boundaries pe lagte hain.

    Do case handle karne hote hain:
      A) lines >= scenes  -> lines ko groups mein baanto, group boundaries pe cut
      B) lines <  scenes  -> (aksar yahi hota hai: 5 lines, 7 scenes)
         lambi lines ko beech se todo taaki har scene ko time mile.
         Bina iske aakhri scenes ko 0 second milta tha aur wo video mein dikhte hi nahi the.
    """
    lines = narration.get("lines") or []
    total = float(narration.get("duration_sec") or 0)
    n = len(scenes)
    if n == 0:
        return scenes
    if not lines or total <= 0:
        # koi timing info nahi — barabar baant do
        step = max(1.0, total or n * 4.0) / n
        return [{**sc, "start": round(i * step, 3), "end": round((i + 1) * step, 3),
                 "dur": round(step, 3)} for i, sc in enumerate(scenes)]

    # ---- saare candidate cut points = line boundaries ----
    cuts = [ln["end"] for ln in lines[:-1]]

    # ---- CASE B: scenes zyada hain -> lambi lines ko todo ----
    MIN_SCENE = 1.5   # isse chhota scene dikhta hi nahi (Ken Burns ke liye time chahiye)
    while len(cuts) < n - 1:
        # sabse lambe segment ko beech se todo
        bounds = [0.0, *sorted(cuts), total]
        widths = [(bounds[i + 1] - bounds[i], i) for i in range(len(bounds) - 1)]
        widest, idx = max(widths)
        if widest < MIN_SCENE * 2:
            break   # aur todne se scenes bahut chhote ho jayenge
        cuts.append(round((bounds[idx] + bounds[idx + 1]) / 2, 3))

    # ---- CASE A: cuts zyada hain -> sabse chhote segments merge karo ----
    cuts = sorted(cuts)
    while len(cuts) > n - 1:
        bounds = [0.0, *cuts, total]
        widths = [(bounds[i + 1] - bounds[i], i) for i in range(len(bounds) - 1)]
        _, idx = min(widths)
        # us segment ka koi ek boundary hata do
        drop = cuts[idx] if idx < len(cuts) else cuts[-1]
        cuts.remove(drop)

    # ---- agar phir bhi kam cuts hain (bahut chhota audio) to scenes kam kar do ----
    if len(cuts) < n - 1:
        keep = len(cuts) + 1
        log.warn(f"Audio chhota hai — {n} ki jagah {keep} scenes use ho rahe hain "
                 f"(har scene kam se kam {MIN_SCENE}s ka hona chahiye)")
        scenes = scenes[:keep]
        n = keep

    bounds = [0.0, *cuts, total]
    out = []
    for i, sc in enumerate(scenes):
        start, end = bounds[i], bounds[i + 1]
        out.append({**sc, "start": round(start, 3), "end": round(end, 3),
                    "dur": round(end - start, 3)})

    # sanity: koi bhi scene 0 second ka nahi hona chahiye
    bad = [s["n"] for s in out if s["dur"] < 0.5]
    if bad:
        log.error(f"Scenes {bad} ko time nahi mila — ye bug hai, report karo")
    return out


def report(m: dict, out_dir: Path):
    s, n = m["script"], m["narration"]
    print("\n" + "=" * 68)
    print(f"  ✅ PHASE 2 COMPLETE — video #{m['video_id']}")
    print("=" * 68)
    print(f"  Title      : {s['title']}")
    print(f"  Hook type  : {s['hook_type']}  ({s['hook_line'][:52]}...)")
    print(f"  Overlay    : \"{s['hook_text_overlay']}\"")
    print(f"  Template   : {m['art']['template_name']}  ({m['art']['template_id']})")
    print(f"  Voice      : {n['voice_id']}  [{n['voice']} rate={n['rate']} pitch={n['pitch']}]")
    print(f"  Duration   : {n['duration_sec']}s   (target {s['target_length_sec']}s, "
          f"sweet spot 22-45s)")
    print(f"  Scenes     : {len(m['scenes'])}   Words: {len(m['words'])}")
    print(f"  Hashtags   : {' '.join(s['hashtags'])}")
    print(f"  Comment bait: {s['comment_bait'][:60]}...")
    print(f"  Built in   : {m['built_in_sec']}s")
    print("-" * 68)
    imgs = sorted(out_dir.glob("scene_*.jpg"))
    mp3 = out_dir / "narration.mp3"
    print(f"  📁 {out_dir}")
    print(f"     scene_*.jpg   : {len(imgs)} files"
          f" ({sum(p.stat().st_size for p in imgs)//1024} KB)"
          if imgs else "     scene_*.jpg   : 0 ⚠️")
    print(f"     narration.mp3 : {'✅ ' + str(mp3.stat().st_size//1024) + ' KB' if mp3.exists() else '❌'}")
    print(f"     timing.json   : {'✅' if (out_dir/'timing.json').exists() else '❌'}")
    print(f"     manifest.json : ✅")
    if s.get("warnings"):
        print("-" * 68)
        for w in s["warnings"]:
            print(f"  ⚠️  {w}")
    providers = {sc.get("provider") for sc in m["scenes"] if sc.get("provider")}
    if "local_placeholder" in providers:
        print("  ⚠️  PLACEHOLDER images use hui — ye publish layak NAHI hain.")
    print("=" * 68)
    print("  Agla step: Phase 3 — render.py (ffmpeg se in sabko MP4 banana)\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="AUTOPILOT Phase 2 runner")
    ap.add_argument("--topic", help="video ka topic (na do to seed list se uthega)")
    ap.add_argument("--voice", help="voice profile (e.g. hi_m_grave, hi_f_calm)")
    ap.add_argument("--dry-run", action="store_true", help="koi network call nahi")
    ap.add_argument("--no-images", action="store_true", help="images skip karo (tez test)")
    a = ap.parse_args()
    try:
        make_video(a.topic, dry_run=a.dry_run, with_images=not a.no_images, voice=a.voice)
    except KeyboardInterrupt:
        log.warn("User ne rok diya")
    except Exception as e:  # noqa: BLE001
        log.fatal("Phase 2 crash ho gaya", e)
        sys.exit(1)
