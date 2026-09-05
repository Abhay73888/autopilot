#!/usr/bin/env python3
"""
run.py — EK COMMAND SE POORA VIDEO.

    python run.py                                  # ek video banao
    python run.py --topic "Wo train jo kabhi..."   # apna topic do
    python run.py --dry-run                        # bina network ke test
    python run.py --render-only 3                  # video #3 sirf dobara render karo
    python run.py --count 2                        # 2 videos banao

Acceptance test (Section 12): "Ek command se end-to-end video banta hai,
bina manual step ke" ✅ — yahi wo command hai.

Kya hota hai:
    Phase 2  (script -> images -> narration)
       ↓
    Phase 3  (ffmpeg render -> final.mp4)
       ↓
    output/video_XXXX/final.mp4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import CONFIG        # noqa: E402
from core.db import DB                # noqa: E402
from core.ffmpeg import FFmpegMissing, capabilities, ffmpeg_bin  # noqa: E402
from core.logbook import Logbook      # noqa: E402
from pipeline.render import Renderer  # noqa: E402
from pipeline.validate import validate_dir  # noqa: E402
from run_phase2 import make_video     # noqa: E402

log = Logbook("chief")


def preflight() -> bool:
    """Chalane se pehle check karo ki sab tools hain. Beginner ko saaf batao."""
    ok = True
    print("\n🔍 PREFLIGHT CHECK")
    print("-" * 60)

    try:
        ffmpeg_bin()
        caps = capabilities()
        print(f"  ✅ ffmpeg          {'(system)' if 'imageio' not in ffmpeg_bin() else '(pip bundled)'}")
        if not caps["libx264"]:
            print("  ❌ libx264 nahi hai — Instagram H.264 maangta hai. Dusra build install karo.")
            ok = False
        if not caps["aac"]:
            print("  ❌ AAC encoder nahi hai — Instagram AAC maangta hai.")
            ok = False
        if not caps["ass"]:
            print("  ⚠️  libass nahi hai — SUBTITLES NAHI LAGENGE. "
                  "60% log sound off pe dekhte hain, ye bada nuksaan hai.")
        if not caps["loudnorm"]:
            print("  ⚠️  loudnorm nahi hai — audio -14 LUFS pe normalize nahi hoga.")
    except FFmpegMissing as e:
        print(f"  ❌ ffmpeg\n{e}")
        ok = False

    font = Path(CONFIG["_root"]) / "assets" / "fonts" / "NotoSansDevanagari-Bold.ttf"
    if font.exists():
        print("  ✅ Devanagari font")
    else:
        print("  ⚠️  Devanagari font nahi mila — Hindi subtitles ☐☐☐ boxes dikhenge.\n"
              "     Fix: SETUP.md STEP 5b dekho")

    try:
        import edge_tts  # noqa: F401
        print("  ✅ edge-tts")
    except ImportError:
        print("  ⚠️  edge-tts nahi hai — `pip install edge-tts` (awaaz ke liye zaroori)")

    import os
    if CONFIG.get("mock_mode"):
        print("  ⚠️  MOCK MODE ON — content ghisa-pita hoga, publish layak nahi.\n"
              "     Fix: .env mein GEMINI_API_KEY daalo + config.yaml mein mock_mode: false")
    elif not os.environ.get("GEMINI_API_KEY"):
        print("  ⚠️  GEMINI_API_KEY nahi mili — mock pe girega")
    else:
        print("  ✅ Gemini API key")

    print("-" * 60)
    return ok


def one_video(topic: str | None, *, dry_run: bool, with_images: bool,
              preset: str, keep_temp: bool) -> dict | None:
    t0 = time.time()

    # ---------- PHASE 2 ----------
    manifest = make_video(topic, dry_run=dry_run, with_images=with_images)
    vid = manifest["video_id"]
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{vid:04d}"

    # ---------- PHASE 3 ----------
    log.info("🎬 Render shuru — ffmpeg kaam kar raha hai, ruko...")
    db = DB()
    try:
        info = Renderer(manifest).render(out_dir, preset=preset, keep_temp=keep_temp)
        db.update_video(vid, video_path=info["video_path"],
                        cover_path=info["cover_path"],
                        length_sec=info["duration_sec"], status="rendered")
        db.log_event("rendered", "chief", vid, **info)
    except Exception as e:  # noqa: BLE001
        db.set_status(vid, "failed", note=f"render fail: {str(e)[:200]}")
        db.log_event("render_failed", "chief", vid, error=str(e)[:500])
        log.error("Render fail ho gaya", e)
        db.close()
        return None

    manifest["render"] = info
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- PHASE 4: VALIDATE (publish se pehle gatekeeper) ----------
    log.info("🔍 Validate — format/loudness/spec check...")
    rep = validate_dir(out_dir)
    manifest["validation"] = rep.to_dict()
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if rep.ok:
        # review_first hai to insaan ke approve ka intezaar; auto_publish hai to seedha aage
        db.set_status(vid, "validated",
                      note=f"validate pass ({len(rep.warns)} warning)")
    else:
        db.set_status(vid, "failed",
                      note=f"validate FAIL: {rep.fatals[0].code}")
    db.log_event("validated", "chief", vid, ok=rep.ok, issues=len(rep.issues))
    db.close()

    final_report(manifest, info, time.time() - t0, rep)
    return info


def render_only(video_id: int, preset: str, keep_temp: bool):
    """Sirf dobara render karo — script/images/audio wahi rakho (tez iteration)."""
    out_dir = Path(CONFIG["_root"]) / "output" / f"video_{video_id:04d}"
    mf = out_dir / "manifest.json"
    if not mf.exists():
        log.error(f"manifest.json nahi mila: {mf}")
        return
    info = Renderer(mf).render(out_dir, preset=preset, keep_temp=keep_temp)
    m = json.loads(mf.read_text(encoding="utf-8"))
    m["render"] = info
    rep = validate_dir(out_dir)
    m["validation"] = rep.to_dict()
    mf.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    with DB() as db:
        if db.get_video(video_id):
            db.update_video(video_id, video_path=info["video_path"],
                            cover_path=info["cover_path"],
                            status="validated" if rep.ok else "failed")
    final_report(m, info, 0, rep)


def final_report(manifest: dict, info: dict, elapsed: float, rep=None):
    s = manifest["script"]
    n = manifest["narration"]
    dur = info["duration_sec"]

    print("\n" + "=" * 68)
    print(f"  🎬 VIDEO READY — #{manifest['video_id']}")
    print("=" * 68)
    print(f"  {info['video_path']}")
    print(f"  {info['size_mb']} MB · {info['resolution']} · {dur}s · "
          f"{info['vcodec']}+{info['acodec']}")
    print("-" * 68)
    print(f"  Title    : {s['title']}")
    print(f"  Hook     : [{s['hook_type']}] {s['hook_line'][:48]}")
    print(f"  Overlay  : \"{s['hook_text_overlay']}\"")
    print(f"  Template : {manifest['art']['template_name']}")
    print(f"  Voice    : {n['voice_id']}")
    print(f"  Scenes   : {info['n_scenes']} · Subtitles: {len(manifest.get('words', []))} words")
    engines = n.get("engines_used", [])
    if "silence" in engines:
        silent_count = sum(1 for ln in n.get("lines", []) if ln.get("engine") == "silence") or 1
        print(f"  ⚠️  Narration mein {silent_count} lines silent hain — ye video publish layak NAHI hai. "
              f"TTS fix karo (SETUP.md STEP 4).")
    print("-" * 68)

    # ---- validate.py ka poora report (Section 12 ke acceptance points) ----
    if rep is not None:
        f = rep.facts
        print(f"  {'✅ VALIDATE PASS' if rep.ok else '❌ VALIDATE FAIL'}"
              f"   {f.get('lufs','?')} LUFS · TP {f.get('true_peak','?')} dBTP")
        if not rep.issues:
            print("  ✅ Koi problem nahi mili")
        for i in rep.issues:
            icon = {"FATAL": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}[i.level]
            print(f"  {icon} [{i.code}] {i.msg[:88]}")
            if i.fix:
                print(f"      → {i.fix[:88]}")
        if not rep.ok:
            print("\n  🚫 YE VIDEO PUBLISH MAT KARNA — upar wale ❌ pehle theek karo")
    else:
        for ok, label in [
            (22 <= dur <= 45, f"Length {dur}s (22-45s sweet spot)"),
            (info["resolution"] == "1080x1920", f"Resolution {info['resolution']}"),
            (info["vcodec"] in ("h264", "?"), f"Codec {info['vcodec']}+{info['acodec']}"),
        ]:
            print(f"  {'✅' if ok else '❌'} {label}")

    if elapsed:
        print("-" * 68)
        print(f"  ⏱️  Total {elapsed:.0f}s")
    print("=" * 68)
    print("  Dekhne/approve karne ke liye dashboard kholo:  python -m web.server\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="AUTOPILOT — ek command se video")
    ap.add_argument("--topic", help="video ka topic")
    ap.add_argument("--count", type=int, default=1, help="kitne videos banane hain")
    ap.add_argument("--dry-run", action="store_true", help="koi network call nahi")
    ap.add_argument("--no-images", action="store_true", help="images skip (tez test)")
    ap.add_argument("--render-only", type=int, metavar="ID",
                    help="sirf dobara render karo (video id do)")
    ap.add_argument("--preset", default="veryfast",
                    help="x264 preset: ultrafast(tez/bada) .. slow(dheema/chhota)")
    ap.add_argument("--keep-temp", action="store_true", help="temp clips mat delete karo")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--dashboard", action="store_true",
                    help="banane ke baad dashboard khol do")
    a = ap.parse_args()

    if not a.skip_preflight and not preflight():
        log.fatal("Preflight fail — upar wale ❌ theek karke dobara chalao")
        sys.exit(1)

    try:
        if a.render_only:
            render_only(a.render_only, a.preset, a.keep_temp)
        else:
            for i in range(a.count):
                if a.count > 1:
                    log.info(f"===== VIDEO {i+1}/{a.count} =====")
                one_video(a.topic, dry_run=a.dry_run, with_images=not a.no_images,
                          preset=a.preset, keep_temp=a.keep_temp)
        if a.dashboard:
            from web.server import serve
            serve()
    except KeyboardInterrupt:
        log.warn("User ne rok diya")
    except Exception as e:  # noqa: BLE001
        log.fatal("Crash", e)
        sys.exit(1)
