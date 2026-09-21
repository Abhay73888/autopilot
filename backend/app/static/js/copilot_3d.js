/**
 * copilot_3d.js — 3D Humanoid Robot AI Assistant Engine
 * Powered by Three.js with Web Audio API Real-Time Lip-Sync & State Machine.
 */

(function (window) {
  'use strict';

  // Check WebGL availability
  function isWebGLAvailable() {
    try {
      const canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  class HumanoidRobot3D {
    constructor(containerEl, options = {}) {
      this.container = typeof containerEl === 'string' ? document.getElementById(containerEl) : containerEl;
      if (!this.container) {
        console.error('[Copilot3D] Container element not found');
        return;
      }

      this.options = Object.assign({
        fov: 36,
        accentColor: 0x06B6D4, // Cyan
        secondaryColor: 0x8B5CF6, // Purple
        reactorColor: 0x06B6D4,
        enableGazeTracking: true,
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
      }, options);

      this.state = 'IDLE'; // IDLE, LISTENING, THINKING, SPEAKING, SUCCESS, ERROR
      this.audioContext = null;
      this.analyser = null;
      this.audioSource = null;
      this.currentAudioElement = null;
      this.currentAudioLevel = 0;
      this.targetAudioLevel = 0;

      this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
      this.clock = null;
      this.animId = null;
      this.isVisible = true;

      // Eye blink state
      this.blinkProgress = 0;
      this.isBlinking = false;
      this.nextBlinkTime = 3.0;

      // Thinking scan state
      this.thinkingTimer = 0;

      this.init();
    }

    init() {
      if (!isWebGLAvailable() || typeof THREE === 'undefined') {
        console.warn('[Copilot3D] WebGL or Three.js unavailable. Falling back to 2D Animated Avatar.');
        this.init2DFallback();
        return;
      }

      try {
        this.initThreeJS();
        this.buildRobot();
        this.setupEvents();
        this.startRenderLoop();
      } catch (err) {
        console.error('[Copilot3D] Initialization failed:', err);
        this.init2DFallback();
      }
    }

    initThreeJS() {
      this.container.innerHTML = '';
      const w = this.container.clientWidth || 380;
      const h = this.container.clientHeight || 420;

      this.scene = new THREE.Scene();
      this.clock = new THREE.Clock();

      this.camera = new THREE.PerspectiveCamera(this.options.fov, w / h, 0.1, 100);
      this.camera.position.set(0, 0.45, 3.2);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      this.renderer.setSize(w, h);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      if (this.renderer.outputColorSpace) {
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      }
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.15;

      this.container.appendChild(this.renderer.domElement);

      // Lighting
      const ambientLight = new THREE.AmbientLight(0x181e36, 1.4);
      this.scene.add(ambientLight);

      const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
      keyLight.position.set(2.5, 4, 3);
      this.scene.add(keyLight);

      const fillLight = new THREE.DirectionalLight(0x8B5CF6, 1.6);
      fillLight.position.set(-3, 1, 2);
      this.scene.add(fillLight);

      this.rimLight = new THREE.PointLight(0x06B6D4, 2.8, 10);
      this.rimLight.position.set(0, 2.5, -2);
      this.scene.add(this.rimLight);

      this.chestLight = new THREE.PointLight(this.options.reactorColor, 2.2, 3.5);
      this.chestLight.position.set(0, -0.2, 0.8);
      this.scene.add(this.chestLight);
    }

    buildRobot() {
      this.robotGroup = new THREE.Group();
      this.robotGroup.position.set(0, -0.25, 0);
      this.scene.add(this.robotGroup);

      // Materials
      this.armorMat = new THREE.MeshStandardMaterial({
        color: 0x111624,
        roughness: 0.28,
        metalness: 0.82
      });

      this.chassisMat = new THREE.MeshStandardMaterial({
        color: 0x1e273d,
        roughness: 0.35,
        metalness: 0.7
      });

      this.chromeMat = new THREE.MeshStandardMaterial({
        color: 0x94A3B8,
        roughness: 0.15,
        metalness: 0.95
      });

      this.visorMat = new THREE.MeshStandardMaterial({
        color: 0x05070e,
        roughness: 0.1,
        metalness: 0.9,
        transparent: true,
        opacity: 0.95
      });

      this.glowCyanMat = new THREE.MeshBasicMaterial({
        color: 0x06B6D4
      });

      this.glowPurpleMat = new THREE.MeshBasicMaterial({
        color: 0x8B5CF6
      });

      // --- TORSO / UPPER BODY ---
      this.torsoGroup = new THREE.Group();
      this.robotGroup.add(this.torsoGroup);

      // Chest plate
      const chestGeo = new THREE.CylinderGeometry(0.42, 0.32, 0.65, 8);
      const chest = new THREE.Mesh(chestGeo, this.armorMat);
      chest.position.set(0, -0.15, 0);
      chest.scale.set(1.15, 1, 0.7);
      this.torsoGroup.add(chest);

      // Collar armor
      const collarGeo = new THREE.CylinderGeometry(0.24, 0.38, 0.22, 8);
      const collar = new THREE.Mesh(collarGeo, this.chassisMat);
      collar.position.set(0, 0.16, 0);
      collar.scale.set(1.1, 1, 0.8);
      this.torsoGroup.add(collar);

      // Chest Reactor Core (Glowing Arc Reactor)
      const coreGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.05, 32);
      this.coreMesh = new THREE.Mesh(coreGeo, this.glowCyanMat);
      this.coreMesh.rotation.x = Math.PI / 2;
      this.coreMesh.position.set(0, -0.12, 0.24);
      this.torsoGroup.add(this.coreMesh);

      const coreRingGeo = new THREE.TorusGeometry(0.14, 0.02, 16, 32);
      this.coreRing = new THREE.Mesh(coreRingGeo, this.chromeMat);
      this.coreRing.position.set(0, -0.12, 0.25);
      this.torsoGroup.add(this.coreRing);

      // Shoulders & Pauldrons
      [-1, 1].forEach(side => {
        const shoulderJointGeo = new THREE.SphereGeometry(0.14, 16, 16);
        const shoulderJoint = new THREE.Mesh(shoulderJointGeo, this.chromeMat);
        shoulderJoint.position.set(side * 0.52, 0.05, 0);
        this.torsoGroup.add(shoulderJoint);

        const pauldronGeo = new THREE.CylinderGeometry(0.15, 0.22, 0.25, 6);
        const pauldron = new THREE.Mesh(pauldronGeo, this.armorMat);
        pauldron.position.set(side * 0.55, 0.08, 0);
        pauldron.rotation.z = -side * 0.35;
        this.torsoGroup.add(pauldron);

        // Accent strip on shoulder
        const stripGeo = new THREE.BoxGeometry(0.02, 0.2, 0.16);
        const strip = new THREE.Mesh(stripGeo, this.glowCyanMat);
        strip.position.set(side * 0.64, 0.09, 0.02);
        this.torsoGroup.add(strip);
      });

      // --- NECK ---
      const neckGeo = new THREE.CylinderGeometry(0.12, 0.14, 0.2, 16);
      const neck = new THREE.Mesh(neckGeo, this.chromeMat);
      neck.position.set(0, 0.32, 0);
      this.torsoGroup.add(neck);

      // --- HEAD GROUP ---
      this.headGroup = new THREE.Group();
      this.headGroup.position.set(0, 0.52, 0);
      this.robotGroup.add(this.headGroup);

      // Helmet Cranium (Head Chassis)
      const helmetGeo = new THREE.SphereGeometry(0.38, 32, 24);
      const helmet = new THREE.Mesh(helmetGeo, this.armorMat);
      helmet.scale.set(0.95, 1.08, 1.05);
      this.headGroup.add(helmet);

      // Side Audio Receptor Pods (Ears)
      [-1, 1].forEach(side => {
        const earPodGeo = new THREE.CylinderGeometry(0.12, 0.14, 0.08, 16);
        const earPod = new THREE.Mesh(earPodGeo, this.chromeMat);
        earPod.rotation.z = Math.PI / 2;
        earPod.position.set(side * 0.38, 0.02, 0);
        this.headGroup.add(earPod);

        const earGlowGeo = new THREE.TorusGeometry(0.08, 0.015, 12, 24);
        const earGlow = new THREE.Mesh(earGlowGeo, this.glowCyanMat);
        earGlow.rotation.y = Math.PI / 2;
        earGlow.position.set(side * 0.425, 0.02, 0);
        this.headGroup.add(earGlow);
      });

      // Visor Face Plate
      const visorGeo = new THREE.SphereGeometry(0.32, 28, 20, 0, Math.PI);
      const visor = new THREE.Mesh(visorGeo, this.visorMat);
      visor.rotation.y = -Math.PI / 2;
      visor.position.set(0, 0.02, 0.12);
      visor.scale.set(0.9, 0.95, 1.05);
      this.headGroup.add(visor);

      // --- DIGITAL FACE DISPLAY (Eyes & Mouth) ---
      // Eyes
      this.eyeLeftGroup = new THREE.Group();
      this.eyeRightGroup = new THREE.Group();
      this.eyeLeftGroup.position.set(-0.12, 0.06, 0.4);
      this.eyeRightGroup.position.set(0.12, 0.06, 0.4);
      this.headGroup.add(this.eyeLeftGroup);
      this.headGroup.add(this.eyeRightGroup);

      const eyeGeo = new THREE.CylinderGeometry(0.048, 0.048, 0.02, 24);
      const eyeL = new THREE.Mesh(eyeGeo, this.glowCyanMat);
      eyeL.rotation.x = Math.PI / 2;
      this.eyeLeftGroup.add(eyeL);

      const eyeR = new THREE.Mesh(eyeGeo, this.glowCyanMat);
      eyeR.rotation.x = Math.PI / 2;
      this.eyeRightGroup.add(eyeR);

      // Eye outer glow halos
      const haloGeo = new THREE.RingGeometry(0.052, 0.075, 24);
      const haloL = new THREE.Mesh(haloGeo, this.glowPurpleMat);
      haloL.position.set(0, 0, 0.01);
      this.eyeLeftGroup.add(haloL);

      const haloR = new THREE.Mesh(haloGeo, this.glowPurpleMat);
      haloR.position.set(0, 0, 0.01);
      this.eyeRightGroup.add(haloR);

      // --- DIGITAL MOUTH / AUDIO RECEPTOR APERTURE ---
      this.mouthBars = [];
      this.mouthGroup = new THREE.Group();
      this.mouthGroup.position.set(0, -0.12, 0.38);
      this.headGroup.add(this.mouthGroup);

      // 5-bar cybernetic waveform mouth
      const barCount = 7;
      const barWidth = 0.022;
      for (let i = 0; i < barCount; i++) {
        const xPos = (i - Math.floor(barCount / 2)) * (barWidth + 0.012);
        const barGeo = new THREE.BoxGeometry(barWidth, 0.02, 0.01);
        const bar = new THREE.Mesh(barGeo, this.glowCyanMat);
        bar.position.set(xPos, 0, 0);
        this.mouthGroup.add(bar);
        this.mouthBars.push(bar);
      }

      // Floating Particle Halo / Thinking Matrix
      const particleCount = 28;
      const partGeo = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);
      for (let i = 0; i < particleCount; i++) {
        const angle = (i / particleCount) * Math.PI * 2;
        const rad = 0.65 + Math.random() * 0.15;
        positions[i * 3] = Math.cos(angle) * rad;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 0.3;
        positions[i * 3 + 2] = Math.sin(angle) * rad;
      }
      partGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const partMat = new THREE.PointsMaterial({
        color: 0x06B6D4,
        size: 0.035,
        transparent: true,
        opacity: 0.45
      });
      this.haloParticles = new THREE.Points(partGeo, partMat);
      this.haloParticles.position.set(0, 0.15, 0);
      this.headGroup.add(this.haloParticles);
    }

    setupEvents() {
      // Mouse gaze tracking
      const onMouseMove = (e) => {
        if (!this.options.enableGazeTracking || this.options.reducedMotion) return;
        const rect = this.container.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        this.mouse.targetX = ((e.clientX - cx) / (window.innerWidth / 2)) * 0.45;
        this.mouse.targetY = ((e.clientY - cy) / (window.innerHeight / 2)) * 0.35;
      };
      window.addEventListener('mousemove', onMouseMove, { passive: true });

      // Resize observer
      const onResize = () => {
        if (!this.container || !this.renderer || !this.camera) return;
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        if (w > 0 && h > 0) {
          this.camera.aspect = w / h;
          this.camera.updateProjectionMatrix();
          this.renderer.setSize(w, h);
        }
      };
      window.addEventListener('resize', onResize, { passive: true });

      // Intersection observer to pause rendering when hidden
      if ('IntersectionObserver' in window) {
        this.observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            this.isVisible = entry.isIntersecting && !document.hidden;
          });
        }, { threshold: 0.1 });
        this.observer.observe(this.container);
      }

      document.addEventListener('visibilitychange', () => {
        this.isVisible = !document.hidden;
      });
    }

    setState(newState) {
      if (this.state === newState) return;
      this.state = newState.toUpperCase();
      console.log(`[Copilot3D] Robot State: ${this.state}`);

      // Update light & material accents based on state
      if (!this.glowCyanMat) return;

      switch (this.state) {
        case 'IDLE':
          this.glowCyanMat.color.setHex(0x06B6D4);
          this.glowPurpleMat.color.setHex(0x8B5CF6);
          this.chestLight.color.setHex(0x06B6D4);
          this.haloParticles.visible = true;
          break;
        case 'LISTENING':
          this.glowCyanMat.color.setHex(0x38BDF8);
          this.chestLight.color.setHex(0x38BDF8);
          this.chestLight.intensity = 3.5;
          break;
        case 'THINKING':
          this.glowCyanMat.color.setHex(0xA855F7);
          this.glowPurpleMat.color.setHex(0xEC4899);
          this.chestLight.color.setHex(0xA855F7);
          this.chestLight.intensity = 3.2;
          this.thinkingTimer = 0;
          break;
        case 'SPEAKING':
          this.glowCyanMat.color.setHex(0x06B6D4);
          this.glowPurpleMat.color.setHex(0x38BDF8);
          this.chestLight.color.setHex(0x06B6D4);
          break;
        case 'SUCCESS':
          this.glowCyanMat.color.setHex(0x10B981); // Emerald
          this.glowPurpleMat.color.setHex(0x34D399);
          this.chestLight.color.setHex(0x10B981);
          setTimeout(() => { if (this.state === 'SUCCESS') this.setState('IDLE'); }, 2500);
          break;
        case 'ERROR':
          this.glowCyanMat.color.setHex(0xF43F5E); // Rose Red
          this.glowPurpleMat.color.setHex(0xFB7185);
          this.chestLight.color.setHex(0xF43F5E);
          setTimeout(() => { if (this.state === 'ERROR') this.setState('IDLE'); }, 3000);
          break;
      }

      // Trigger UI callback if attached
      if (typeof this.onStateChange === 'function') {
        this.onStateChange(this.state);
      }
    }

    // Connect Web Audio API to analyze speech amplitude for lip sync
    playSpeechAudio(base64AudioData, onComplete) {
      this.stopSpeech();
      this.setState('SPEAKING');

      try {
        const audio = new Audio('data:audio/mp3;base64,' + base64AudioData);
        this.currentAudioElement = audio;

        if (!this.audioContext) {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext;
          if (AudioContextClass) {
            this.audioContext = new AudioContextClass();
          }
        }

        if (this.audioContext) {
          if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
          }
          const source = this.audioContext.createMediaElementSource(audio);
          const analyser = this.audioContext.createAnalyser();
          analyser.fftSize = 64;
          analyser.smoothingTimeConstant = 0.8;
          source.connect(analyser);
          analyser.connect(this.audioContext.destination);

          this.analyser = analyser;
          this.audioSource = source;
          this.dataArray = new Uint8Array(analyser.frequencyBinCount);
        }

        audio.onended = () => {
          this.targetAudioLevel = 0;
          this.currentAudioLevel = 0;
          this.setState('IDLE');
          if (typeof onComplete === 'function') onComplete();
        };

        audio.onerror = (err) => {
          console.warn('[Copilot3D] Audio playback error:', err);
          this.setState('IDLE');
          if (typeof onComplete === 'function') onComplete();
        };

        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise.catch((err) => {
            console.warn('[Copilot3D] Autoplay prevented:', err);
            this.setState('IDLE');
            if (typeof onComplete === 'function') onComplete();
          });
        }
      } catch (err) {
        console.error('[Copilot3D] playSpeechAudio failed:', err);
        this.setState('IDLE');
        if (typeof onComplete === 'function') onComplete();
      }
    }

    stopSpeech() {
      if (this.currentAudioElement) {
        try {
          this.currentAudioElement.pause();
          this.currentAudioElement.currentTime = 0;
        } catch (e) {}
        this.currentAudioElement = null;
      }
      this.targetAudioLevel = 0;
      this.currentAudioLevel = 0;
    }

    startRenderLoop() {
      const render = () => {
        this.animId = requestAnimationFrame(render);
        if (!this.isVisible || !this.renderer || !this.scene) return;

        const delta = this.clock.getDelta();
        const time = this.clock.getElapsedTime();

        this.updateAnimation(delta, time);
        this.renderer.render(this.scene, this.camera);
      };
      render();
    }

    updateAnimation(delta, time) {
      if (this.options.reducedMotion) return;

      // Smooth mouse tracking
      this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.08;
      this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.08;

      // Audio Amplitude Sampling
      if (this.state === 'SPEAKING' && this.analyser && this.dataArray) {
        this.analyser.getByteFrequencyData(this.dataArray);
        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
          sum += this.dataArray[i];
        }
        const avg = sum / this.dataArray.length;
        this.targetAudioLevel = Math.min(avg / 128.0, 1.0);
      } else {
        this.targetAudioLevel = 0;
      }
      this.currentAudioLevel += (this.targetAudioLevel - this.currentAudioLevel) * 0.25;

      // --- STATE SPECIFIC ANIMATIONS ---
      switch (this.state) {
        case 'IDLE':
          // Organic breathing float
          this.robotGroup.position.y = -0.25 + Math.sin(time * 1.6) * 0.025;
          this.torsoGroup.rotation.x = Math.sin(time * 1.6) * 0.015;
          this.torsoGroup.rotation.z = Math.sin(time * 0.8) * 0.01;

          // Head gently looks towards user mouse cursor
          this.headGroup.rotation.y = this.mouse.x * 0.5 + Math.sin(time * 0.9) * 0.03;
          this.headGroup.rotation.x = -this.mouse.y * 0.4 + Math.sin(time * 1.6) * 0.02;

          // Mouth stays at resting line
          if (this.mouthBars) {
            this.mouthBars.forEach((bar, idx) => {
              bar.scale.y = 1.0;
            });
          }
          break;

        case 'LISTENING':
          // Attentive forward posture
          this.robotGroup.position.y = -0.23;
          this.headGroup.rotation.y = this.mouse.x * 0.8;
          this.headGroup.rotation.x = -this.mouse.y * 0.5 + 0.08;
          this.torsoGroup.rotation.x = 0.04;
          break;

        case 'THINKING':
          // Head tilted up, cognitive pondering
          this.thinkingTimer += delta * 3.5;
          this.headGroup.rotation.x = -0.12 + Math.sin(time * 2.0) * 0.02;
          this.headGroup.rotation.y = Math.sin(time * 1.5) * 0.18;

          // Scanning ocular sensor sweep
          const scanX = Math.sin(this.thinkingTimer) * 0.035;
          this.eyeLeftGroup.position.x = -0.12 + scanX;
          this.eyeRightGroup.position.x = 0.12 + scanX;

          // Rotate thinking particle halo
          if (this.haloParticles) {
            this.haloParticles.rotation.y = time * 0.9;
          }
          break;

        case 'SPEAKING':
          // Conversational head nods and subtle torso movement
          this.robotGroup.position.y = -0.25 + Math.sin(time * 3.5) * 0.015;
          this.headGroup.rotation.y = this.mouse.x * 0.45 + Math.sin(time * 4.0) * 0.03;
          this.headGroup.rotation.x = -this.mouse.y * 0.35 + Math.sin(time * 6.5) * 0.04 * (this.currentAudioLevel * 1.5 + 0.5);

          // Audio-reactive mouth aperture modulation
          if (this.mouthBars) {
            this.mouthBars.forEach((bar, idx) => {
              const centerDist = Math.abs(idx - Math.floor(this.mouthBars.length / 2));
              const falloff = 1.0 - centerDist * 0.18;
              const barScale = 1.0 + this.currentAudioLevel * 5.0 * falloff + Math.sin(time * 18 + idx) * 0.8 * this.currentAudioLevel;
              bar.scale.y = Math.max(0.6, barScale);
            });
          }

          // Reactor core beats with speech
          if (this.chestLight) {
            this.chestLight.intensity = 2.0 + this.currentAudioLevel * 2.5;
          }
          break;

        case 'SUCCESS':
          // Firm double nod
          this.headGroup.rotation.x = Math.sin(time * 8.0) * 0.08;
          break;

        case 'ERROR':
          // Side-to-side disagreement head shake
          this.headGroup.rotation.y = Math.sin(time * 9.0) * 0.12;
          break;
      }

      // Blink animation
      this.nextBlinkTime -= delta;
      if (this.nextBlinkTime <= 0 && !this.isBlinking) {
        this.isBlinking = true;
        this.blinkProgress = 0;
      }
      if (this.isBlinking) {
        this.blinkProgress += delta * 12.0;
        const blinkScale = Math.max(0.1, Math.abs(Math.sin(this.blinkProgress * Math.PI)));
        this.eyeLeftGroup.scale.y = blinkScale;
        this.eyeRightGroup.scale.y = blinkScale;
        if (this.blinkProgress >= 1.0) {
          this.isBlinking = false;
          this.eyeLeftGroup.scale.y = 1.0;
          this.eyeRightGroup.scale.y = 1.0;
          this.nextBlinkTime = 3.5 + Math.random() * 4.0;
        }
      }
    }

    // 2D Canvas Fallback if WebGL is unavailable
    init2DFallback() {
      this.container.innerHTML = `
        <div class="copilot-2d-avatar-box">
          <div class="avatar-robot-ring" id="copilot2DRing"></div>
          <div class="avatar-robot-face" id="copilot2DFace">
            <div class="avatar-eye left" id="copilot2DEyeL"></div>
            <div class="avatar-eye right" id="copilot2DEyeR"></div>
            <div class="avatar-mouth" id="copilot2DMouth">
              <span class="mouth-bar"></span>
              <span class="mouth-bar"></span>
              <span class="mouth-bar"></span>
              <span class="mouth-bar"></span>
              <span class="mouth-bar"></span>
            </div>
          </div>
          <div class="avatar-state-tag" id="copilot2DTag">AI COPILOT — READY</div>
        </div>
      `;
    }

    destroy() {
      if (this.animId) cancelAnimationFrame(this.animId);
      this.stopSpeech();
      if (this.observer) this.observer.disconnect();
      if (this.renderer) {
        this.renderer.dispose();
      }
    }
  }

  // Export to window
  window.HumanoidRobot3D = HumanoidRobot3D;

})(window);
