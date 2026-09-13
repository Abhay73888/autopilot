"""
web/ml_studio.py — AI Brain & ML Studio frontend component.

Includes:
  1. ML_STUDIO_CSS: Styling for Wan2.1 generator cards, retention prediction meter, and learned weights.
  2. ML_STUDIO_TAB_HTML: Dashboard tab structure for section #sec-ml.
  3. ML_STUDIO_JS: Client-side logic for predicting retention, retraining the ML model, and testing Wan2.1.
"""

ML_STUDIO_CSS = r"""
/* ==========================================================================
   AI BRAIN & ML STUDIO GLASSMORPHIC STYLING
   ========================================================================== */
.ml-dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}
@media (max-width: 1080px) {
  .ml-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.ml-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(12px);
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}
.ml-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.ml-card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Wan2.1 Banner & Details */
.wan-banner {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(0, 242, 254, 0.1));
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.wan-tag {
  background: rgba(168, 85, 247, 0.25);
  border: 1px solid var(--purple);
  color: #d8b4fe;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.wan-specs-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 18px;
}
.wan-spec-box {
  background: rgba(5, 8, 20, 0.6);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}
.wan-spec-lbl {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.wan-spec-val {
  font-size: 14px;
  font-weight: 700;
  color: var(--cyan);
}

/* Retention Gauge Meter */
.retention-meter-box {
  display: flex;
  align-items: center;
  gap: 24px;
  background: rgba(5, 8, 20, 0.7);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 20px;
}
.meter-circle {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: conic-gradient(var(--cyan) calc(var(--prs-pct, 74) * 1%), rgba(255, 255, 255, 0.08) 0);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  flex-shrink: 0;
  box-shadow: 0 0 20px rgba(0, 242, 254, 0.2);
}
.meter-circle-inner {
  width: 86px;
  height: 86px;
  border-radius: 50%;
  background: #090f22;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.meter-val {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 800;
  color: #fff;
}
.meter-lbl {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
}

.meter-details h4 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--green);
}
.meter-details p {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

/* Feature Importance Horizontal Bars */
.feature-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}
.feature-bar-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.feature-bar-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
}
.feature-bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}
.feature-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--cyan), var(--purple));
}

/* Guidelines List */
.guidelines-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.guideline-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.5;
}
.guideline-item span.icon {
  color: var(--cyan);
  font-size: 16px;
}
"""

ML_STUDIO_TAB_HTML = r"""
  <!-- ============================================================== -->
  <!-- TAB: AI BRAIN & ML STUDIO (WAN2.1 + RETENTION FLYWHEEL) -->
  <!-- ============================================================== -->
  <section class="tab-section" id="sec-ml">
    <!-- WAN2.1 MODEL BANNER -->
    <div class="wan-banner">
      <div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <h2 style="font-family:'Outfit',sans-serif; font-size:20px; font-weight:800;">Alibaba Wan2.1 Video Generator</h2>
          <span class="wan-tag">CINEMA SOTA</span>
        </div>
        <p style="font-size:13px; color:var(--text-muted);">
          Active video diffusion engine for high-framerate 9:16 Shorts with dynamic character physics and camera motion.
        </p>
      </div>
      <div style="display:flex; gap:10px; align-items:center;">
        <span class="status-pill"><span class="copilot-orb"></span> Engine Ready</span>
        <button class="btn btn-ghost" onclick="testWan21Clip()">⚡ Test Wan2.1 Clip</button>
      </div>
    </div>

    <!-- SPECS GRID -->
    <div class="wan-specs-grid">
      <div class="wan-spec-box">
        <div class="wan-spec-lbl">ACTIVE MODEL</div>
        <div class="wan-spec-val" id="mlWanModel">Wan2.1 (1.3B / 14B)</div>
      </div>
      <div class="wan-spec-box">
        <div class="wan-spec-lbl">FORMAT &amp; FPS</div>
        <div class="wan-spec-val">9:16 HD @ 24 FPS</div>
      </div>
      <div class="wan-spec-box">
        <div class="wan-spec-lbl">FALLBACK CHAIN</div>
        <div class="wan-spec-val" style="font-size:12px; color:var(--text-main);">Wan2.1 → Flux Motion → Procedural</div>
      </div>
    </div>

    <!-- MAIN DUAL GRID -->
    <div class="ml-dashboard-grid">
      <!-- LEFT: RETENTION PREDICTOR TOOL -->
      <div class="ml-card">
        <div class="ml-card-header">
          <div class="ml-card-title">🔮 Real-Time Retention Predictor (PRS)</div>
          <span class="status-pill" id="mlConfidencePill">Calibrated Model</span>
        </div>
        <p style="font-size:13px; color:var(--text-muted); margin-bottom:16px;">
          Nayi video script generate karne se pehle uska retention score evaluate karein:
        </p>

        <div style="margin-bottom:14px;">
          <label style="font-size:12px; color:var(--text-muted); font-weight:600;">Test Video Topic:</label>
          <input type="text" id="mlTestTopic" class="custom-input" style="width:100%; margin-top:4px;" value="3:17 AM Mystery Time Loop Ka Rahasya">
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px;">
          <div>
            <label style="font-size:12px; color:var(--text-muted); font-weight:600;">Hook Formula:</label>
            <select id="mlTestHook" class="ep-select" style="width:100%; margin-top:4px;">
              <option value="contrarian">Contrarian Hook (High 1s)</option>
              <option value="specific_outcome">Specific Outcome</option>
              <option value="question">Question Bait</option>
              <option value="pov">POV Character</option>
            </select>
          </div>
          <div>
            <label style="font-size:12px; color:var(--text-muted); font-weight:600;">Scene Pacing:</label>
            <select id="mlTestPacing" class="ep-select" style="width:100%; margin-top:4px;">
              <option value="7">Fast Cuts (7 scenes / ~22-30s)</option>
              <option value="5">Standard (5 scenes / ~30-40s)</option>
              <option value="4">Relaxed (4 scenes / ~45s)</option>
            </select>
          </div>
        </div>

        <div style="margin-bottom:18px;">
          <label style="font-size:12px; color:var(--text-muted); font-weight:600;">Script Opening Lines:</label>
          <textarea id="mlTestScript" class="custom-input" rows="3" style="width:100%; margin-top:4px; resize:vertical;">Agar aapko lagta hai ki ghadi theek chal rahi hai, to 3:17 AM ka ye rahasya aapki neend uda dega. Kabir har raat theek isi second pe wapas laut jata hai.</textarea>
        </div>

        <button class="btn btn-primary" style="width:100%; justify-content:center; margin-bottom:20px;" onclick="evaluateRetentionPrediction()">⚡ Evaluate Retention Potential</button>

        <!-- PREDICTION OUTPUT -->
        <div class="retention-meter-box" id="mlMeterBox">
          <div class="meter-circle" id="mlMeterCircle" style="--prs-pct:78;">
            <div class="meter-circle-inner">
              <span class="meter-val" id="mlMeterVal">78%</span>
              <span class="meter-lbl">Predicted</span>
            </div>
          </div>
          <div class="meter-details">
            <h4 id="mlMeterGrade">🔥 High Potential (Viral Velocity)</h4>
            <p id="mlMeterSuggestions">Opening hook brevity is optimal. Pacing ensures retention through critical 1s and 3s distribution gates.</p>
          </div>
        </div>
      </div>

      <!-- RIGHT: LEARNING BRAIN & EVOLVING WEIGHTS -->
      <div class="ml-card">
        <div class="ml-card-header">
          <div class="ml-card-title">🧠 Learning Brain &amp; Retention Flywheel</div>
          <button class="btn btn-ghost" style="padding:4px 10px; font-size:12px;" onclick="retrainMLModel()">🔄 Retrain On DB</button>
        </div>

        <p style="font-size:13px; color:var(--text-muted); margin-bottom:14px;">
          Har published video ke 2h velocity aur retention signals se model automatically seekhta hai:
        </p>

        <!-- FEATURE IMPORTANCE WEIGHTS -->
        <h4 style="font-size:13px; font-weight:700; margin-bottom:8px;">Model Feature Importance (Retention Drivers):</h4>
        <div class="feature-bars" id="mlFeatureBars">
          <!-- Populated dynamically via JS -->
        </div>

        <hr style="border:none; border-top:1px solid var(--border); margin:20px 0;">

        <!-- EVOLVED GUIDELINES -->
        <h4 style="font-size:13px; font-weight:700; margin-bottom:10px;">Auto-Evolved Prompt Guidelines (Injected in Writer):</h4>
        <div class="guidelines-list" id="mlGuidelinesList">
          <!-- Populated dynamically via JS -->
        </div>
      </div>
    </div>
  </section>
"""

ML_STUDIO_JS = r"""
// ==============================================================================
// AI BRAIN & ML STUDIO CLIENT CONTROLLER
// ==============================================================================
async function loadMLInsights() {
  try {
    const res = await fetch('/api/ml/insights');
    const data = await res.json();
    if (!data.ok) return;

    // Render Feature Bars
    const barsContainer = document.getElementById('mlFeatureBars');
    if (barsContainer && data.weights && data.feature_labels) {
      barsContainer.innerHTML = data.feature_labels.map((lbl, i) => {
        const wt = data.weights[i] || 0.1;
        const pct = Math.min(Math.round(wt * 300), 100);
        return `
          <div class="feature-bar-row">
            <div class="feature-bar-header">
              <span>${lbl}</span>
              <span style="color:var(--cyan);">${(wt * 100).toFixed(1)}% weight</span>
            </div>
            <div class="feature-bar-track">
              <div class="feature-bar-fill" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Render Guidelines
    const guideContainer = document.getElementById('mlGuidelinesList');
    if (guideContainer && data.guidelines) {
      guideContainer.innerHTML = data.guidelines.map(g => {
        const text = g.replace(/^-\s*/, '');
        if (!text) return '';
        return `
          <div class="guideline-item">
            <span class="icon">💡</span>
            <div>${esc(text)}</div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('loadMLInsights error:', err);
  }
}

async function evaluateRetentionPrediction() {
  const topic = document.getElementById('mlTestTopic').value;
  const hook = document.getElementById('mlTestHook').value;
  const pacing = parseInt(document.getElementById('mlTestPacing').value) || 7;
  const script = document.getElementById('mlTestScript').value;

  try {
    const res = await fetch('/api/ml/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        hook_type: hook,
        scene_count: pacing,
        script: script,
        length_sec: 32.0
      })
    });
    const data = await res.json();
    if (!data.ok || !data.result) return;

    const r = data.result;
    const meterCircle = document.getElementById('mlMeterCircle');
    const meterVal = document.getElementById('mlMeterVal');
    const meterGrade = document.getElementById('mlMeterGrade');
    const meterSuggestions = document.getElementById('mlMeterSuggestions');

    if (meterCircle) meterCircle.style.setProperty('--prs-pct', r.predicted_retention_pct);
    if (meterVal) meterVal.textContent = r.predicted_retention_pct + '%';
    if (meterGrade) meterGrade.textContent = r.velocity_grade;
    if (meterSuggestions) {
      meterSuggestions.innerHTML = r.suggestions.map(s => `• ${esc(s)}`).join('<br>');
    }
  } catch (err) {
    alert('Prediction error: ' + err.message);
  }
}

async function retrainMLModel() {
  try {
    const res = await fetch('/api/ml/train', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      alert(`Model successfully retrained on ${data.samples_trained} empirical samples! Updated R² score: ${data.r2_score}`);
      loadMLInsights();
    } else {
      alert('Retrain notice: ' + (data.error || 'Failed'));
    }
  } catch (err) {
    alert('Retrain error: ' + err.message);
  }
}

function testWan21Clip() {
  alert('Wan2.1 Generator Ready: 9:16 vertical clips configured with Replicate/Fal/Flux-motion fallback chain.');
}

// Hook into tab switches
const _origSwitchNav = window.switchNav;
window.switchNav = function(tabId) {
  if (_origSwitchNav) _origSwitchNav(tabId);
  if (tabId === 'ml') {
    loadMLInsights();
    evaluateRetentionPrediction();
  }
};
"""
