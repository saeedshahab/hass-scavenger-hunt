console.info("%c SCAVENGER HUNT CARD %c Loaded ", "color: white; background: #2f3542; font-weight: 700;", "color: #2f3542; background: white; font-weight: 700;");

class WebAudioEngine {
  constructor() {
    this.context = null;
    this.enabled = false;
    this.musicGain = null;
    this.musicInterval = null;
    this.volume = 0.3;
    this.musicEnabled = false;
  }

  init() {
    if (this.context) return;
    this.context = new (window.AudioContext || window.webkitAudioContext)();
    this.musicGain = this.context.createGain();
    this.musicGain.connect(this.context.destination);
    this.musicGain.gain.setValueAtTime(0, this.context.currentTime);
  }

  toggle() {
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.init();
      if (this.musicEnabled) this.startBackgroundMusic();
    } else {
      this.stopBackgroundMusic();
    }
    return this.enabled;
  }

  toggleMusic() {
    this.musicEnabled = !this.musicEnabled;
    if (this.musicEnabled && this.enabled) {
      this.startBackgroundMusic();
    } else {
      this.stopBackgroundMusic();
    }
    return this.musicEnabled;
  }

  setVolume(v) {
    this.volume = v;
    if (this.musicGain) {
      this.musicGain.gain.setTargetAtTime(this.musicEnabled ? v : 0, this.context.currentTime, 0.1);
    }
  }

  startBackgroundMusic() {
    if (!this.context || this.musicInterval) return;
    
    this.musicGain.gain.setTargetAtTime(this.volume, this.context.currentTime, 0.5);
    
    let step = 0;
    const playStep = () => {
      if (!this.musicEnabled || !this.enabled) return;
      
      const time = this.context.currentTime;
      const osc = this.context.createOscillator();
      const g = this.context.createGain();
      
      // Enthusiastic pulsing beat
      if (step % 4 === 0) {
        // Kick-ish sound
        osc.frequency.setValueAtTime(150, time);
        osc.frequency.exponentialRampToValueAtTime(40, time + 0.1);
        g.gain.setValueAtTime(0.1, time);
        g.gain.exponentialRampToValueAtTime(0.001, time + 0.2);
      } else {
        // Soft pulse
        osc.frequency.setValueAtTime(440, time);
        g.gain.setValueAtTime(0.02, time);
        g.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
      }
      
      osc.connect(g);
      g.connect(this.musicGain);
      osc.start(time);
      osc.stop(time + 0.2);
      
      step++;
      this.musicInterval = setTimeout(playStep, 500); // 120 BPM pulse
    };
    
    playStep();
  }

  stopBackgroundMusic() {
    if (this.musicInterval) {
      clearTimeout(this.musicInterval);
      this.musicInterval = null;
    }
    if (this.musicGain) {
      this.musicGain.gain.setTargetAtTime(0, this.context.currentTime, 0.5);
    }
  }

  playSuccess() {
    if (!this.enabled || !this.context) return;
    const osc = this.context.createOscillator();
    const gain = this.context.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, this.context.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1320, this.context.currentTime + 0.1);
    gain.gain.setValueAtTime(this.volume, this.context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.context.currentTime + 0.3);
    osc.connect(gain);
    gain.connect(this.context.destination);
    osc.start();
    osc.stop(this.context.currentTime + 0.3);
  }

  playError() {
    if (!this.enabled || !this.context) return;
    const osc = this.context.createOscillator();
    const gain = this.context.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(150, this.context.currentTime);
    osc.frequency.exponentialRampToValueAtTime(100, this.context.currentTime + 0.2);
    gain.gain.setValueAtTime(this.volume * 0.5, this.context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.context.currentTime + 0.4);
    osc.connect(gain);
    gain.connect(this.context.destination);
    osc.start();
    osc.stop(this.context.currentTime + 0.4);
  }

  playVictory() {
    if (!this.enabled || !this.context) return;
    const now = this.context.currentTime;
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    notes.forEach((freq, i) => {
      const osc = this.context.createOscillator();
      const gain = this.context.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, now + (i * 0.1));
      gain.gain.setValueAtTime(0.05, now + (i * 0.1));
      gain.gain.exponentialRampToValueAtTime(0.01, now + (i * 0.1) + 0.5);
      osc.connect(gain);
      gain.connect(this.context.destination);
      osc.start(now + (i * 0.1));
      osc.stop(now + (i * 0.1) + 0.5);
    });
  }
}

const audio = new WebAudioEngine();

const DEFAULT_LOGO_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"></circle>
  <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
</svg>
`;




class ScavengerHuntCard extends HTMLElement {
  constructor() {
    super();
    this.audio = new WebAudioEngine();
    this._gameStarted = false;
    this._lastScore = 0;
  }

  _startHunt() {
    this._gameStarted = true;
    this.audio.init(); 
    this.requestUpdate();
  }

  requestUpdate() {
    this.hass = this._hass;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.innerHTML = `
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800&family=Lora:ital,wght@1,400;1,700&family=Playfair+Display:wght@700&display=swap');
          
          :host {
            --shc-bg: #e7dcc9;
            --shc-text: #333333;
            --shc-accent-sage: #c1d6cb;
            --shc-accent-lavender: #c9b0dc;
            --shc-accent-rose: #e18e9e;
            --shc-border: rgba(51, 51, 51, 0.1);
            --shc-font-header: 'Montserrat', sans-serif;
            --shc-font-body: 'Lora', serif;
            display: block;
            padding: 0;
          }

          .shc-card {
            background: var(--shc-bg);
            color: var(--shc-text);
            padding: 48px;
            width: 100%;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            font-family: var(--shc-font-body);
            position: relative;
            box-sizing: border-box;
            text-align: center;
          }

          .shc-brand-wrapper {
            margin-bottom: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
          }

          .shc-logo-wrapper {
            width: 350px;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            margin-bottom: 10px;
          }

          .shc-logo-wrapper svg {
            width: 100%;
            height: auto;
          }

          .shc-title {
            font-family: var(--shc-font-header);
            font-size: 5rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 15px;
            margin: 0;
            color: var(--shc-text);
          }

          .shc-score-container {
            font-family: var(--shc-font-header);
            font-size: 10rem;
            font-weight: 700;
            margin: 20px 0;
            color: var(--shc-text);
            line-height: 1;
          }

          .shc-tag-info {
            font-family: var(--shc-font-body);
            font-style: italic;
            font-size: 1.6rem;
            margin-top: 10px;
            opacity: 0.8;
          }

          .shc-progress-wrapper {
            width: 50%;
            height: 2px;
            background: rgba(51, 51, 51, 0.1);
            margin: 48px 0;
            position: relative;
            display: none;
          }

          .shc-progress-bar {
            height: 100%;
            background: var(--shc-accent-sage);
            transition: width 1s ease-in-out;
          }

          .shc-lifeline {
            margin-top: 32px;
            padding: 14px 40px;
            background: white;
            border: 1px solid var(--shc-border);
            color: var(--shc-text);
            font-family: var(--shc-font-header);
            font-weight: 700;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            display: none;
            cursor: pointer;
            transition: all 0.3s;
          }

          .shc-lifeline:hover {
            background: var(--shc-accent-lavender);
            border-color: transparent;
          }

          .shc-bypass-ui {
            display: none;
            margin-top: 24px;
            gap: 16px;
            align-items: center;
          }

          .shc-input {
            background: white;
            border: 1px solid var(--shc-border);
            padding: 12px;
            font-size: 1.2rem;
            width: 100px;
            text-align: center;
            font-family: var(--shc-font-header);
          }

          .shc-guess-btn {
            background: var(--shc-text);
            color: white;
            border: none;
            padding: 12px 32px;
            font-family: var(--shc-font-header);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
          }

          .shc-verify-btn {
            margin-top: 48px;
            background: transparent;
            border: 1px solid var(--shc-text);
            color: var(--shc-text);
            padding: 16px 48px;
            font-family: var(--shc-font-header);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 3px;
            cursor: pointer;
            transition: all 0.3s;
          }

          .shc-verify-btn:hover {
            background: var(--shc-text);
            color: white;
          }

          .shc-completed {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--shc-accent-sage);
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10;
            animation: fadeIn 0.8s ease-out;
          }

          .shc-completed h1 {
            font-family: var(--shc-font-header);
            font-size: 6rem;
            letter-spacing: 20px;
            margin: 0;
            text-transform: uppercase;
            font-weight: 800;
          }

          .shc-controls {
            position: absolute;
            top: 15px;
            right: 15px;
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 10;
          }

          .shc-control-item {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--shc-text);
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            transition: all 0.3s ease;
          }

          .shc-control-item:hover {
            background: rgba(255, 255, 255, 0.4);
          }

          .shc-volume-container {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            height: 40px;
          }

          .shc-volume-slider {
            width: 80px;
            height: 4px;
            -webkit-appearance: none;
            background: var(--shc-border);
            outline: none;
            border-radius: 2px;
          }

          .shc-volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: var(--shc-text);
            border-radius: 50%;
            cursor: pointer;
          }

          @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }

          .shc-shake {
            animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
          }
          @keyframes shake {
            10%, 90% { transform: translate3d(-1px, 0, 0); }
            20%, 80% { transform: translate3d(2px, 0, 0); }
            30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
            40%, 60% { transform: translate3d(4px, 0, 0); }
          }
          .shc-start-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
          }

          .shc-instructions {
            text-align: left;
            margin: 30px 0;
            padding: 0;
            list-style: none;
            font-size: 1.1rem;
            line-height: 1.8;
          }

          .shc-instructions li {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
          }

          .shc-instructions li::before {
            content: "•";
            color: var(--shc-accent-rose);
            font-weight: bold;
            margin-right: 15px;
            font-size: 1.5rem;
            line-height: 1;
          }

          .shc-start-btn {
            background: var(--shc-text);
            color: var(--shc-bg);
            border: none;
            padding: 15px 40px;
            font-family: var(--shc-font-header);
            font-weight: 700;
            letter-spacing: 2px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            font-size: 0.9rem;
          }

          .shc-start-btn:hover {
            opacity: 0.9;
            transform: translateY(-2px);
          }
        </style>
        <div class="shc-card">
          <div class="shc-controls">
            <div class="shc-volume-container">
              <ha-icon icon="mdi:volume-medium" style="font-size: 18px;"></ha-icon>
              <input type="range" class="shc-volume-slider" id="volume-slider" min="0" max="1" step="0.1" value="0.3">
            </div>
            <div class="shc-control-item" id="music-btn" title="Toggle Music">
              <ha-icon icon="mdi:music-off"></ha-icon>
            </div>
            <div class="shc-control-item" id="sound-btn" title="Toggle Sound Effects">
              <ha-icon icon="mdi:volume-off"></ha-icon>
            </div>
          </div>
          
          <div class="shc-brand-wrapper">
            <div class="shc-logo-wrapper">${this._logoHtml}</div>
            <h1 class="shc-title">${this._title}</h1>
          </div>

          <!-- Start Screen -->
          <div id="start-screen" class="shc-start-screen">
            <ul class="shc-instructions">
              <li>Find hidden tags throughout the house.</li>
              <li>Scan them with your phone to collect items.</li>
              <li>Use lifelines if you need a hint.</li>
              <li>Unlock the collection once finished!</li>
            </ul>
            <button class="shc-start-btn" id="start-btn">Start Hunt</button>
          </div>

          <!-- Game UI -->
          <div id="game-ui" style="display: none;">
            <div class="shc-score-container" id="score">0</div>
            <div class="shc-tag-info" id="last-tag">Scan a tag to begin!</div>

            <div class="shc-progress-wrapper" id="progress-wrapper">
              <div class="shc-progress-bar" id="progress-bar"></div>
            </div>

            <div class="shc-lifeline" id="lifeline"></div>
            
            <div class="shc-bypass-ui" id="bypass-ui">
              <input type="number" class="shc-input" id="guess-input" placeholder="0">
              <button class="shc-guess-btn" id="guess-btn">Submit Guess</button>
            </div>
            
            <button class="shc-verify-btn" id="verify-btn">Unlock Gifts</button>
          </div>

          <!-- Victory Screen -->
          <div class="shc-completed" id="completed-screen" style="display: none;">
            <h1 style="font-family: var(--shc-font-header); font-size: 1.2rem; letter-spacing: 4px; margin-bottom: 60px; font-weight: 400;">SUCCESS</h1>
            <div class="shc-logo-wrapper" style="width: 280px; margin-bottom: 20px;">${this._logoHtml}</div>
            <div style="font-family: var(--shc-font-header); font-size: 2.5rem; font-weight: 800; letter-spacing: 6px; border-top: 1.5px solid var(--shc-text); border-bottom: 1.5px solid var(--shc-text); padding: 15px 0; width: 85%; margin: 10px 0;">${this._completedTitle}</div>
            <p style="font-size: 1.4rem; margin-top: 40px; font-style: italic; opacity: 0.8;">on your way</p>
          </div>
        </div>
      `;
      this.content = this.querySelector('.shc-card');

      this.querySelector('#start-btn').addEventListener('click', () => {
        this._gameStarted = true;
        this.audio.init();
        this.querySelector('#start-screen').style.display = 'none';
        this.querySelector('#game-ui').style.display = 'block';
      });

      this.querySelector('#verify-btn').addEventListener('click', () => {
        this._hass.callService("interactive_scavenger_hunt", "verify_completion", {});
      });

      this.querySelector('#lifeline').addEventListener('click', () => {
        const activeLifelines = this._lastLifelines || [];
        if (activeLifelines.length > 0) {
          const service = activeLifelines[0];
          if (service !== "guess_bypass") {
            this._hass.callService("interactive_scavenger_hunt", service, {});
          }
        }
      });

      this.querySelector('#guess-btn').addEventListener('click', () => {
        const guess = parseInt(this.querySelector('#guess-input').value, 10);
        if (guess) {
          this._hass.callService("interactive_scavenger_hunt", "guess_bypass", { guess });
        }
      });

      this.querySelector('#sound-btn').addEventListener('click', () => {
        const isEnabled = this.audio.toggle();
        const icon = this.querySelector('#sound-btn ha-icon');
        icon.setAttribute('icon', isEnabled ? 'mdi:volume-high' : 'mdi:volume-off');
      });

      this.querySelector('#music-btn').addEventListener('click', () => {
        const isEnabled = this.audio.toggleMusic();
        const icon = this.querySelector('#music-btn ha-icon');
        icon.setAttribute('icon', isEnabled ? 'mdi:music' : 'mdi:music-off');
      });

      this.querySelector('#volume-slider').addEventListener('input', (e) => {
        this.audio.setVolume(parseFloat(e.target.value));
      });
    }

    const sensorEntityId = this.config.entity || "sensor.scavenger_hunt_score";
    const binarySensorId = "binary_sensor.scavenger_hunt_completion";

    const scoreState = hass.states[sensorEntityId];
    const completionState = hass.states[binarySensorId];

    if (scoreState) {
      let score = parseInt(scoreState.state, 10);
      if (isNaN(score)) {
        score = 0;
      }
      const attrs = scoreState.attributes;
      let total = parseInt(attrs.total_tags, 10);
      if (isNaN(total) || total <= 0) {
        total = 20;
      }
      const revealed = attrs.revealed_total || false;
      const lastTag = attrs.last_tag || "Keep searching...";

      const scoreEl = this.querySelector('#score');
      const progressWrapperEl = this.querySelector('#progress-wrapper');
      const progressBarEl = this.querySelector('#progress-bar');
      const lastTagEl = this.querySelector('#last-tag');
      const lifelineEl = this.querySelector('#lifeline');

      // Update UI visibility based on game state
      // If score transitions from >0 to 0, it means a reset happened, so show instructions
      if (this._lastScore > 0 && score === 0) {
        this._gameStarted = false;
      }
      // If score is > 0, we are definitely playing
      if (score > 0) {
        this._gameStarted = true;
      }
      this._lastScore = score;

      if (this._gameStarted) {
        this.querySelector('#start-screen').style.display = 'none';
        this.querySelector('#game-ui').style.display = 'block';
      } else {
        this.querySelector('#start-screen').style.display = 'flex';
        this.querySelector('#game-ui').style.display = 'none';
      }

      // Update Score Display
      if (revealed) {
        scoreEl.innerText = `${score} / ${total}`;
        progressWrapperEl.style.display = 'block';
        const percent = Math.min(100, Math.max(0, (score / total) * 100));
        progressBarEl.style.width = `${percent}%`;
      } else {
        scoreEl.innerText = `${score}`;
        progressWrapperEl.style.display = 'none';
      }

      // Update Last Tag
      lastTagEl.innerText = lastTag ? `Found: ${lastTag}` : "Scan a tag to begin!";

      // Update Lifelines
      const activeLifelines = attrs.lifelines_available || [];
      this._lastLifelines = activeLifelines;
      
      const bypassUiEl = this.querySelector('#bypass-ui');

      if (activeLifelines.length > 0) {
        const service = activeLifelines[0];
        const name = service.replace(/_/g, ' ');
        lifelineEl.innerText = `Lifeline Active: ${name}`;
        lifelineEl.style.display = 'block';
        
        // Show/hide bypass UI
        if (service === "guess_bypass") {
          bypassUiEl.style.display = 'flex';
        } else {
          bypassUiEl.style.display = 'none';
        }
      } else {
        lifelineEl.style.display = 'none';
        bypassUiEl.style.display = 'none';
      }

      // Feedback for failed verification
      const verifyFailed = attrs.last_verify_failed;
      if (verifyFailed && verifyFailed !== this._lastVerifyFailed) {
        this._lastVerifyFailed = verifyFailed;
        this.content.classList.add('shc-shake');
        setTimeout(() => this.content.classList.remove('shc-shake'), 600);
      }

      // Sound Engine Logic
      const soundEvent = attrs.last_sound_event;
      if (soundEvent && soundEvent.timestamp !== this._lastSoundTimestamp) {
        this._lastSoundTimestamp = soundEvent.timestamp;
        if (soundEvent.type === 'success') this.audio.playSuccess();
        if (soundEvent.type === 'error') this.audio.playError();
        if (soundEvent.type === 'victory') this.audio.playVictory();
      }
    }

    // Update Completion Screen
    if (completionState) {
      const completedScreen = this.querySelector('#completed-screen');
      const brandWrapper = this.querySelector('.shc-brand-wrapper');
      const startScreen = this.querySelector('#start-screen');
      const gameUi = this.querySelector('#game-ui');
      const soundBtn = this.querySelector('#sound-btn');

      if (completionState.state === 'on') {
        completedScreen.style.display = 'flex';
        brandWrapper.style.display = 'none';
        startScreen.style.display = 'none';
        gameUi.style.display = 'none';
        soundBtn.style.display = 'none';
      } else {
        completedScreen.style.display = 'none';
        brandWrapper.style.display = 'flex';
        soundBtn.style.display = 'flex';
        // startScreen/gameUi visibility handled by score check above
      }
    }
  }

  setConfig(config) {
    this.config = config;
    this._title = config.title || "SCAVENGE";
    this._completedTitle = config.completed_title || "PREMIERE COLLECTION";
    
    // Determine logo
    if (config.logo_path) {
      this._logoHtml = `<img src="${config.logo_path}" style="max-width: 100%; max-height: 100%; object-fit: contain;">`;
    } else if (config.logo_svg) {
      this._logoHtml = config.logo_svg;
    } else {
      // Default to generic logo if no config
      this._logoHtml = DEFAULT_LOGO_SVG;
    }
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('scavenger-hunt-card', ScavengerHuntCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "scavenger-hunt-card",
  name: "Scavenger Hunt Dashboard",
  preview: true,
  description: "A beautiful interactive dashboard for scavenger hunts"
});
