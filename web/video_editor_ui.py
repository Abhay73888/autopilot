"""
web/video_editor_ui.py — God-Level AI Mini Video Editor frontend module.

Includes:
  1. EDITOR_CSS: Ultra-premium dark glassmorphic styling, responsive 9:16 canvas player,
     interactive multi-track scrubber, color grading palette, hook overlays.
  2. EDITOR_TAB_HTML: Section markup for #sec-editor.
  3. EDITOR_JS: Real-time client-side timeline synchronization, instant live CSS filter preview,
     AI God Mode auto-enhance, and asynchronous FFmpeg export.
"""

EDITOR_CSS = r"""
/* ==========================================================================
   GOD-LEVEL AI MINI VIDEO EDITOR STYLING
   ========================================================================== */
.editor-container {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 28px;
  margin-top: 12px;
  align-items: start;
}
@media (max-width: 1150px) {
  .editor-container {
    grid-template-columns: 1fr;
  }
}

/* Left Column: Video Preview & Canvas */
.editor-preview-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 20px;
  backdrop-filter: blur(16px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.editor-viewport-wrap {
  width: 100%;
  max-width: 320px;
  aspect-ratio: 9 / 16;
  background: #05070d;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 242, 254, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.08);
  margin-bottom: 16px;
}

#editorVideo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: filter 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* On-Screen Viral Hook Overlay */
.editor-hook-overlay {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 86%;
  text-align: center;
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 15px;
  line-height: 1.25;
  color: #ffeb3b;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9), 0 0 2px #000;
  background: rgba(0, 0, 0, 0.72);
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 235, 59, 0.4);
  pointer-events: none;
  display: none;
  z-index: 10;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.6);
  letter-spacing: 0.5px;
}
.editor-hook-overlay.pos-top { top: 12%; }
.editor-hook-overlay.pos-center { top: 50%; transform: translate(-50%, -50%); }
.editor-hook-overlay.pos-bottom { bottom: 14%; }

/* Player Transport Controls */
.editor-transport {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.editor-transport-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 15px;
  transition: all 0.2s ease;
}
.editor-transport-btn:hover {
  background: var(--accent);
  color: #000;
  transform: scale(1.05);
}
.editor-timecode {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

/* Right Column: Workstation Tracks & Panels */
.editor-workstation {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.editor-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 22px;
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

.editor-panel-title {
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  color: #fff;
}

/* Timeline & Trimmer Scrubber */
.timeline-track-container {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 16px;
  position: relative;
}

.timeline-ruler {
  display: flex;
  justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.timeline-scrubber {
  position: relative;
  width: 100%;
  height: 44px;
  background: linear-gradient(90deg, #111827 0%, #1f2937 100%);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.timeline-scenes-filmstrip {
  position: absolute;
  inset: 0;
  display: flex;
  opacity: 0.35;
  pointer-events: none;
}
.timeline-scene-thumb {
  flex: 1;
  height: 100%;
  object-fit: cover;
  border-right: 1px dashed rgba(255, 255, 255, 0.3);
}

.timeline-active-range {
  position: absolute;
  top: 0;
  bottom: 0;
  background: rgba(0, 242, 254, 0.25);
  border-left: 3px solid #00f2fe;
  border-right: 3px solid #00f2fe;
  box-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
  pointer-events: none;
}

.timeline-playhead {
  position: absolute;
  top: -2px;
  bottom: -2px;
  width: 2px;
  background: #ff007a;
  box-shadow: 0 0 8px #ff007a;
  pointer-events: none;
  z-index: 5;
}
.timeline-playhead::after {
  content: '';
  position: absolute;
  top: 0;
  left: -4px;
  width: 10px;
  height: 10px;
  background: #ff007a;
  border-radius: 50%;
}

.timeline-controls-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.trim-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.04);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.trim-input-group label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}
.trim-input-group input {
  background: transparent;
  border: none;
  color: #00f2fe;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  width: 58px;
  text-align: right;
  outline: none;
}

/* Color Filter Presets Grid */
.filter-presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
}

.filter-chip {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}
.filter-chip:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}
.filter-chip.active {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.15), rgba(168, 85, 247, 0.15));
  border-color: #00f2fe;
  box-shadow: 0 4px 14px rgba(0, 242, 254, 0.25);
}
.filter-chip-name {
  font-weight: 700;
  font-size: 13px;
  color: #fff;
}
.filter-chip-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.2;
}

/* Viral Hook Headline Panel */
.hook-tool-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  margin-bottom: 12px;
}
.hook-text-input {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 10px 14px;
  color: #fff;
  font-size: 13px;
  outline: none;
}
.hook-text-input:focus {
  border-color: #ffeb3b;
  box-shadow: 0 0 10px rgba(255, 235, 59, 0.2);
}

.pos-btn-group {
  display: flex;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}
.pos-btn {
  background: rgba(255, 255, 255, 0.05);
  border: none;
  color: var(--text-muted);
  padding: 0 12px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.pos-btn.active {
  background: #ffeb3b;
  color: #000;
  font-weight: 700;
}

/* Audio & Speed Mixer Row */
.audio-mixer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.mixer-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mixer-item label {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
}

/* Export & AI Action Bar */
.editor-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-wrap: wrap;
}

.btn-ai-enhance {
  background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  padding: 12px 22px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(168, 85, 247, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}
.btn-ai-enhance:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 26px rgba(168, 85, 247, 0.6);
}

.btn-export-cut {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #000;
  font-weight: 800;
  font-size: 14px;
  padding: 12px 26px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}
.btn-export-cut:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 26px rgba(0, 242, 254, 0.6);
}
.btn-export-cut:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Export Result Card */
.export-result-card {
  background: linear-gradient(135deg, rgba(0, 242, 254, 0.08), rgba(168, 85, 247, 0.08));
  border: 1px solid rgba(0, 242, 254, 0.3);
  border-radius: 16px;
  padding: 16px 20px;
  margin-top: 18px;
  display: none;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.export-result-card.active {
  display: flex;
}
"""


EDITOR_TAB_HTML = r"""
<section class="tab-section" id="sec-editor">
  <div class="header">
    <div>
      <h2 style="font-family:'Outfit',sans-serif; font-size: 26px; font-weight:800; margin:0; display:flex; align-items:center; gap:10px;">
        <span>✂️ God-Level AI Mini Video Editor</span>
        <span style="font-size:12px; background:linear-gradient(135deg,#00f2fe,#a855f7); color:#000; font-weight:800; padding:2px 8px; border-radius:20px;">PRO STUDIO</span>
      </h2>
      <div class="sub" style="color:var(--text-muted); font-size:13px; margin-top:4px;">
        Pick any generated video, trim In/Out points, apply cinematic LUT color grading, add viral hook stickers, and export in seconds.
      </div>
    </div>
    <div style="display:flex; gap:12px; align-items:center;">
      <select id="editorVideoSelect" onchange="onEditorSelectVideo(this.value)" style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:8px 14px; border-radius:10px; font-size:13px; max-width:320px; outline:none; cursor:pointer;">
        <option value="">⏳ Loading videos...</option>
      </select>
      <button class="btn btn-sm" onclick="loadEditorVideos()" title="Refresh video list" style="padding:8px 12px;">🔄</button>
    </div>
  </div>

  <div class="editor-container">
    <!-- LEFT: Interactive 9:16 Canvas Player -->
    <div class="editor-preview-card">
      <div class="editor-viewport-wrap" id="editorViewport">
        <video id="editorVideo" playsinline preload="metadata" crossorigin="anonymous">
          <source id="editorVideoSource" src="" type="video/mp4">
        </video>
        <!-- Real-time Viral Hook Overlay -->
        <div id="editorHookOverlay" class="editor-hook-overlay pos-top">
          WAIT TILL THE END 😱
        </div>
      </div>

      <!-- Player Transport Controls -->
      <div class="editor-transport">
        <button class="editor-transport-btn" id="btnStepBack" onclick="editorStep(-1.0)" title="Step back 1s">⏪</button>
        <button class="editor-transport-btn" id="btnPlayPause" onclick="editorTogglePlay()" title="Play/Pause (Space)" style="width:44px; height:44px; background:var(--accent); color:#000; font-size:18px;">▶</button>
        <button class="editor-transport-btn" id="btnStepForward" onclick="editorStep(1.0)" title="Step forward 1s">⏩</button>
        <button class="editor-transport-btn" id="btnLoop" onclick="editorToggleLoop()" title="Loop Playback">🔁</button>
        <div class="editor-timecode" id="editorTimecode">00:00.0 / 00:00.0</div>
      </div>

      <div style="width:100%; display:flex; justify-content:space-between; margin-top:12px; font-size:12px; color:var(--text-muted);">
        <span>Aspect: <strong>9:16 Shorts</strong></span>
        <span id="editorActiveFilterLabel">Filter: <strong>Original</strong></span>
      </div>
    </div>

    <!-- RIGHT: Timeline & Multi-Track Workstation -->
    <div class="editor-workstation">
      <!-- Panel 1: Interactive Multi-Track Scrubber -->
      <div class="editor-panel">
        <div class="editor-panel-title">
          <span>🎬 Interactive Timeline & Trim Handles</span>
          <span style="font-size:12px; color:var(--accent);" id="editorTrimDurationLabel">Trimmed: 0.0s</span>
        </div>

        <div class="timeline-track-container">
          <div class="timeline-ruler">
            <span id="rulerStart">00:00</span>
            <span id="rulerMid">00:15</span>
            <span id="rulerEnd">00:30</span>
          </div>

          <div class="timeline-scrubber" id="timelineScrubber" onclick="onTimelineClick(event)">
            <div class="timeline-scenes-filmstrip" id="timelineScenesStrip"></div>
            <div class="timeline-active-range" id="timelineActiveRange"></div>
            <div class="timeline-playhead" id="timelinePlayhead"></div>
          </div>

          <div class="timeline-controls-row">
            <div class="trim-input-group">
              <label>IN POINT</label>
              <input type="number" id="inputTrimIn" step="0.1" min="0" value="0.0" onchange="onTrimInputChange()">
              <span style="font-size:11px; color:var(--text-muted);">sec</span>
              <button class="btn btn-sm" onclick="setTrimCurrent('in')" style="padding:2px 6px; font-size:10px;">SET HERE</button>
            </div>

            <div class="trim-input-group">
              <label>OUT POINT</label>
              <input type="number" id="inputTrimOut" step="0.1" min="0" value="30.0" onchange="onTrimInputChange()">
              <span style="font-size:11px; color:var(--text-muted);">sec</span>
              <button class="btn btn-sm" onclick="setTrimCurrent('out')" style="padding:2px 6px; font-size:10px;">SET HERE</button>
            </div>

            <div class="trim-input-group" style="margin-left:auto;">
              <label>SPEED</label>
              <select id="selectSpeed" onchange="onSpeedChange(this.value)" style="background:transparent; border:none; color:#00f2fe; font-family:'JetBrains Mono',monospace; outline:none; cursor:pointer;">
                <option value="0.75">0.75x (Cinematic Slow)</option>
                <option value="1.0" selected>1.0x (Normal)</option>
                <option value="1.1">1.1x (Fast Shorts)</option>
                <option value="1.25">1.25x (Viral Pacing)</option>
                <option value="1.5">1.5x (Super Speed)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel 2: Cinematic LUT Color Grading -->
      <div class="editor-panel">
        <div class="editor-panel-title">
          <span>🎨 Cinematic LUT Color Grading</span>
          <span style="font-size:11px; color:var(--text-muted);">Instant Live Preview</span>
        </div>
        <div class="filter-presets-grid" id="filterPresetsGrid">
          <div class="filter-chip active" onclick="applyEditorFilter('none', this)">
            <div class="filter-chip-name">✨ Original</div>
            <div class="filter-chip-desc">Untouched natural balance</div>
          </div>
          <div class="filter-chip" onclick="applyEditorFilter('cyberpunk', this)">
            <div class="filter-chip-name">⚡ Cyberpunk Neon</div>
            <div class="filter-chip-desc">Electric blue & magenta pop</div>
          </div>
          <div class="filter-chip" onclick="applyEditorFilter('noir', this)">
            <div class="filter-chip-name">🕵️ Cinematic Noir</div>
            <div class="filter-chip-desc">Moody teal & dark contrast</div>
          </div>
          <div class="filter-chip" onclick="applyEditorFilter('golden_hour', this)">
            <div class="filter-chip-name">🌅 Golden Hour</div>
            <div class="filter-chip-desc">Radiant amber sunlight glow</div>
          </div>
          <div class="filter-chip" onclick="applyEditorFilter('anime_vivid', this)">
            <div class="filter-chip-name">🌸 Anime Vivid</div>
            <div class="filter-chip-desc">Vibrant hyper-saturation</div>
          </div>
          <div class="filter-chip" onclick="applyEditorFilter('vintage', this)">
            <div class="filter-chip-name">📼 Vintage 90s</div>
            <div class="filter-chip-desc">Retro film grain vignette</div>
          </div>
          <div class="filter-chip" onclick="applyEditorFilter('horror', this)">
            <div class="filter-chip-name">🩸 Dark Horror</div>
            <div class="filter-chip-desc">Cold desaturated dread</div>
          </div>
        </div>
      </div>

      <!-- Panel 3: Viral Hook Headline & Audio Mixer -->
      <div class="editor-panel">
        <div class="editor-panel-title">
          <span>🔥 Viral Hook Sticker & Audio Control</span>
        </div>

        <div class="hook-tool-row">
          <input type="text" id="inputHookText" class="hook-text-input" placeholder="Enter viral headline sticker (e.g. WAIT FOR 0:17 😱)" oninput="onHookTextInput(this.value)">
          <div class="pos-btn-group">
            <button class="pos-btn active" id="posTop" onclick="setHookPos('top')">Top</button>
            <button class="pos-btn" id="posCenter" onclick="setHookPos('center')">Mid</button>
            <button class="pos-btn" id="posBottom" onclick="setHookPos('bottom')">Bottom</button>
          </div>
        </div>

        <div class="audio-mixer-grid" style="margin-top:16px;">
          <div class="mixer-item">
            <label><span>Voiceover Volume</span><span id="voiceVolLabel">100%</span></label>
            <input type="range" id="rangeVoiceVol" min="0" max="200" value="100" oninput="onVoiceVolChange(this.value)">
          </div>
          <div class="mixer-item">
            <label><span>Audio Fade In/Out</span></label>
            <div style="display:flex; align-items:center; gap:8px; height:34px;">
              <input type="checkbox" id="checkFadeAudio" checked style="accent-color:#00f2fe; width:18px; height:18px;">
              <span style="font-size:12px; color:#fff;">Smooth 0.5s audio fades</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons Bar -->
      <div class="editor-actions-bar">
        <button class="btn-ai-enhance" onclick="triggerAiGodMode()">
          <span>✨ 1-Click AI God Mode</span>
        </button>

        <button class="btn-export-cut" id="btnExportCut" onclick="exportEditedCut()">
          <span>⚡ Render & Export Cut</span>
        </button>
      </div>

      <!-- Export Result Card -->
      <div class="export-result-card" id="exportResultCard">
        <div>
          <div style="font-weight:700; font-size:15px; color:#fff; display:flex; align-items:center; gap:8px;">
            <span>🎉 Export Completed!</span>
            <span id="exportDurationBadge" style="font-size:11px; background:#00f2fe; color:#000; font-weight:800; padding:2px 6px; border-radius:12px;">0.0s</span>
          </div>
          <div id="exportStatusMsg" style="font-size:12px; color:var(--text-muted); margin-top:2px;">
            Your edited video is ready for download and publishing.
          </div>
        </div>
        <div style="display:flex; gap:10px;">
          <a id="btnDownloadExport" href="#" download class="btn btn-sm" style="background:#00f2fe; color:#000; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
            <span>⬇️ Download MP4</span>
          </a>
          <button class="btn btn-sm" onclick="showTab('sec-queue')" style="background:rgba(255,255,255,0.08); color:#fff;">
            <span>📋 View In Queue</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</section>
"""


EDITOR_JS = r"""
/* ==========================================================================
   GOD-LEVEL MINI VIDEO EDITOR CLIENT-SIDE CONTROLLER
   ========================================================================== */

let _edVideos = [];
let _edCurrentVideo = null;
let _edDuration = 30.0;
let _edTrimIn = 0.0;
let _edTrimOut = 30.0;
let _edSpeed = 1.0;
let _edActiveFilter = 'none';
let _edHookPos = 'top';
let _edFilterCssMap = {
  'none': 'none',
  'cyberpunk': 'contrast(1.35) saturate(1.5) hue-rotate(-15deg)',
  'noir': 'contrast(1.4) saturate(0.65) brightness(0.9)',
  'vintage': 'sepia(0.25) contrast(1.15) saturate(0.9) brightness(0.95)',
  'golden_hour': 'sepia(0.15) contrast(1.18) saturate(1.3) brightness(1.05)',
  'anime_vivid': 'contrast(1.25) saturate(1.7) brightness(1.02)',
  'horror': 'contrast(1.45) saturate(0.4) brightness(0.85)'
};

async function loadEditorVideos() {
  const sel = document.getElementById('editorVideoSelect');
  if (!sel) return;
  sel.innerHTML = '<option value="">⏳ Scanning editable videos...</option>';

  try {
    const res = await fetch('/api/editor/videos');
    const data = await res.json();
    if (!data.ok || !data.videos || data.videos.length === 0) {
      sel.innerHTML = '<option value="">No videos found</option>';
      return;
    }
    _edVideos = data.videos;
    sel.innerHTML = '';
    _edVideos.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `#${v.id} — ${v.title.slice(0, 45)} (${v.length_sec}s)`;
      sel.appendChild(opt);
    });

    // Auto-select first video
    if (_edVideos.length > 0) {
      onEditorSelectVideo(_edVideos[0].id);
    }
  } catch (err) {
    console.error('loadEditorVideos error', err);
    sel.innerHTML = '<option value="">Failed to load videos</option>';
  }
}

async function onEditorSelectVideo(vid) {
  if (!vid) return;
  const vidInt = parseInt(vid, 10);
  const vMeta = _edVideos.find(v => v.id === vidInt);
  const vEl = document.getElementById('editorVideo');
  if (!vEl) return;

  try {
    const res = await fetch(`/api/editor/video/${vidInt}`);
    const data = await res.json();
    if (!data.ok) {
      toast('Failed to load video timeline', 'warn');
      return;
    }
    _edCurrentVideo = data;
    _edDuration = data.duration || 30.0;
    _edTrimIn = 0.0;
    _edTrimOut = _edDuration;

    // Set video src
    vEl.src = data.video_url;
    vEl.load();

    // Reset inputs
    const inEl = document.getElementById('inputTrimIn');
    const outEl = document.getElementById('inputTrimOut');
    if (inEl) { inEl.value = '0.0'; inEl.max = _edDuration; }
    if (outEl) { outEl.value = _edDuration.toFixed(1); outEl.max = _edDuration; }

    // Update ruler
    const rStart = document.getElementById('rulerStart');
    const rMid = document.getElementById('rulerMid');
    const rEnd = document.getElementById('rulerEnd');
    if (rStart) rStart.textContent = '00:00';
    if (rMid) rMid.textContent = formatTimecode(_edDuration / 2);
    if (rEnd) rEnd.textContent = formatTimecode(_edDuration);

    // Filmstrip scenes
    const strip = document.getElementById('timelineScenesStrip');
    if (strip) {
      strip.innerHTML = '';
      if (data.scenes && data.scenes.length > 0) {
        data.scenes.forEach(s => {
          const img = document.createElement('img');
          img.src = s.img_url;
          img.className = 'timeline-scene-thumb';
          strip.appendChild(img);
        });
      }
    }

    // Hook overlay suggestion from script if available
    const hookInp = document.getElementById('inputHookText');
    if (hookInp) {
      if (vMeta && vMeta.hook_overlay) {
        hookInp.value = vMeta.hook_overlay;
      } else {
        hookInp.value = '';
      }
      onHookTextInput(hookInp.value);
    }

    updateTimelineVisuals();
    toast(`Loaded Video #${vidInt} (${_edDuration}s)`, 'ok');
  } catch (err) {
    console.error('onEditorSelectVideo error', err);
  }
}

function formatTimecode(sec) {
  if (isNaN(sec)) sec = 0;
  const m = Math.floor(sec / 60);
  const s = (sec % 60).toFixed(1);
  return `${m.toString().padStart(2, '0')}:${s.padStart(4, '0')}`;
}

function editorTogglePlay() {
  const vEl = document.getElementById('editorVideo');
  const btn = document.getElementById('btnPlayPause');
  if (!vEl) return;
  if (vEl.paused) {
    // If playhead past trim out, loop to trim in
    if (vEl.currentTime >= _edTrimOut || vEl.currentTime < _edTrimIn) {
      vEl.currentTime = _edTrimIn;
    }
    vEl.play();
    if (btn) btn.textContent = '⏸';
  } else {
    vEl.pause();
    if (btn) btn.textContent = '▶';
  }
}

function editorStep(delta) {
  const vEl = document.getElementById('editorVideo');
  if (!vEl) return;
  vEl.currentTime = Math.max(0, Math.min(_edDuration, vEl.currentTime + delta));
}

function editorToggleLoop() {
  const btn = document.getElementById('btnLoop');
  const vEl = document.getElementById('editorVideo');
  if (!vEl) return;
  vEl.loop = !vEl.loop;
  if (btn) {
    btn.style.background = vEl.loop ? 'var(--accent)' : 'rgba(255,255,255,0.08)';
    btn.style.color = vEl.loop ? '#000' : '#fff';
  }
}

// Scrubber events
document.addEventListener('DOMContentLoaded', () => {
  const vEl = document.getElementById('editorVideo');
  if (!vEl) return;

  vEl.addEventListener('timeupdate', () => {
    const cur = vEl.currentTime;
    const tcEl = document.getElementById('editorTimecode');
    if (tcEl) tcEl.textContent = `${formatTimecode(cur)} / ${formatTimecode(_edDuration)}`;

    // Playhead line
    const ph = document.getElementById('timelinePlayhead');
    if (ph && _edDuration > 0) {
      const pct = (cur / _edDuration) * 100;
      ph.style.left = `${pct}%`;
    }

    // Boundary check for loop inside trimmed in/out
    if (cur >= _edTrimOut) {
      if (vEl.loop) {
        vEl.currentTime = _edTrimIn;
      } else {
        vEl.pause();
        const btn = document.getElementById('btnPlayPause');
        if (btn) btn.textContent = '▶';
      }
    }
  });

  vEl.addEventListener('ended', () => {
    const btn = document.getElementById('btnPlayPause');
    if (btn) btn.textContent = '▶';
  });
});

function onTimelineClick(e) {
  const scrubber = document.getElementById('timelineScrubber');
  const vEl = document.getElementById('editorVideo');
  if (!scrubber || !vEl || !_edDuration) return;

  const rect = scrubber.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const pct = Math.max(0, Math.min(1, clickX / rect.width));
  const targetTime = pct * _edDuration;
  vEl.currentTime = targetTime;
}

function setTrimCurrent(type) {
  const vEl = document.getElementById('editorVideo');
  if (!vEl) return;
  const cur = parseFloat(vEl.currentTime.toFixed(1));
  if (type === 'in') {
    _edTrimIn = cur;
    if (_edTrimIn >= _edTrimOut) _edTrimOut = Math.min(_edDuration, _edTrimIn + 3.0);
    const inEl = document.getElementById('inputTrimIn');
    const outEl = document.getElementById('inputTrimOut');
    if (inEl) inEl.value = _edTrimIn.toFixed(1);
    if (outEl) outEl.value = _edTrimOut.toFixed(1);
  } else {
    _edTrimOut = cur;
    if (_edTrimOut <= _edTrimIn) _edTrimIn = Math.max(0, _edTrimOut - 3.0);
    const inEl = document.getElementById('inputTrimIn');
    const outEl = document.getElementById('inputTrimOut');
    if (inEl) inEl.value = _edTrimIn.toFixed(1);
    if (outEl) outEl.value = _edTrimOut.toFixed(1);
  }
  updateTimelineVisuals();
}

function onTrimInputChange() {
  const inEl = document.getElementById('inputTrimIn');
  const outEl = document.getElementById('inputTrimOut');
  if (!inEl || !outEl) return;

  let valIn = parseFloat(inEl.value) || 0.0;
  let valOut = parseFloat(outEl.value) || _edDuration;

  valIn = Math.max(0, Math.min(_edDuration - 1.0, valIn));
  valOut = Math.max(valIn + 1.0, Math.min(_edDuration, valOut));

  _edTrimIn = valIn;
  _edTrimOut = valOut;

  inEl.value = valIn.toFixed(1);
  outEl.value = valOut.toFixed(1);

  updateTimelineVisuals();
}

function updateTimelineVisuals() {
  const rangeEl = document.getElementById('timelineActiveRange');
  const durLabel = document.getElementById('editorTrimDurationLabel');
  if (!_edDuration) return;

  const leftPct = (_edTrimIn / _edDuration) * 100;
  const widthPct = ((_edTrimOut - _edTrimIn) / _edDuration) * 100;

  if (rangeEl) {
    rangeEl.style.left = `${leftPct}%`;
    rangeEl.style.width = `${widthPct}%`;
  }

  const trimmedDur = (_edTrimOut - _edTrimIn) / _edSpeed;
  if (durLabel) {
    durLabel.textContent = `Trimmed: ${trimmedDur.toFixed(1)}s (at ${_edSpeed}x)`;
  }
}

function onSpeedChange(val) {
  _edSpeed = parseFloat(val) || 1.0;
  const vEl = document.getElementById('editorVideo');
  if (vEl) vEl.playbackRate = _edSpeed;
  updateTimelineVisuals();
}

function applyEditorFilter(preset, chipEl) {
  _edActiveFilter = preset;
  // Update chips
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  if (chipEl) chipEl.classList.add('active');

  // Live CSS Filter on video
  const vEl = document.getElementById('editorVideo');
  const label = document.getElementById('editorActiveFilterLabel');
  const css = _edFilterCssMap[preset] || 'none';
  if (vEl) {
    vEl.style.filter = css;
  }
  if (label) {
    const name = chipEl ? chipEl.querySelector('.filter-chip-name').textContent : preset;
    label.innerHTML = `Filter: <strong>${name}</strong>`;
  }
}

function onHookTextInput(val) {
  const overlay = document.getElementById('editorHookOverlay');
  if (!overlay) return;
  if (val.trim()) {
    overlay.textContent = val.trim();
    overlay.style.display = 'block';
  } else {
    overlay.style.display = 'none';
  }
}

function setHookPos(pos) {
  _edHookPos = pos;
  ['posTop', 'posCenter', 'posBottom'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.classList.remove('active');
  });

  const activeBtn = document.getElementById(pos === 'top' ? 'posTop' : (pos === 'center' ? 'posCenter' : 'posBottom'));
  if (activeBtn) activeBtn.classList.add('active');

  const overlay = document.getElementById('editorHookOverlay');
  if (overlay) {
    overlay.className = `editor-hook-overlay pos-${pos}`;
  }
}

function onVoiceVolChange(val) {
  const label = document.getElementById('voiceVolLabel');
  if (label) label.textContent = `${val}%`;
}

// 1-Click AI God Mode Auto-Enhance
function triggerAiGodMode() {
  if (!_edCurrentVideo) {
    toast('Please select a video first', 'warn');
    return;
  }

  // Optimize trim to ideal 28s duration
  _edTrimIn = 0.0;
  _edTrimOut = Math.min(_edDuration, 28.0);
  const inEl = document.getElementById('inputTrimIn');
  const outEl = document.getElementById('inputTrimOut');
  if (inEl) inEl.value = '0.0';
  if (outEl) outEl.value = _edTrimOut.toFixed(1);

  // Set speed to 1.1x
  _edSpeed = 1.1;
  const speedSel = document.getElementById('selectSpeed');
  if (speedSel) speedSel.value = '1.1';
  onSpeedChange('1.1');

  // Apply winning Cyberpunk color grade
  const chips = document.querySelectorAll('.filter-chip');
  if (chips.length > 1) {
    applyEditorFilter('cyberpunk', chips[1]);
  }

  // Auto hook headline
  const hookInp = document.getElementById('inputHookText');
  if (hookInp && !hookInp.value) {
    hookInp.value = 'WAIT TILL THE END 😱';
    onHookTextInput('WAIT TILL THE END 😱');
  }

  updateTimelineVisuals();
  toast('✨ AI God Mode Applied: 28s Sweet Spot + Cyberpunk Color Grade + 1.1x Pacing!', 'ok');
}

// Export Cut API
async function exportEditedCut() {
  if (!_edCurrentVideo) {
    toast('Select a video first', 'warn');
    return;
  }

  const btn = document.getElementById('btnExportCut');
  const resultCard = document.getElementById('exportResultCard');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Rendering FFmpeg Cut...</span>';
  }
  if (resultCard) resultCard.classList.remove('active');

  const payload = {
    video_id: _edCurrentVideo.video_id,
    start_sec: _edTrimIn,
    end_sec: _edTrimOut,
    speed: _edSpeed,
    filter_preset: _edActiveFilter,
    hook_headline: (document.getElementById('inputHookText') || {}).value || '',
    hook_position: _edHookPos,
    voice_volume: (parseFloat((document.getElementById('rangeVoiceVol') || {}).value) || 100) / 100.0,
    fade_audio: (document.getElementById('checkFadeAudio') || {}).checked !== false
  };

  try {
    const res = await fetch('/api/editor/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.ok) {
      toast(`Export failed: ${data.error || 'Unknown error'}`, 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>⚡ Render & Export Cut</span>';
      }
      return;
    }

    // Success! Show download card
    toast(`🎉 Cut rendered in ${data.render_time_sec}s!`, 'ok');
    if (resultCard) {
      resultCard.classList.add('active');
      const badge = document.getElementById('exportDurationBadge');
      const msg = document.getElementById('exportStatusMsg');
      const dlBtn = document.getElementById('btnDownloadExport');
      if (badge) badge.textContent = `${data.duration}s (${data.filter_applied})`;
      if (msg) msg.textContent = `Rendered in ${data.render_time_sec}s. Ready to publish or download.`;
      if (dlBtn) dlBtn.href = data.output_url;
    }

    // Refresh video list
    loadEditorVideos();
  } catch (err) {
    console.error('exportEditedCut error', err);
    toast('Network error while exporting video', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>⚡ Render & Export Cut</span>';
    }
  }
}
"""
