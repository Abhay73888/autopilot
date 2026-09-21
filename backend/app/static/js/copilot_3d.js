/**
 * copilot_3d.js — Anime-Style Humanoid AI Robot Companion Engine
 * Inspired by high-end anime character aesthetics with tailored attire,
 * expressive ruby/crimson anime eyes, layered hair, real-time Web Audio API
 * lip-sync, cursor gaze tracking, and state machine animations.
 */

(function (window) {
  'use strict';

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
        fov: 34,
        skinColor: 0xF7E3D0,
        hairColor: 0x18181B, // Jet charcoal anime hair
        coatColor: 0x09090B, // Deep black tailored coat
        suitColor: 0x1E1E24, // Charcoal inner vest
        shirtColor: 0xF8FAFC, // Crisp white high collar shirt
        tieColor: 0x0F172A, // Black necktie
        eyeGlowColor: 0xE11D48, // Crimson ruby anime eyes
        accentGlow: 0x38BDF8, // Cyber aura
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

      // Speaking cadence
      this.speechNodTimer = 0;

      this.init();
    }

    init() {
      if (!isWebGLAvailable() || typeof THREE === 'undefined') {
        console.warn('[Copilot3D] WebGL or Three.js unavailable. Falling back to 2D Anime Avatar.');
        this.init2DFallback();
        return;
      }

      try {
        this.initThreeJS();
        this.buildAnimeCharacter();
        this.setupEvents();
        this.startRenderLoop();
      } catch (err) {
        console.error('[Copilot3D] Initialization failed, using 2D fallback:', err);
        this.init2DFallback();
      }
    }

    initThreeJS() {
      this.container.innerHTML = '';
      const w = this.container.clientWidth || 380;
      const h = this.container.clientHeight || 440;

      this.scene = new THREE.Scene();
      this.clock = new THREE.Clock();

      this.camera = new THREE.PerspectiveCamera(this.options.fov, w / h, 0.1, 100);
      this.camera.position.set(0, 0.35, 3.1);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      this.renderer.setSize(w, h);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      if (this.renderer.outputColorSpace) {
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      }
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.15;

      this.container.appendChild(this.renderer.domElement);

      // Environment & Lights
      const ambientLight = new THREE.AmbientLight(0x38bdf8, 0.65);
      this.scene.add(ambientLight);

      // Key light illuminating face and suit
      this.keyLight = new THREE.DirectionalLight(0xffffff, 1.45);
      this.keyLight.position.set(1.2, 2.0, 2.5);
      this.scene.add(this.keyLight);

      // Soft fill light
      this.fillLight = new THREE.DirectionalLight(0x818cf8, 0.7);
      this.fillLight.position.set(-1.8, 0.8, 1.5);
      this.scene.add(this.fillLight);

      // Rim light for anime hair silhouette
      this.rimLight = new THREE.DirectionalLight(0xe11d48, 2.2);
      this.rimLight.position.set(0, 2.5, -2.2);
      this.scene.add(this.rimLight);

      // Floating digital dust particles
      this.initParticles();
    }

    initParticles() {
      const pCount = 65;
      const geom = new THREE.BufferGeometry();
      const pos = new Float32Array(pCount * 3);
      for (let i = 0; i < pCount; i++) {
        pos[i * 3] = (Math.random() - 0.5) * 3.5;
        pos[i * 3 + 1] = (Math.random() - 0.5) * 3.0 + 0.4;
        pos[i * 3 + 2] = (Math.random() - 0.5) * 2.5 - 0.4;
      }
      geom.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      const mat = new THREE.PointsMaterial({
        color: 0x38bdf8,
        size: 0.022,
        transparent: true,
        opacity: 0.55,
        blending: THREE.AdditiveBlending
      });
      this.particles = new THREE.Points(geom, mat);
      this.scene.add(this.particles);
    }

    buildAnimeCharacter() {
      this.characterGroup = new THREE.Group();
      this.characterGroup.position.set(0, -0.75, 0);

      // Shared Materials
      const skinMat = new THREE.MeshStandardMaterial({
        color: this.options.skinColor,
        roughness: 0.58,
        metalness: 0.04
      });

      const hairMat = new THREE.MeshStandardMaterial({
        color: this.options.hairColor,
        roughness: 0.42,
        metalness: 0.15
      });

      const coatMat = new THREE.MeshStandardMaterial({
        color: this.options.coatColor,
        roughness: 0.75,
        metalness: 0.12
      });

      const suitVestMat = new THREE.MeshStandardMaterial({
        color: this.options.suitColor,
        roughness: 0.65,
        metalness: 0.15
      });

      const shirtMat = new THREE.MeshStandardMaterial({
        color: this.options.shirtColor,
        roughness: 0.55,
        metalness: 0.05
      });

      const tieMat = new THREE.MeshStandardMaterial({
        color: this.options.tieColor,
        roughness: 0.35,
        metalness: 0.25
      });

      const rubyEyeMat = new THREE.MeshStandardMaterial({
        color: this.options.eyeGlowColor,
        emissive: 0xbe123c,
        emissiveIntensity: 0.85,
        roughness: 0.1,
        metalness: 0.2
      });

      // Platform Dais under character
      const daisGeom = new THREE.CylinderGeometry(1.2, 1.3, 0.06, 32);
      const daisMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.4,
        metalness: 0.8
      });
      const dais = new THREE.Mesh(daisGeom, daisMat);
      dais.position.y = -0.03;
      this.characterGroup.add(dais);

      const daisRingGeom = new THREE.RingGeometry(0.9, 1.15, 32);
      const daisRingMat = new THREE.MeshBasicMaterial({
        color: 0x0ea5e9,
        transparent: true,
        opacity: 0.4,
        side: THREE.DoubleSide
      });
      const daisRing = new THREE.Mesh(daisRingGeom, daisRingMat);
      daisRing.rotation.x = -Math.PI / 2;
      daisRing.position.y = 0.005;
      this.characterGroup.add(daisRing);

      // --- TORSO & WAIST ---
      this.torsoGroup = new THREE.Group();
      this.torsoGroup.position.set(0, 0.7, 0);

      // Inner Tailored Vest / Torso
      const torsoGeom = new THREE.CylinderGeometry(0.34, 0.26, 0.72, 20);
      const torsoMesh = new THREE.Mesh(torsoGeom, suitVestMat);
      torsoMesh.position.y = 0.36;
      this.torsoGroup.add(torsoMesh);

      // Crisp White Shirt Front Triangle (v-neck opening)
      const shirtBibGeom = new THREE.ConeGeometry(0.18, 0.38, 4);
      const shirtBib = new THREE.Mesh(shirtBibGeom, shirtMat);
      shirtBib.rotation.z = Math.PI;
      shirtBib.position.set(0, 0.52, 0.17);
      shirtBib.scale.set(1.0, 1.0, 0.25);
      this.torsoGroup.add(shirtBib);

      // High White Collar
      const collarLGeom = new THREE.BoxGeometry(0.04, 0.14, 0.12);
      const collarL = new THREE.Mesh(collarLGeom, shirtMat);
      collarL.position.set(-0.09, 0.70, 0.15);
      collarL.rotation.set(0, 0.35, -0.3);
      this.torsoGroup.add(collarL);

      const collarR = new THREE.Mesh(collarLGeom, shirtMat);
      collarR.position.set(0.09, 0.70, 0.15);
      collarR.rotation.set(0, -0.35, 0.3);
      this.torsoGroup.add(collarR);

      // Slim Silk Necktie
      const tieGeom = new THREE.BoxGeometry(0.052, 0.34, 0.02);
      const tieMesh = new THREE.Mesh(tieGeom, tieMat);
      tieMesh.position.set(0, 0.44, 0.20);
      tieMesh.rotation.x = -0.05;
      this.torsoGroup.add(tieMesh);

      // Glowing Cybernetic Lapel Brooch / Core
      const pinGeom = new THREE.OctahedronGeometry(0.035);
      this.lapelPinMat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x0284c7,
        emissiveIntensity: 0.9,
        roughness: 0.2
      });
      const lapelPin = new THREE.Mesh(pinGeom, this.lapelPinMat);
      lapelPin.position.set(-0.13, 0.56, 0.21);
      this.torsoGroup.add(lapelPin);

      // --- TAILORED DRAPED OVERCOAT / CAPE ---
      // Left Shoulder Pauldron / Coat draping
      const shoulderGeom = new THREE.SphereGeometry(0.18, 16, 12);
      const shoulderL = new THREE.Mesh(shoulderGeom, coatMat);
      shoulderL.position.set(-0.38, 0.64, 0.02);
      shoulderL.scale.set(1.2, 0.85, 1.05);
      this.torsoGroup.add(shoulderL);

      const shoulderR = new THREE.Mesh(shoulderGeom, coatMat);
      shoulderR.position.set(0.38, 0.64, 0.02);
      shoulderR.scale.set(1.2, 0.85, 1.05);
      this.torsoGroup.add(shoulderR);

      // Flowing Overcoat Back & Flaps
      const coatBackGeom = new THREE.CylinderGeometry(0.38, 0.48, 0.85, 16, 1, true, -Math.PI * 0.85, Math.PI * 1.7);
      const coatBack = new THREE.Mesh(coatBackGeom, coatMat);
      coatBack.position.set(0, 0.32, -0.02);
      this.torsoGroup.add(coatBack);

      // Coat Lapels
      const lapelGeom = new THREE.BoxGeometry(0.12, 0.45, 0.04);
      const lapelL = new THREE.Mesh(lapelGeom, coatMat);
      lapelL.position.set(-0.19, 0.46, 0.17);
      lapelL.rotation.set(0, 0.25, -0.15);
      this.torsoGroup.add(lapelL);

      const lapelR = new THREE.Mesh(lapelGeom, coatMat);
      lapelR.position.set(0.19, 0.46, 0.17);
      lapelR.rotation.set(0, -0.25, 0.15);
      this.torsoGroup.add(lapelR);

      // Arms in suit sleeves
      const armGeom = new THREE.CylinderGeometry(0.09, 0.08, 0.62, 14);
      this.armL = new THREE.Mesh(armGeom, coatMat);
      this.armL.position.set(-0.41, 0.28, 0.05);
      this.armL.rotation.z = 0.18;
      this.armL.rotation.x = 0.1;
      this.torsoGroup.add(this.armL);

      this.armR = new THREE.Mesh(armGeom, coatMat);
      this.armR.position.set(0.41, 0.28, 0.05);
      this.armR.rotation.z = -0.18;
      this.armR.rotation.x = 0.1;
      this.torsoGroup.add(this.armR);

      // Sculpted Hands
      const handGeom = new THREE.BoxGeometry(0.07, 0.11, 0.04);
      const handL = new THREE.Mesh(handGeom, skinMat);
      handL.position.set(-0.46, -0.08, 0.1);
      handL.rotation.z = 0.12;
      this.torsoGroup.add(handL);

      const handR = new THREE.Mesh(handGeom, skinMat);
      handR.position.set(0.46, -0.08, 0.1);
      handR.rotation.z = -0.12;
      this.torsoGroup.add(handR);

      this.characterGroup.add(this.torsoGroup);

      // --- SLENDER ANIME NECK ---
      const neckGeom = new THREE.CylinderGeometry(0.10, 0.12, 0.20, 16);
      const neck = new THREE.Mesh(neckGeom, skinMat);
      neck.position.set(0, 1.44, 0.04);
      this.characterGroup.add(neck);

      // --- ANIME HEAD & FACE ---
      this.headGroup = new THREE.Group();
      this.headGroup.position.set(0, 1.62, 0.05);

      // Cranium / Head Contour
      const headGeom = new THREE.SphereGeometry(0.24, 24, 24);
      headGeom.scale(1.0, 1.15, 1.05);
      const headMesh = new THREE.Mesh(headGeom, skinMat);
      this.headGroup.add(headMesh);

      // Refined Tapered Anime Chin / Jaw
      const chinGeom = new THREE.ConeGeometry(0.18, 0.24, 16);
      const chinMesh = new THREE.Mesh(chinGeom, skinMat);
      chinMesh.rotation.x = Math.PI;
      chinMesh.position.set(0, -0.16, 0.07);
      chinMesh.scale.set(0.85, 1.0, 0.7);
      this.headGroup.add(chinMesh);

      // Delicate Nose Bridge
      const noseGeom = new THREE.ConeGeometry(0.02, 0.05, 4);
      const nose = new THREE.Mesh(noseGeom, skinMat);
      nose.position.set(0, 0.01, 0.265);
      nose.rotation.x = -0.3;
      this.headGroup.add(nose);

      // --- EXPRESSIVE ANIME EYES ---
      this.eyesGroup = new THREE.Group();
      this.eyesGroup.position.set(0, 0.07, 0.23);

      const createAnimeEye = (isLeft) => {
        const eyeG = new THREE.Group();
        const xOffset = isLeft ? -0.095 : 0.095;
        eyeG.position.x = xOffset;

        // Eye White Sclera
        const scleraGeom = new THREE.PlaneGeometry(0.082, 0.065);
        const scleraMat = new THREE.MeshBasicMaterial({ color: 0xF8FAFC, depthWrite: false });
        const sclera = new THREE.Mesh(scleraGeom, scleraMat);
        sclera.position.z = 0.01;
        eyeG.add(sclera);

        // Glowing Ruby/Crimson Iris
        const irisGeom = new THREE.CircleGeometry(0.029, 20);
        const iris = new THREE.Mesh(irisGeom, rubyEyeMat);
        iris.position.z = 0.015;
        eyeG.add(iris);

        // Black Pupil
        const pupilGeom = new THREE.CircleGeometry(0.013, 16);
        const pupilMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
        const pupil = new THREE.Mesh(pupilGeom, pupilMat);
        pupil.position.z = 0.02;
        eyeG.add(pupil);

        // Lifelike Specular Sparkle Highlight
        const glintGeom = new THREE.CircleGeometry(0.007, 8);
        const glintMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        const glint = new THREE.Mesh(glintGeom, glintMat);
        glint.position.set(-0.009, 0.009, 0.025);
        eyeG.add(glint);

        // Upper Eyelash / Eyelid Arc
        const lashGeom = new THREE.BoxGeometry(0.092, 0.014, 0.01);
        const lashMat = new THREE.MeshBasicMaterial({ color: 0x09090b });
        const lash = new THREE.Mesh(lashGeom, lashMat);
        lash.position.set(0, 0.038, 0.028);
        lash.rotation.z = isLeft ? -0.1 : 0.1;
        eyeG.add(lash);

        // Blinking Shutter Mesh
        const eyelidGeom = new THREE.PlaneGeometry(0.095, 0.08);
        const eyelid = new THREE.Mesh(eyelidGeom, skinMat);
        eyelid.position.set(0, 0.04, 0.032);
        eyelid.scale.y = 0.001; // Open by default
        eyeG.add(eyelid);

        eyeG.eyelid = eyelid;
        eyeG.iris = iris;
        eyeG.pupil = pupil;
        eyeG.glint = glint;
        return eyeG;
      };

      this.leftEye = createAnimeEye(true);
      this.rightEye = createAnimeEye(false);
      this.eyesGroup.add(this.leftEye);
      this.eyesGroup.add(this.rightEye);

      // Sharp Anime Eyebrows
      const browGeom = new THREE.BoxGeometry(0.095, 0.012, 0.01);
      const browMat = new THREE.MeshBasicMaterial({ color: 0x18181b });
      const browL = new THREE.Mesh(browGeom, browMat);
      browL.position.set(-0.10, 0.15, 0.245);
      browL.rotation.z = -0.12;
      this.headGroup.add(browL);

      const browR = new THREE.Mesh(browGeom, browMat);
      browR.position.set(0.10, 0.15, 0.245);
      browR.rotation.z = 0.12;
      this.headGroup.add(browR);

      this.headGroup.add(this.eyesGroup);

      // --- ARTICULATED MOUTH & JAW ---
      this.mouthGroup = new THREE.Group();
      this.mouthGroup.position.set(0, -0.095, 0.245);

      // Upper lip contour
      const lipUpperGeom = new THREE.BoxGeometry(0.05, 0.007, 0.01);
      const lipMat = new THREE.MeshBasicMaterial({ color: 0x9f1239 });
      const upperLip = new THREE.Mesh(lipUpperGeom, lipMat);
      this.mouthGroup.add(upperLip);

      // Lower Jaw & Audio-Driven Speaking Aperture
      const mouthInteriorGeom = new THREE.PlaneGeometry(0.055, 0.032);
      const mouthInteriorMat = new THREE.MeshBasicMaterial({ color: 0x4c0519 });
      this.mouthInterior = new THREE.Mesh(mouthInteriorGeom, mouthInteriorMat);
      this.mouthInterior.position.set(0, -0.012, 0.002);
      this.mouthInterior.scale.set(1.0, 0.05, 1.0);
      this.mouthGroup.add(this.mouthInterior);

      const lowerLipGeom = new THREE.BoxGeometry(0.045, 0.006, 0.01);
      this.lowerLip = new THREE.Mesh(lowerLipGeom, lipMat);
      this.lowerLip.position.set(0, -0.024, 0.004);
      this.mouthGroup.add(this.lowerLip);

      this.headGroup.add(this.mouthGroup);

      // --- DETAILED LAYERED ANIME HAIR ---
      this.hairGroup = new THREE.Group();

      // Top & Crown Volume
      const hairCrownGeom = new THREE.SphereGeometry(0.26, 20, 18);
      hairCrownGeom.scale(1.05, 1.1, 1.12);
      const hairCrown = new THREE.Mesh(hairCrownGeom, hairMat);
      hairCrown.position.set(0, 0.08, -0.04);
      this.hairGroup.add(hairCrown);

      // Cascading Side Locks (Framing Face)
      const lockGeom = new THREE.ConeGeometry(0.06, 0.38, 8);
      const lockL1 = new THREE.Mesh(lockGeom, hairMat);
      lockL1.position.set(-0.21, -0.05, 0.14);
      lockL1.rotation.set(0.2, 0, 0.25);
      this.hairGroup.add(lockL1);

      const lockR1 = new THREE.Mesh(lockGeom, hairMat);
      lockR1.position.set(0.21, -0.05, 0.14);
      lockR1.rotation.set(0.2, 0, -0.25);
      this.hairGroup.add(lockR1);

      // Wavy Forehead Bangs (styled fringe)
      const bangGeom = new THREE.ConeGeometry(0.048, 0.26, 7);
      const bang1 = new THREE.Mesh(bangGeom, hairMat);
      bang1.position.set(-0.06, 0.16, 0.23);
      bang1.rotation.set(0.35, 0.2, 0.35);
      this.hairGroup.add(bang1);

      const bang2 = new THREE.Mesh(bangGeom, hairMat);
      bang2.position.set(0.04, 0.17, 0.24);
      bang2.rotation.set(0.32, -0.15, -0.22);
      this.hairGroup.add(bang2);

      const bang3 = new THREE.Mesh(bangGeom, hairMat);
      bang3.position.set(0.12, 0.14, 0.22);
      bang3.rotation.set(0.4, -0.3, -0.45);
      this.hairGroup.add(bang3);

      // Flowing Back Hair Layers
      const backHairGeom = new THREE.CylinderGeometry(0.24, 0.29, 0.42, 16);
      const backHair = new THREE.Mesh(backHairGeom, hairMat);
      backHair.position.set(0, -0.12, -0.14);
      backHair.rotation.x = -0.15;
      this.hairGroup.add(backHair);

      this.headGroup.add(this.hairGroup);

      // Holographic Particle Ring (Thinking Aura)
      const ringGeom = new THREE.TorusGeometry(0.38, 0.012, 12, 36);
      this.thinkingRingMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.0,
        blending: THREE.AdditiveBlending
      });
      this.thinkingRing = new THREE.Mesh(ringGeom, this.thinkingRingMat);
      this.thinkingRing.rotation.x = Math.PI / 2;
      this.thinkingRing.position.set(0, 0.25, 0);
      this.headGroup.add(this.thinkingRing);

      this.characterGroup.add(this.headGroup);
      this.scene.add(this.characterGroup);
    }

    setupEvents() {
      // Mouse move / gaze tracking
      this.onMouseMove = (e) => {
        const rect = this.container.getBoundingClientRect();
        this.mouse.targetX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.targetY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      };
      window.addEventListener('mousemove', this.onMouseMove, { passive: true });

      // Resize
      this.onResize = () => {
        if (!this.renderer || !this.camera || !this.container) return;
        const w = this.container.clientWidth || 380;
        const h = this.container.clientHeight || 440;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
      };
      window.addEventListener('resize', this.onResize);

      // Intersection observer for performance
      if ('IntersectionObserver' in window) {
        this.observer = new IntersectionObserver((entries) => {
          this.isVisible = entries[0].isIntersecting;
        }, { threshold: 0.1 });
        this.observer.observe(this.container);
      }
    }

    setState(newState) {
      this.state = newState;
      const badge = document.getElementById('robotStatusText');
      const pill = document.getElementById('robotStatusBadge');

      if (badge) {
        badge.innerText = `ANIME COPILOT — ${this.state}`;
      }

      if (pill) {
        pill.classList.remove('status-thinking', 'status-speaking', 'status-error');
        if (this.state === 'THINKING') pill.classList.add('status-thinking');
        if (this.state === 'SPEAKING') pill.classList.add('status-speaking');
        if (this.state === 'ERROR') pill.classList.add('status-error');
      }

      // Update light & shader moods
      if (this.lapelPinMat) {
        if (this.state === 'THINKING') {
          this.lapelPinMat.color.setHex(0xf59e0b); // Amber
          this.lapelPinMat.emissive.setHex(0xd97706);
          if (this.thinkingRingMat) this.thinkingRingMat.opacity = 0.85;
        } else if (this.state === 'SPEAKING') {
          this.lapelPinMat.color.setHex(0xe11d48); // Ruby Rose
          this.lapelPinMat.emissive.setHex(0xbe123c);
          if (this.thinkingRingMat) this.thinkingRingMat.opacity = 0.25;
        } else if (this.state === 'SUCCESS') {
          this.lapelPinMat.color.setHex(0x10b981); // Emerald
          this.lapelPinMat.emissive.setHex(0x059669);
          if (this.thinkingRingMat) this.thinkingRingMat.opacity = 0.0;
        } else if (this.state === 'ERROR') {
          this.lapelPinMat.color.setHex(0xef4444); // Crimson
          this.lapelPinMat.emissive.setHex(0xb91c1c);
          if (this.thinkingRingMat) this.thinkingRingMat.opacity = 0.0;
        } else {
          this.lapelPinMat.color.setHex(0x38bdf8); // Cyan
          this.lapelPinMat.emissive.setHex(0x0284c7);
          if (this.thinkingRingMat) this.thinkingRingMat.opacity = 0.0;
        }
      }
    }

    playSpeechAudio(base64Mp3, onComplete) {
      try {
        this.stopSpeechAudio();

        if (!this.audioContext) {
          const AudioCtx = window.AudioContext || window.webkitAudioContext;
          this.audioContext = new AudioCtx();
        }
        if (this.audioContext.state === 'suspended') {
          this.audioContext.resume();
        }

        const audio = new Audio('data:audio/mp3;base64,' + base64Mp3);
        this.currentAudioElement = audio;

        if (!this.analyser) {
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 64;
          this.analyser.smoothingTimeConstant = 0.65;
        }

        try {
          const source = this.audioContext.createMediaElementSource(audio);
          source.connect(this.analyser);
          this.analyser.connect(this.audioContext.destination);
          this.audioSource = source;
        } catch (e) {
          // Fallback if cross-origin or already connected
        }

        this.setState('SPEAKING');

        audio.onended = () => {
          this.stopSpeechAudio();
          this.setState('IDLE');
          if (typeof onComplete === 'function') onComplete();
        };

        audio.onerror = () => {
          this.stopSpeechAudio();
          this.setState('IDLE');
          if (typeof onComplete === 'function') onComplete();
        };

        audio.play().catch(() => {
          this.setState('IDLE');
        });

      } catch (err) {
        console.warn('[Copilot3D] Audio playback error:', err);
        this.setState('IDLE');
        if (typeof onComplete === 'function') onComplete();
      }
    }

    stopSpeechAudio() {
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
      const freqData = new Uint8Array(32);

      const render = () => {
        this.animId = requestAnimationFrame(render);
        if (!this.isVisible || !this.renderer || !this.scene || !this.camera) return;

        const delta = this.clock.getDelta();
        const time = this.clock.getElapsedTime();

        // 1. Audio amplitude extraction
        if (this.analyser && this.state === 'SPEAKING') {
          this.analyser.getByteFrequencyData(freqData);
          let sum = 0;
          for (let i = 0; i < 16; i++) {
            sum += freqData[i];
          }
          const avg = sum / 16;
          this.targetAudioLevel = Math.min(1.0, (avg / 128.0));
        } else {
          this.targetAudioLevel = 0;
        }

        this.currentAudioLevel += (this.targetAudioLevel - this.currentAudioLevel) * 0.35;

        // 2. Mouse gaze tracking interpolation
        this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
        this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

        if (this.headGroup && this.options.enableGazeTracking) {
          const targetRotY = this.mouse.x * 0.32;
          const targetRotX = -this.mouse.y * 0.22;
          this.headGroup.rotation.y = targetRotY;
          this.headGroup.rotation.x = targetRotX;
        }

        // 3. Torso breathing animation
        if (this.torsoGroup) {
          const breath = Math.sin(time * 1.8) * 0.008;
          this.torsoGroup.position.y = 0.7 + breath;
          this.torsoGroup.rotation.y = this.mouse.x * 0.08;
        }

        // 4. Natural Blinking Animation
        if (time > this.nextBlinkTime) {
          this.isBlinking = true;
          this.blinkProgress = 0;
          this.nextBlinkTime = time + 3.0 + Math.random() * 2.8;
        }

        if (this.isBlinking) {
          this.blinkProgress += delta * 9.5;
          const blinkScale = Math.sin(Math.min(Math.PI, this.blinkProgress));
          if (this.leftEye && this.leftEye.eyelid) {
            this.leftEye.eyelid.scale.y = Math.max(0.001, blinkScale * 1.05);
          }
          if (this.rightEye && this.rightEye.eyelid) {
            this.rightEye.eyelid.scale.y = Math.max(0.001, blinkScale * 1.05);
          }
          if (this.blinkProgress >= Math.PI) {
            this.isBlinking = false;
            if (this.leftEye && this.leftEye.eyelid) this.leftEye.eyelid.scale.y = 0.001;
            if (this.rightEye && this.rightEye.eyelid) this.rightEye.eyelid.scale.y = 0.001;
          }
        }

        // 5. Lip-Sync & Jaw Articulation
        if (this.mouthInterior && this.lowerLip) {
          const amp = this.currentAudioLevel;
          // Scale mouth aperture
          this.mouthInterior.scale.y = Math.max(0.05, amp * 1.25);
          this.mouthInterior.scale.x = 1.0 + amp * 0.3;
          this.lowerLip.position.y = -0.024 - amp * 0.038;
        }

        // 6. Speaking Head Nods
        if (this.state === 'SPEAKING' && this.headGroup) {
          this.speechNodTimer += delta * 6.0;
          const nod = Math.sin(this.speechNodTimer) * 0.035 * this.currentAudioLevel;
          this.headGroup.rotation.x += nod;
          this.headGroup.rotation.z = Math.sin(this.speechNodTimer * 0.5) * 0.02;
        }

        // 7. Thinking Halo Spin
        if (this.thinkingRing && this.state === 'THINKING') {
          this.thinkingRing.rotation.z += delta * 4.2;
        }

        // 8. Background digital particles drift
        if (this.particles) {
          const pPos = this.particles.geometry.attributes.position.array;
          for (let i = 1; i < pPos.length; i += 3) {
            pPos[i] += delta * 0.12;
            if (pPos[i] > 2.2) pPos[i] = -0.8;
          }
          this.particles.geometry.attributes.position.needsUpdate = true;
        }

        this.renderer.render(this.scene, this.camera);
      };

      render();
    }

    init2DFallback() {
      this.container.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 24px; text-align: center;">
          <div style="position: relative; width: 140px; height: 140px; border-radius: 50%; background: radial-gradient(circle, #1e1b4b 0%, #030712 100%); border: 2px solid #e11d48; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 25px rgba(225, 29, 72, 0.45); margin-bottom: 16px;">
            <span style="font-size: 64px;">🥷</span>
            <div id="fallbackEyeGlow" style="position: absolute; width: 100%; height: 100%; border-radius: 50%; border: 2px solid #38bdf8; animation: pulseGlow 2s infinite;"></div>
          </div>
          <h3 style="font-family: var(--font-display); font-size: 18px; color: #fff; margin: 0 0 4px;">Anime AI Companion</h3>
          <p style="color: var(--text-muted); font-size: 12px; max-width: 260px;">2D Cybernetic Engine active. All voice, reasoning, and actions are 100% operational.</p>
        </div>
      `;
    }

    destroy() {
      if (this.animId) cancelAnimationFrame(this.animId);
      if (this.onMouseMove) window.removeEventListener('mousemove', this.onMouseMove);
      if (this.onResize) window.removeEventListener('resize', this.onResize);
      if (this.observer) this.observer.disconnect();
      this.stopSpeechAudio();
      if (this.renderer && this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    }
  }

  // Expose globally
  window.HumanoidRobot3D = HumanoidRobot3D;

})(window);
