"""
web/onboarding_tour.py — Interactive Guided Onboarding Tour with Cute Mini Robot Mascot.

Features:
  1. Cute animated SVG mini robot mascot ("Robo-Pilot 🤖") with blinking digital eyes,
     floating hover physics, and radar antenna pulse.
  2. Non-intrusive Welcome Modal: asks user if they want a tour ("Start Tour" vs "Skip / I'll explore myself").
  3. Interactive 6-step guided walkthrough highlighting key tools (Studio, Connect, Editor, ML, Tasks, Copilot)
     with automatic tab switching and glowing spotlight focus.
  4. Persistent state in localStorage (doesn't annoy returning users), with 1-click replay anytime.
"""

TOUR_CSS = r"""
/* ==========================================================================
   CUTE MINI ROBOT MASCOT & INTERACTIVE GUIDED TOUR STYLING
   ========================================================================== */

/* Animated Mini Robot Mascot */
.robo-mascot {
  width: 96px;
  height: 96px;
  display: inline-block;
  animation: robo-float 3.5s ease-in-out infinite;
  filter: drop-shadow(0 10px 20px rgba(0, 242, 254, 0.4));
  user-select: none;
}
.robo-mascot-sm {
  width: 54px;
  height: 54px;
  animation: robo-float 3.5s ease-in-out infinite;
  filter: drop-shadow(0 6px 14px rgba(0, 242, 254, 0.3));
}

@keyframes robo-float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-8px) rotate(2deg);
  }
}

/* Eye Blink Animation */
.robo-eye {
  animation: robo-blink 4s infinite;
  transform-origin: center;
}
@keyframes robo-blink {
  0%, 46%, 48%, 100% {
    transform: scaleY(1);
  }
  47% {
    transform: scaleY(0.1);
  }
}

/* Radar Antenna Pulse */
.robo-antenna-glow {
  animation: robo-radar 2s infinite ease-in-out;
}
@keyframes robo-radar {
  0%, 100% {
    opacity: 0.4;
    r: 5;
  }
  50% {
    opacity: 1;
    r: 7;
    filter: drop-shadow(0 0 6px #00f2fe);
  }
}

/* Welcome Prompt Modal */
.tour-welcome-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 8, 20, 0.85);
  backdrop-filter: blur(12px);
  z-index: 100002;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.tour-welcome-card {
  background: linear-gradient(135deg, rgba(13, 21, 44, 0.95), rgba(9, 15, 34, 0.98));
  border: 1px solid rgba(0, 242, 254, 0.35);
  border-radius: 24px;
  width: 100%;
  max-width: 480px;
  padding: 32px 28px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 242, 254, 0.2);
  position: relative;
  overflow: hidden;
}
.tour-welcome-card::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 242, 254, 0.1) 0%, transparent 60%);
  pointer-events: none;
}

.tour-welcome-title {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  margin: 16px 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.tour-welcome-desc {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.6;
  margin-bottom: 24px;
}

.tour-welcome-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-start-tour {
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  color: #000;
  font-weight: 800;
  font-size: 15px;
  padding: 14px 24px;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(0, 242, 254, 0.4);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-start-tour:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(0, 242, 254, 0.6);
}

.btn-skip-tour {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 18px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-skip-tour:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

/* Floating Tour Step Dialog */
.tour-step-card {
  position: fixed;
  z-index: 100005;
  background: linear-gradient(135deg, rgba(13, 21, 44, 0.96), rgba(9, 15, 34, 0.98));
  border: 1px solid rgba(0, 242, 254, 0.4);
  border-radius: 20px;
  padding: 20px 24px;
  width: 90vw;
  max-width: 440px;
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 242, 254, 0.25);
  backdrop-filter: blur(16px);
  display: none;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.tour-step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.tour-badge-step {
  background: rgba(0, 242, 254, 0.15);
  border: 1px solid rgba(0, 242, 254, 0.4);
  color: #00f2fe;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

.tour-step-title {
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  margin: 0;
}

.tour-step-content {
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.6;
  margin-bottom: 18px;
}

.tour-step-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tour-nav-btns {
  display: flex;
  gap: 8px;
}

.btn-tour-nav {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-tour-nav:hover {
  background: rgba(255, 255, 255, 0.18);
}
.btn-tour-nav.primary {
  background: linear-gradient(135deg, #00f2fe, #38bdf8);
  color: #000;
  font-weight: 800;
  border: none;
}
.btn-tour-nav.primary:hover {
  transform: scale(1.04);
}

/* Spotlight Highlight Ring */
.tour-target-highlight {
  position: relative;
  z-index: 99997 !important;
  box-shadow: 0 0 0 4px #00f2fe, 0 0 30px rgba(0, 242, 254, 0.7) !important;
  border-radius: 12px;
  transition: box-shadow 0.3s ease;
}

/* Official Google Sign In Button */
.btn-google-auth {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  background: #ffffff;
  color: #1f2937;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
  margin-bottom: 16px;
}
.btn-google-auth:hover {
  background: #f9fafb;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
  transform: translateY(-1px);
}
.google-g-icon {
  width: 20px;
  height: 20px;
  display: block;
}
"""


TOUR_HTML = r"""
<!-- CUTE MINI ROBOT WELCOME PROMPT MODAL -->
<div id="tourWelcomeModal" class="tour-welcome-overlay">
  <div class="tour-welcome-card">
    <!-- Inline Cute SVG Robot Mascot -->
    <div class="robo-mascot">
      <svg viewBox="0 0 120 120" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Antenna -->
        <line x1="60" y1="28" x2="60" y2="12" stroke="#00f2fe" stroke-width="4" stroke-linecap="round"/>
        <circle class="robo-antenna-glow" cx="60" cy="10" r="6" fill="#00f2fe"/>
        <!-- Robot Head Frame -->
        <rect x="25" y="28" width="70" height="52" rx="18" fill="#111c38" stroke="#00f2fe" stroke-width="3"/>
        <!-- Digital Face Screen -->
        <rect x="33" y="36" width="54" height="36" rx="12" fill="#060b18"/>
        <!-- Cute Blinking LED Eyes -->
        <circle class="robo-eye" cx="48" cy="54" r="6" fill="#00f2fe"/>
        <circle cx="50" cy="52" r="2" fill="#ffffff"/>
        <circle class="robo-eye" cx="72" cy="54" r="6" fill="#00f2fe"/>
        <circle cx="74" cy="52" r="2" fill="#ffffff"/>
        <!-- Cute Curved Smile -->
        <path d="M52 64 Q60 70 68 64" stroke="#a855f7" stroke-width="3" stroke-linecap="round" fill="none"/>
        <!-- Floating Body Chassis -->
        <rect x="36" y="84" width="48" height="24" rx="10" fill="#1a274e" stroke="#8b5cf6" stroke-width="2.5"/>
        <!-- Thruster Glow -->
        <ellipse cx="60" cy="110" rx="14" ry="4" fill="#00f2fe" opacity="0.6"/>
      </svg>
    </div>

    <h3 class="tour-welcome-title">
      <span>Hello Creator! I'm Robo-Pilot</span> <span>🤖✨</span>
    </h3>
    <p class="tour-welcome-desc">
      Welcome to Autopilot Studio! Would you like a 1-minute interactive guided tour to explore automated video generation, channel integrations, and AI creator tools?
    </p>

    <div class="tour-welcome-actions">
      <button class="btn-start-tour" onclick="startGuidedTour()">
        <span>🚀 Yes, Start Guided Tour!</span>
      </button>
      <button class="btn-skip-tour" onclick="dismissTourWelcome(true)">
        <span>I'll explore on my own (Skip)</span>
      </button>
    </div>
  </div>
</div>

<!-- INTERACTIVE FLOATING TOUR STEP CARD -->
<div id="tourStepCard" class="tour-step-card">
  <div class="tour-step-header">
    <div class="robo-mascot-sm">
      <svg viewBox="0 0 120 120" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg">
        <line x1="60" y1="28" x2="60" y2="12" stroke="#00f2fe" stroke-width="4" stroke-linecap="round"/>
        <circle class="robo-antenna-glow" cx="60" cy="10" r="6" fill="#00f2fe"/>
        <rect x="25" y="28" width="70" height="52" rx="18" fill="#111c38" stroke="#00f2fe" stroke-width="3"/>
        <rect x="33" y="36" width="54" height="36" rx="12" fill="#060b18"/>
        <circle class="robo-eye" cx="48" cy="54" r="5" fill="#00f2fe"/>
        <circle class="robo-eye" cx="72" cy="54" r="5" fill="#00f2fe"/>
        <path d="M52 64 Q60 68 68 64" stroke="#a855f7" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      </svg>
    </div>
    <div>
      <div class="tour-badge-step" id="tourStepBadge">Step 1 of 6</div>
      <h4 class="tour-step-title" id="tourStepTitle">Studio &amp; Series Creator</h4>
    </div>
  </div>

  <div class="tour-step-content" id="tourStepBody">
    Generate flagship anime series episodes like 'Kaal-Rekha' or produce custom viral videos with 1-click autonomous screenplays, neural voiceovers, and flux visual generation.
  </div>

  <div class="tour-step-footer">
    <button class="btn-tour-nav" onclick="dismissTourWelcome(true)">Skip Tour</button>
    <div class="tour-nav-btns">
      <button class="btn-tour-nav" id="btnTourPrev" onclick="prevTourStep()">Back</button>
      <button class="btn-tour-nav primary" id="btnTourNext" onclick="nextTourStep()">Next ➔</button>
    </div>
  </div>
</div>
"""


TOUR_JS = r"""
/* ==========================================================================
   INTERACTIVE GUIDED TOUR ENGINE & MASCOT CONTROLLER (100% ENGLISH)
   ========================================================================== */

const TOUR_STEPS = [
  {
    tab: 'studio',
    target: '#tab-studio',
    badge: 'Step 1 of 6',
    title: '🚀 Studio (Create Videos)',
    content: 'Generate flagship anime series episodes like "Kaal-Rekha" or produce custom viral videos with 1-click autonomous screenplays, neural voiceovers, and flux visual generation.'
  },
  {
    tab: 'onboarding',
    target: '#tab-onboarding',
    badge: 'Step 2 of 6',
    title: '🔗 Connect & Channels Hub',
    content: 'Link your YouTube Shorts and Instagram Reels channels. Autopilot executes autonomous 308 resumable publishing with mandatory automated AI disclosure tags.'
  },
  {
    tab: 'editor',
    target: '#tab-editor',
    badge: 'Step 3 of 6',
    title: '✂️ God-Level Mini Video Editor',
    content: 'Our built-in video editor allows you to adjust In/Out points, apply cinematic Cyberpunk/Golden Hour color grading, and attach viral hook stickers in real-time.'
  },
  {
    tab: 'ml',
    target: '#tab-ml',
    badge: 'Step 4 of 6',
    title: '🧠 AI Brain & ML Studio',
    content: 'Autopilot\'s self-learning machine learning engine analyzes your past video retention curves and predicts retention scores before rendering new screenplays.'
  },
  {
    tab: 'tasks',
    target: '#tab-tasks',
    badge: 'Step 5 of 6',
    title: '📋 Tasks & 1-Click Auto-Fix',
    content: 'Monitor real-time multi-agent swarm rendering tasks and system health. Use 1-Click Auto-Fix to automatically heal pipeline bottlenecks.'
  },
  {
    tab: 'studio',
    target: '#btnTopCopilot',
    badge: 'Step 6 of 6',
    title: '🤖 AI Copilot (Voice & Text Assistant)',
    content: 'Interact with your autonomous swarm anytime via voice or text in fluent English. Instruct Copilot to generate episodes, troubleshoot, or connect channels.'
  }
];

let _tourCurrentIndex = 0;
let _tourActive = false;

// Check if new user needs a tour
function checkNewUserTour(forcePrompt = false) {
  if (!authUser) return;
  const uid = authUser.user_id || 'guest';

  // Founder/Admin is NEVER prompted automatically on login/load
  if (!forcePrompt && (uid === 'admin_abhay' || authUser.role === 'admin')) {
    return;
  }

  // Check if user already marked tour complete either in DB or in localStorage
  const isDbDone = (authUser.tour_completed == 1) || (authUser.tour_completed === true);
  const isLocalDone = (localStorage.getItem('autopilot_tour_done_' + uid) === 'true') || (localStorage.getItem('autopilot_tour_done') === 'true');
  if (!forcePrompt && (isDbDone || isLocalDone)) {
    return;
  }

  // Show cute mini robot welcome modal once
  setTimeout(() => {
    const modal = document.getElementById('tourWelcomeModal');
    if (modal) modal.style.display = 'flex';
    if (typeof audio !== 'undefined' && audio.beep) audio.beep(600, 0.15);
  }, 400);
}

function dismissTourWelcome(markDone = true) {
  const modal = document.getElementById('tourWelcomeModal');
  const card = document.getElementById('tourStepCard');
  if (modal) modal.style.display = 'none';
  if (card) card.style.display = 'none';
  removeTourHighlight();
  _tourActive = false;

  if (markDone) {
    const uid = authUser ? authUser.user_id : 'guest';
    localStorage.setItem('autopilot_tour_done_' + uid, 'true');
    localStorage.setItem('autopilot_tour_done', 'true');

    if (authUser) {
      authUser.tour_completed = 1;
      localStorage.setItem('autopilot_auth_user', JSON.stringify(authUser));

      // Persist permanently in backend database
      fetch('/api/user/tour-complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': uid },
        body: JSON.stringify({ user_id: uid })
      }).catch(() => {});
    }
  }
  if (typeof audio !== 'undefined' && audio.click) audio.click();
}

function startGuidedTour() {
  const modal = document.getElementById('tourWelcomeModal');
  if (modal) modal.style.display = 'none';
  _tourActive = true;
  _tourCurrentIndex = 0;
  if (typeof audio !== 'undefined' && audio.success) audio.success();
  renderTourStep(_tourCurrentIndex);
}

function replayTour() {
  if (typeof audio !== 'undefined' && audio.click) audio.click();
  startGuidedTour();
}

function renderTourStep(index) {
  if (index < 0 || index >= TOUR_STEPS.length) {
    finishTour();
    return;
  }

  const step = TOUR_STEPS[index];
  
  // Switch to the relevant tab
  if (typeof switchNav === 'function' && step.tab) {
    switchNav(step.tab);
  }

  removeTourHighlight();

  // Allow DOM & animations to settle before computing positions (avoids 0,0 glitch)
  setTimeout(() => {
    _positionStepCard(index);
  }, 120);
}

function _positionStepCard(index) {
  if (!_tourActive) return;
  const step = TOUR_STEPS[index];
  const targetEl = document.querySelector(step.target);

  if (targetEl) {
    targetEl.classList.add('tour-target-highlight');
    try {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    } catch(e) {}
  }

  const card = document.getElementById('tourStepCard');
  const badge = document.getElementById('tourStepBadge');
  const title = document.getElementById('tourStepTitle');
  const body = document.getElementById('tourStepBody');
  const btnPrev = document.getElementById('btnTourPrev');
  const btnNext = document.getElementById('btnTourNext');

  if (badge) badge.textContent = step.badge;
  if (title) title.textContent = step.title;
  if (body) body.textContent = step.content;

  if (btnPrev) btnPrev.style.display = index === 0 ? 'none' : 'inline-block';
  if (btnNext) btnNext.textContent = index === TOUR_STEPS.length - 1 ? '🎉 Finish Tour!' : 'Next ➔';

  if (card) {
    card.style.display = 'block';
    const cardWidth = Math.min(420, window.innerWidth - 32);
    card.style.width = cardWidth + 'px';

    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      const cardHeight = 220;
      let top = rect.bottom + 14;
      let left = Math.max(16, Math.min(window.innerWidth - cardWidth - 16, rect.left));

      // Flip above if too close to bottom
      if (top + cardHeight > window.innerHeight) {
        top = Math.max(16, rect.top - cardHeight - 14);
      }
      card.style.top = `${top}px`;
      card.style.left = `${left}px`;
      card.style.bottom = 'auto';
      card.style.transform = 'none';
    } else {
      card.style.top = 'auto';
      card.style.bottom = '24px';
      card.style.left = '50%';
      card.style.transform = 'translateX(-50%)';
    }
  }

  if (typeof audio !== 'undefined' && audio.beep) audio.beep(750, 0.08);
}

// Keep step card aligned on window resize
window.addEventListener('resize', () => {
  if (_tourActive) {
    _positionStepCard(_tourCurrentIndex);
  }
});

function nextTourStep() {
  if (_tourCurrentIndex < TOUR_STEPS.length - 1) {
    _tourCurrentIndex++;
    renderTourStep(_tourCurrentIndex);
  } else {
    finishTour();
  }
}

function prevTourStep() {
  if (_tourCurrentIndex > 0) {
    _tourCurrentIndex--;
    renderTourStep(_tourCurrentIndex);
  }
}

function finishTour() {
  dismissTourWelcome(true);
  toast('🎉 Guided Tour Complete! Your workspace is fully ready.', 'ok');
  if (typeof audio !== 'undefined' && audio.success) audio.success();
}

function removeTourHighlight() {
  document.querySelectorAll('.tour-target-highlight').forEach(el => {
    el.classList.remove('tour-target-highlight');
  });
}

"""

