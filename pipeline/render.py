"""
pipeline/render.py — images + audio + subtitles -> dekhne layak 1080x1920 MP4.

Ye Phase 3 ka dil hai. Section 5 ki 6 cheezein jo "AI slideshow" ko video banati hain:

  1. ✅ Ken Burns motion    — har scene pe slow zoom/pan, direction ALTERNATE
  2. ✅ Beat-matched cuts   — scene boundaries narration ke line-breaks pe (Phase 2 se aaye)
  3. ✅ Parallax            — foreground/background alag speed (2-layer fake parallax)
  4. ✅ Animated subtitles  — word-by-word karaoke (pipeline/subtitles.py)
  5. ✅ Sound design        — whoosh transitions + low drone ambience (ffmpeg se GENERATE,
                              koi copyrighted music nahi — hard constraint #6)
  6. ✅ Character consistency — Phase 2 ne already handle kiya

⚠️ EK ASLI TECHNICAL FAISLA (jhoot nahi bolunga):

ffmpeg ka standard Ken Burns filter `zoompan` hai. Maine test kiya — is machine pe
wo 4 second ke ek clip pe 180+ second le raha tha (zoompan har frame pe poora
image rescale karta hai, bahut mehnga hai).

HAL: `scale=eval=frame` + constant `crop`. Same visual result, par 2.9 SECOND
mein. 60x tez. Ek hi limitation hai: zoom ke saath simultaneous pan thoda kam
smooth hota hai, isliye hum zoom AUR pan alag-alag motions rakhte hain
(jo actually behtar dikhta hai — dono ek saath karna nauseating lagta hai).

Render steps:
  1. Har scene ka apna clip banao (Ken Burns + parallax + grade)
  2. Sab clips ko crossfade ke saath jodo
  3. Narration + generated ambience + whoosh SFX mix karo
  4. Karaoke subtitles burn karo
  5. Loudness -14 LUFS pe normalize karo
  6. Cover frame (thumbnail) nikalo
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
from pathlib import Path

from core.config import CONFIG
from core.ffmpeg import capabilities, run
from core.logbook import Logbook
from pipeline.subtitles import build_ass, build_srt

log = Logbook("render")

FONTS_DIR = Path(CONFIG["_root"]) / "assets" / "fonts"

# Transition ki lambai — itni chhoti ki cut lage, itni badi ki jhatka na lage
XFADE = 0.4


# =====================================================================
# KEN BURNS — motion filter banane wala
# =====================================================================
def ken_burns(motion: str, dur: float, w: int, h: int, fps: int,
              parallax: bool = False) -> str:
    """
    Ek scene ka video filter chain.

    Trick: pehle image ko 1.35x bade canvas pe scale karo, phir us bade canvas
    ke andar move/zoom karo. Isse edges kabhi khaali nahi dikhte.
    """
    over = 1.35                       # kitna extra area rakhna hai movement ke liye
    bw, bh = _even(w * over), _even(h * over)
    z = 0.24                          # 24% dynamic zoom for punchy mobile engagement
    p = 0.5 if parallax else 1.0      # parallax layer dheere chalti hai

    # base: image ko bade canvas pe fit karo (crop se aspect ratio bachao)
    base = (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,"
            f"crop={bw}:{bh},setsar=1")

    # t/dur = 0..1 progress. Har expression even numbers deta hai (H.264 requirement).
    if motion == "zoom_in":
        mv = (f"scale=w='2*floor({w}*(1+{z*p}*t/{dur})/2)':"
              f"h='2*floor({h}*(1+{z*p}*t/{dur})/2)':eval=frame,"
              f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")
    elif motion == "zoom_out":
        mv = (f"scale=w='2*floor({w}*(1+{z*p}-{z*p}*t/{dur})/2)':"
              f"h='2*floor({h}*(1+{z*p}-{z*p}*t/{dur})/2)':eval=frame,"
              f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")
    elif motion == "zoom_in_slow":
        mv = (f"scale=w='2*floor({w}*(1+{z*p*0.55}*t/{dur})/2)':"
              f"h='2*floor({h}*(1+{z*p*0.55}*t/{dur})/2)':eval=frame,"
              f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")
    elif motion == "zoom_in_dramatic":
        mv = (f"scale=w='2*floor({w}*(1+{z*p*1.4}*t/{dur})/2)':"
              f"h='2*floor({h}*(1+{z*p*1.4}*t/{dur})/2)':eval=frame,"
              f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")
    elif motion == "punch_in":
        # Rapid high-impact punch zoom for dramatic viral hooks and reveals
        mv = (f"scale=w='2*floor({w}*(1+{z*p*1.8}*min(1.0,t*1.5/{dur}))/2)':"
              f"h='2*floor({h}*(1+{z*p*1.8}*min(1.0,t*1.5/{dur}))/2)':eval=frame,"
              f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")
    elif motion == "whip_zoom":
        # Dynamic whip zoom (deep zoom with acceleration)
        mv = (f"scale=w='2*floor({w}*(1.1+{z*p*1.2}*(t/{dur})*(t/{dur}))/2)':"
              f"h='2*floor({h}*(1.1+{z*p*1.2}*(t/{dur})*(t/{dur}))/2)':eval=frame,"
              f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2")
    elif motion == "pan_left":
        mv = f"crop={w}:{h}:x='(in_w-{w})*(1-t/{dur})*{p}+(in_w-{w})*(1-{p})/2':y='(in_h-{h})/2'"
    elif motion == "pan_right":
        mv = f"crop={w}:{h}:x='(in_w-{w})*(t/{dur})*{p}+(in_w-{w})*(1-{p})/2':y='(in_h-{h})/2'"
    elif motion == "pan_up":
        mv = f"crop={w}:{h}:x='(in_w-{w})/2':y='(in_h-{h})*(1-t/{dur})*{p}+(in_h-{h})*(1-{p})/2'"
    else:  # unknown motion — static (kabhi nahi hona chahiye, par crash mat karo)
        log.warn(f"Motion '{motion}' pata nahi — static rakh rahe hain")
        mv = f"crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2"

    # Colour grade: enhanced contrast + saturation boost for mobile AMOLED punch
    grade = "eq=contrast=1.08:saturation=1.15:gamma=0.97"
    # Vignette — dhyan center pe jaata hai (suspense content ke liye zaroori)
    vig = "vignette=PI/5"

    return f"{base},{mv},{grade},{vig},fps={fps},format=yuv420p"


def _even(n: float) -> int:
    """H.264 ko even dimensions chahiye — warna 'Invalid argument' error."""
    return int(n) // 2 * 2


# =====================================================================
# SOUND DESIGN — sab kuch ffmpeg se GENERATE hota hai
# Hard constraint #6: koi copyrighted music nahi. Ye 100% synthesized hai.
# =====================================================================
def build_audio_filter(n_scenes: int, cuts: list[float], total: float,
                       reveal_sec: float | None = None,
                       notif_sec: float | None = None,
                       effects_cfg: dict | None = None,
                       cinematic: bool = False) -> tuple[list[str], str]:
    """
    Return: (extra ffmpeg inputs, filter_complex ka audio hissa)

    Layers:
      1. Narration (input 0) — compressed & filtered for mobile clarity.
      2. Ambient drone / heartbeat / riser / sub-hit / braam / room-tone (via pipeline.sound if cinematic).
      3. Dynamic ducking + master limiter before -14 LUFS loudnorm.
    """
    if cinematic:
        from pipeline.sound import build_sound_design_package
        pkg = build_sound_design_package(total, cuts, reveal_sec=reveal_sec, notif_sec=notif_sec, cfg_override=effects_cfg)
        inputs = pkg["inputs"]
        parts = []

        # Narration audio conditioning
        parts.append("[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
                     "acompressor=threshold=0.15:ratio=3:attack=20:release=250,"
                     "highpass=f=85,volume=1.0[narr]")

        # Sound design background layers
        parts.extend(pkg["parts"])
        bg_label = pkg["bg_label"]

        # Ducking: duck background audio against narration
        caps = capabilities()
        if pkg.get("ducking") and caps.get("sidechaincompress", False):
            parts.append("[narr]asplit=2[narr_sc][narr_mix]")
            parts.append(f"{bg_label}[narr_sc]sidechaincompress=threshold=0.1:ratio=5:attack=20:release=250[bg_ducked]")
            ducked_label = "[bg_ducked]"
            narr_label = "[narr_mix]"
        else:
            ducked_label = bg_label
            narr_label = "[narr]"

        # Mix ducked background + narration
        parts.append(f"{ducked_label}{narr_label}amix=inputs=2:duration=first:normalize=0[premix]")

        # Master limiter + loudnorm (-14 LUFS)
        limiter_str = "alimiter=limit=0.9:attack=5:release=50," if pkg.get("limiter") and caps.get("alimiter", False) else ""
        parts.append(f"[premix]{limiter_str}loudnorm=I=-14:TP=-1.5:LRA=11,"
                     f"aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[aout]")
        return inputs, ";".join(parts)

    inputs = []
    parts = []

    # ---- Layer 2: drone (do sine waves, halka detune = "unease" feel) ----
    inputs += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "sine=frequency=55:sample_rate=44100"]
    inputs += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "sine=frequency=110.7:sample_rate=44100"]

    # ---- Layer 3: whoosh per cut ----
    n_whoosh = 0
    for c in cuts:
        if 0.3 < c < total - 0.3:
            inputs += ["-f", "lavfi", "-t", "0.7", "-i",
                       "anoisesrc=color=brown:sample_rate=44100:amplitude=0.5"]
            n_whoosh += 1

    # narration ko thoda compress karo (consistent loudness, mobile speaker pe clear)
    parts.append("[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
                 "acompressor=threshold=0.15:ratio=3:attack=20:release=250,"
                 "highpass=f=85,volume=1.0[narr]")

    # drone: bahut dheemi (-32dB) + slow fade in/out
    parts.append(f"[1:a][2:a]amix=inputs=2:duration=shortest[dr0];"
                 f"[dr0]volume=0.025,lowpass=f=200,"
                 f"afade=t=in:st=0:d=2,afade=t=out:st={max(0.1, total-2):.2f}:d=2,"
                 f"aformat=channel_layouts=stereo[drone]")

    # whoosh: har ek ko cut ke time pe rakho (adelay), band-pass + fade
    whoosh_labels = []
    idx = 3  # 0=narration, 1,2=drone sines
    wi = 0
    for c in cuts:
        if not (0.3 < c < total - 0.3):
            continue
        delay_ms = int(max(0, (c - 0.25)) * 1000)
        parts.append(
            f"[{idx}:a]highpass=f=300,lowpass=f=6000,"
            f"afade=t=in:st=0:d=0.12,afade=t=out:st=0.25:d=0.45,"
            f"volume=0.10,adelay={delay_ms}|{delay_ms},"
            f"aformat=channel_layouts=stereo[wh{wi}]")
        whoosh_labels.append(f"[wh{wi}]")
        idx += 1
        wi += 1

    if whoosh_labels:
        parts.append(f"{''.join(whoosh_labels)}amix=inputs={len(whoosh_labels)}:"
                     f"duration=longest:normalize=0[whooshes]")
        mix_in = "[narr][drone][whooshes]"
        n_mix = 3
    else:
        mix_in = "[narr][drone]"
        n_mix = 2

    # Final mix + loudness normalize (-14 LUFS, Section 5 ka spec)
    parts.append(f"{mix_in}amix=inputs={n_mix}:duration=first:normalize=0[premix];"
                 f"[premix]loudnorm=I=-14:TP=-1.5:LRA=11,"
                 f"aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[aout]")

    log.debug(f"Sound design: 1 narration + drone + {n_whoosh} whoosh")
    return inputs, ";".join(parts)


# =====================================================================
# MAIN RENDER
# =====================================================================
class Renderer:
    def __init__(self, manifest: dict | str | Path):
        if isinstance(manifest, (str, Path)):
            manifest = json.loads(Path(manifest).read_text(encoding="utf-8"))
        self.m = manifest
        spec = self.m.get("render_spec", {})
        res = spec.get("resolution", CONFIG["resolution"])
        self.w, self.h = (int(x) for x in str(res).lower().split("x"))
        self.fps = int(spec.get("fps", 30))
        self.crf = int(spec.get("crf", 21))
        self.caps = capabilities()

    # ------------------------------------------------------------------
    def render(self, out_dir: str | Path, *, preset: str = "veryfast",
               keep_temp: bool = False) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="autopilot_render_"))

        try:
            scenes = self._prepare_scenes()
            audio_path = Path(self.m["narration"]["audio_path"])
            if not audio_path.exists():
                raise FileNotFoundError(
                    f"Narration audio nahi mila: {audio_path}. "
                    f"Pehle Phase 2 chalao: python run_phase2.py")

            total = sum(s["dur"] for s in scenes) - XFADE * (len(scenes) - 1)
            log.info(f"Render shuru: {len(scenes)} scenes, ~{total:.1f}s, "
                     f"{self.w}x{self.h}@{self.fps}")

            # ---- STEP 1: har scene ka clip ----
            clips = []
            for i, sc in enumerate(scenes):
                cp = tmp / f"clip_{i:02d}.mp4"
                self._render_clip(sc, cp, preset, is_first=(i == 0))
                clips.append(cp)
                log.debug(f"clip {i+1}/{len(scenes)} ready", motion=sc["motion"],
                          dur=f"{sc['dur']:.2f}s")

            # ---- STEP 2: crossfade se jodo ----
            silent = tmp / "video_silent.mp4"
            self._concat_xfade(clips, scenes, silent, preset)

            # ---- STEP 3: subtitles ----
            sub_style = (self.m.get("subtitles") or {}).get("style") or CONFIG.get("subtitle_style", "kinetic")
            ass = build_ass(self.m.get("words", []),
                            self.m["script"].get("hook_text_overlay", ""),
                            tmp / "subs.ass", width=self.w, height=self.h,
                            style=sub_style)
            build_srt(self.m.get("words", []), out_dir / "subtitles.srt")

            # ---- STEP 4+5: audio mix + subtitles burn + final encode ----
            final = out_dir / "final.mp4"
            self._finalize(silent, audio_path, ass, scenes, final, preset)

            # ---- STEP 6: cover frame ----
            cover = out_dir / "cover.jpg"
            self._cover(final, cover)

            info = self._summary(final, cover, out_dir, scenes)
            log.ok(f"✅ Video ready: {final.name}", size_mb=info["size_mb"],
                   duration=info["duration_sec"])
            return info
        finally:
            if keep_temp:
                log.info(f"Temp files rakhe: {tmp}")
            else:
                shutil.rmtree(tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    def _prepare_scenes(self) -> list[dict]:
        """Manifest ke scenes ko validate karo aur durations theek karo."""
        scenes = []
        for sc in self.m["scenes"]:
            p = sc.get("path")
            if not p or not Path(p).exists():
                log.warn(f"Scene {sc['n']} ki image nahi mili — scene skip",
                         path=p)
                continue
            dur = float(sc.get("dur") or 0)
            if dur < 0.8:
                dur = 0.8   # itna chhota scene dikhta hi nahi
            scenes.append({**sc, "dur": dur + XFADE})  # xfade overlap ke liye extra
        if not scenes:
            raise RuntimeError(
                "Ek bhi scene image nahi mili. Phase 2 dobara chalao: "
                "python run_phase2.py")
        if len(scenes) < len(self.m["scenes"]):
            log.warn(f"{len(self.m['scenes']) - len(scenes)} scenes skip hue "
                     f"(images missing) — video chhota hoga")
        return scenes

    # ------------------------------------------------------------------
    def _render_clip(self, sc: dict, out: Path, preset: str, is_first: bool = False):
        vis_cfg = (self.m.get("effects") or {}).get("visual") or (CONFIG.get("effects") or {}).get("visual") or {}
        if vis_cfg:
            from pipeline.effects import build_cinematic_scene_filter
            vf, _ = build_cinematic_scene_filter(
                sc["motion"], sc["dur"], self.w, self.h, self.fps,
                emotion=sc.get("emotion", "neutral"),
                role=sc.get("role", "body"),
                parallax=sc.get("parallax", False),
                is_first=is_first,
                effects_cfg=vis_cfg,
            )
        else:
            vf = ken_burns(sc["motion"], sc["dur"], self.w, self.h, self.fps,
                           parallax=sc.get("parallax", False))
        run(["-loop", "1", "-t", f"{sc['dur']:.3f}", "-r", str(self.fps),
             "-i", sc["path"], "-vf", vf,
             "-c:v", "libx264", "-preset", preset, "-crf", str(self.crf),
             "-pix_fmt", "yuv420p", "-an", str(out)],
            what=f"scene {sc['n']} render", timeout=300)

    # ------------------------------------------------------------------
    def _concat_xfade(self, clips: list[Path], scenes: list[dict],
                      out: Path, preset: str):
        """
        Sab clips ko crossfade se jodo.
        xfade filter chain: clip0 x clip1 -> v01, v01 x clip2 -> v02, ...
        """
        if len(clips) == 1:
            shutil.copy(clips[0], out)
            return
        if not self.caps.get("xfade", True):
            log.warn("xfade filter nahi hai — hard cuts use kar rahe hain "
                     "(video thoda jhatkedaar lagega)")
            return self._concat_hard(clips, out)

        inputs = []
        for c in clips:
            inputs += ["-i", str(c)]

        chain, prev, offset = [], "[0:v]", 0.0
        for i in range(1, len(clips)):
            offset += scenes[i - 1]["dur"] - XFADE
            label = f"[v{i}]" if i < len(clips) - 1 else "[vout]"
            # Transition rotate karo — har cut ek jaisa nahi lagna chahiye.
            # ⚠️ 'fadeblack' JAAN-BOOJH KAR HATAYA hai: wo beech mein poore kaale
            # frames banata hai (maine blackdetect se pakda — 2.4s aur 18.4s pe).
            # Shorts mein kaala frame = darshak ko lagta hai video khatam ho gaya
            # = scroll. Retention seedha girta hai.
            trans = ["fade", "smoothleft", "fade", "smoothup", "fade", "smoothright"][i % 6]
            chain.append(f"{prev}[{i}:v]xfade=transition={trans}:"
                         f"duration={XFADE}:offset={offset:.3f},format=yuv420p{label}")
            prev = label

        run([*inputs, "-filter_complex", ";".join(chain), "-map", "[vout]",
             "-c:v", "libx264", "-preset", preset, "-crf", str(self.crf),
             "-pix_fmt", "yuv420p", "-r", str(self.fps), "-an", str(out)],
            what="crossfade concat", timeout=600)

    def _concat_hard(self, clips: list[Path], out: Path):
        """Fallback: bina transition ke jodo (concat demuxer — bahut tez)."""
        lst = out.parent / "concat.txt"
        lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")
        run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
            what="hard concat")

    # ------------------------------------------------------------------
    def _finalize(self, video: Path, audio: Path, ass: Path,
                  scenes: list[dict], out: Path, preset: str):
        """Audio mix + subtitles burn + final encode — sab ek hi pass mein."""
        total = sum(s["dur"] for s in scenes) - XFADE * (len(scenes) - 1)
        # cut points nikalo (whoosh SFX yahan lagenge)
        cuts, t = [], 0.0
        for s in scenes[:-1]:
            t += s["dur"] - XFADE
            cuts.append(t)
        # reveal point find karo
        reveal_sec = None
        for ln in self.m.get("narration", {}).get("lines", []):
            if ln.get("role") == "reveal":
                reveal_sec = float(ln.get("start", total * 0.75))
                break
        sound_cfg = (self.m.get("effects") or {}).get("sound") or (CONFIG.get("effects") or {}).get("sound") or {}
        cinematic_sound = bool(sound_cfg)

        # notification alert time find karo (social/chat scenes)
        notif_sec = None
        for ln in self.m.get("narration", {}).get("lines", []):
            txt = ln.get("text", "").lower()
            if any(k in txt for k in ("notification", "follow", "message", "dm", "accepted")):
                notif_sec = float(ln.get("start", 0))
                break

        extra_inputs, afilter = build_audio_filter(len(scenes), cuts, total,
                                                   reveal_sec=reveal_sec,
                                                   notif_sec=notif_sec,
                                                   effects_cfg=sound_cfg,
                                                   cinematic=cinematic_sound)

        # subtitles path ko ffmpeg filter ke liye escape karna padta hai
        ass_esc = str(ass).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        fonts_esc = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")
        vfilter = f"[0:v]ass='{ass_esc}':fontsdir='{fonts_esc}',format=yuv420p[vout]"

        if not self.caps.get("ass", True):
            log.error("libass nahi hai — subtitles NAHI lagenge! "
                      "60% log sound off pe dekhte hain, ye video unke liye bekaar hai. "
                      "Poora ffmpeg build install karo.")
            vfilter = "[0:v]format=yuv420p[vout]"

        run(["-i", str(video), "-i", str(audio), *extra_inputs,
             "-filter_complex", f"{vfilter};{_shift_audio_idx(afilter)}",
             "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-preset", preset, "-crf", str(self.crf),
             "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
             "-r", str(self.fps),
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
             "-movflags", "+faststart",   # IG/YT ke liye — metadata shuru mein
             "-shortest", str(out)],
            what="final encode (audio mix + subtitles)", timeout=900)

    # ------------------------------------------------------------------
    def _cover(self, video: Path, out: Path):
        """
        Cover frame = 1 second wala frame.
        Frame 0 kyun nahi? Kyunki wahan fade-in chal raha hota hai (kaala frame).
        1s pe hook overlay bhi dikh raha hota hai — thumbnail ke liye perfect.
        """
        try:
            run(["-ss", "1.0", "-i", str(video), "-frames:v", "1",
                 "-q:v", "2", str(out)], what="cover frame", timeout=120)
        except Exception as e:  # noqa: BLE001
            log.warn("Cover frame nahi bana (video chal jayega)", reason=str(e)[:120])

    # ------------------------------------------------------------------
    def _summary(self, final: Path, cover: Path, out_dir: Path,
                 scenes: list[dict]) -> dict:
        from core.ffmpeg import probe
        info = probe(final)
        dur = 0.0
        vcodec = acodec = "?"
        w = h = 0
        if info:
            dur = float(info.get("format", {}).get("duration", 0) or 0)
            for st in info.get("streams", []):
                if st.get("codec_type") == "video":
                    vcodec = st.get("codec_name", "?")
                    w, h = st.get("width", 0), st.get("height", 0)
                elif st.get("codec_type") == "audio":
                    acodec = st.get("codec_name", "?")
        if not dur:
            dur = float(self.m["narration"]["duration_sec"])
            w, h = self.w, self.h
        return {
            "video_path": str(final),
            "cover_path": str(cover) if cover.exists() else None,
            "srt_path": str(out_dir / "subtitles.srt"),
            "duration_sec": round(dur, 2),
            "size_mb": round(final.stat().st_size / 1024 / 1024, 2),
            "resolution": f"{w}x{h}",
            "vcodec": vcodec, "acodec": acodec,
            "n_scenes": len(scenes),
        }


def _shift_audio_idx(afilter: str) -> str:
    """
    build_audio_filter() maanta hai ki narration input #0 hai.
    Par _finalize mein input #0 = video, #1 = narration hai.
    Isliye saare audio input indices ek se aage khiska do.
    """
    import re
    def bump(match):
        return f"[{int(match.group(1)) + 1}:a]"
    return re.sub(r"\[(\d+):a\]", bump, afilter)


if __name__ == "__main__":
    import sys
    mf = sys.argv[1] if len(sys.argv) > 1 else "output/video_0001/manifest.json"
    r = Renderer(mf)
    print(json.dumps(r.render(Path(mf).parent), indent=2, ensure_ascii=False))
