# 2.5D Layered Scenes & Parallax Architecture (Phase E)

## 1. Overview & Objective
Standard single-image Ken Burns motion creates a "flat slideshow" aesthetic because background and foreground move at identical relative velocity. In real cinema, parallax depth occurs when camera movement displaces near objects faster than distant horizons.

**Phase E** introduces a lightweight, pure stdlib/ffmpeg 2.5D layered compositor that separates background setting and foreground subject, applying differential motion vectors to create three-dimensional depth without requiring heavy external ML packages or proprietary APIs.

---

## 2. Layer Separation Strategies (Zero New Pip Dependencies)

### Approach A: Dual-Plate Prompt Generation (Image Model Native)
The ArtDirector prompts two complementary image plates per layered scene:
1. **Background Plate (`bg_*.jpg`)**: Wide environmental scene with no foreground subjects (e.g., `"deep dark corridor with flickering bulb, empty background, no people, vertical 9:16"`).
2. **Foreground Plate (`fg_*.png`)**: The character subject framed cleanly against a pure solid keying background (e.g., `"same character standing in foreground, green screen background, chroma key solid color #00FF00, vertical 9:16"`).

*Keying in FFmpeg*:
```bash
[1:v]colorkey=0x00FF00:0.3:0.1,format=yuva420p[fg_keyed]
```

### Approach B: Pure Python/Pillow Luminance & Gradient Depth Map
For single images where dual-plate is unavailable, standard library `Pillow` generates an automated luminance depth mask:
1. Load image in grayscale (`L` mode).
2. Apply edge detection (`ImageFilter.FIND_EDGES`) and vertical/radial gradient weighting (foreground characters typically inhabit lower-middle 60% of vertical 9:16 frame).
3. Generate a binary/alpha mask (`mask.png`) separating foreground character from background plate.
4. Background in-painting simulation in FFmpeg: Background plate is scaled slightly up (1.08x) and blurred (`boxblur=10:1`) to mask cutout silhouette halos.

---

## 3. FFmpeg Parallax Filter Graph & Differential Motion

The parallax compositor applies differential speed coefficients:
- **Background Layer**: 0.3x displacement rate (e.g., zoom from 1.00 to 1.04).
- **Foreground Layer**: 1.0x displacement rate (e.g., zoom from 1.00 to 1.14 + slight pan drift).

### Parallax Intensity Presets (A/B Testable)
| Preset | BG Scale Delta | FG Scale Delta | Differential | Cinematic Feel |
|---|---|---|---|---|
| **Low** | 1.00 -> 1.03 | 1.00 -> 1.08 | 0.05 | Subtle documentary realism |
| **Medium** (Default) | 1.00 -> 1.05 | 1.00 -> 1.15 | 0.10 | Suspense cinematic tension |
| **High** | 1.00 -> 1.08 | 1.00 -> 1.28 | 0.20 | Dramatic vertigo / reveal effect |

### Complex Filter Graph Expression
```text
[0:v]scale=w='2*floor(1080*(1+0.05*t/D)/2)':h='2*floor(1920*(1+0.05*t/D)/2)':eval=frame,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2[bg];
[1:v]scale=w='2*floor(1080*(1+0.15*t/D)/2)':h='2*floor(1920*(1+0.15*t/D)/2)':eval=frame,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2[fg];
[bg][fg]overlay=x=0:y=0:shortest=1,format=yuv420p[out]
```

---

## 4. Procedural Atmospheric Dust & Fog Layers (lavfi Native)

To enhance the feeling of suspense, environmental depth particles are generated on the fly via ffmpeg `lavfi` source filters without downloading or caching external video asset files.

### 1. Floating Micro-Dust Particles
Procedural white speck generation with randomized frame evaluation, slight gaussian diffusion, and low opacity alpha blending:
```text
nullsrc=s=1080x1920:d={dur}:r=30,
geq=r='if(gt(random(1),0.998),255,0)':g='if(gt(random(1),0.998),255,0)':b='if(gt(random(1),0.998),255,0)',
boxblur=2:1,format=yuva420p,colorchannelmixer=aa=0.3[dust]
```

### 2. Atmospheric Drifting Fog
Soft moving noise bed with horizontal translation and low-pass luminance:
```text
nullsrc=s=1080x1920:d={dur}:r=30,
noise=alls=25:allf=t+u,
boxblur=15:5,format=yuva420p,colorchannelmixer=aa=0.15[fog]
```

---

## 5. Performance Budget & Graceful Fallback

- **Time Budget**: Full single-pass video rendering takes ~45-55 seconds.
- Multi-layer 2.5D compositing adds ~15-25 seconds per video, well within the **150s hard ceiling**.
- **Configuration Toggle**:
  `config.yaml -> effects.visual.layered_scenes: false` (default `false` to maintain maximum speed on budget hardware, activated when set to `true`).
- **Graceful Fallback**: If `colorkey`, `overlay`, or secondary plate fails, the compositor automatically logs a warning and falls back to standard single-image Ken Burns with zero pipeline stoppage.
