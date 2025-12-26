"""UI routes for the HAL brain web app."""

from __future__ import annotations

from flask import Blueprint, render_template_string

ui_bp = Blueprint("ui", __name__)

_PAGE = """
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>HAL 9000 — Interface Immersive</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #050509;
        --panel: rgba(20, 20, 28, 0.92);
        --panel-border: #2a2a38;
        --accent: #e63946;
        --accent-soft: rgba(230, 57, 70, 0.25);
        --text: #f3f3f7;
        --muted: #9d9db0;
        --glow: 0 0 24px rgba(230, 57, 70, 0.35);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "JetBrains Mono", "SFMono-Regular", "Segoe UI", sans-serif;
        background: radial-gradient(circle at top, #16161f 0%, #050509 55%, #030305 100%);
        color: var(--text);
        min-height: 100vh;
        display: flex;
        flex-direction: column;
      }
      header {
        padding: 24px;
        border-bottom: 1px solid var(--panel-border);
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        align-items: center;
        justify-content: space-between;
        background: rgba(6, 6, 10, 0.8);
        backdrop-filter: blur(6px);
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 16px;
      }
      .halo {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: var(--glow);
        position: relative;
      }
      .halo::after {
        content: "";
        position: absolute;
        inset: 6px;
        border-radius: 50%;
        background: #0b0b12;
        border: 1px solid rgba(255, 255, 255, 0.2);
      }
      header h1 {
        margin: 0;
        font-size: 20px;
        letter-spacing: 0.3em;
        text-transform: uppercase;
      }
      header p {
        margin: 4px 0 0;
        color: var(--muted);
        font-size: 12px;
      }
      nav {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      nav button {
        background: transparent;
        border: 1px solid var(--panel-border);
        color: var(--text);
        padding: 8px 14px;
        border-radius: 999px;
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 12px;
      }
      nav button.active {
        background: var(--accent);
        border-color: var(--accent);
        color: #111;
      }
      main {
        padding: 24px;
        display: grid;
        gap: 20px;
        flex: 1;
      }
      .panel {
        background: var(--panel);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      }
      .panel h2 {
        margin: 0 0 12px;
        font-size: 14px;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: var(--accent);
      }
      .hidden { display: none; }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      .status-card {
        background: rgba(9, 9, 14, 0.7);
        border: 1px solid #242436;
        border-radius: 12px;
        padding: 12px;
      }
      .status-card h3 {
        margin: 0 0 8px;
        font-size: 12px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.12em;
      }
      .pill {
        display: inline-flex;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: #2b2b3a;
      }
      .status-ok { background: rgba(70, 170, 90, 0.2); color: #9ce6b0; }
      .status-warn { background: rgba(255, 184, 77, 0.2); color: #ffd49c; }
      .status-error { background: rgba(230, 57, 70, 0.25); color: #ff9aa4; }
      .muted { color: var(--muted); }
      .thought-display {
        min-height: 120px;
        font-size: 16px;
        line-height: 1.7;
        letter-spacing: 0.05em;
      }
      .meta {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-top: 16px;
        font-size: 12px;
      }
      .meta span {
        display: block;
        color: var(--muted);
      }
      .thinking {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--accent);
        font-size: 12px;
        letter-spacing: 0.2em;
        text-transform: uppercase;
      }
      .thinking .dots::after {
        content: "...";
        animation: blink 1.6s infinite;
      }
      @keyframes blink {
        0% { opacity: 0.2; }
        50% { opacity: 1; }
        100% { opacity: 0.2; }
      }
      pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 12px;
        line-height: 1.6;
      }
      .list {
        display: grid;
        gap: 10px;
        font-size: 13px;
      }
      .list-item {
        border-left: 2px solid var(--accent);
        padding-left: 10px;
      }
      .controls {
        display: grid;
        gap: 16px;
      }
      .control {
        display: grid;
        gap: 6px;
      }
      .control input[type="range"] {
        width: 100%;
      }
      .control label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
      }
      .toggle {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .toggle input {
        width: 18px;
        height: 18px;
      }
      .footer-note {
        margin-top: 8px;
        font-size: 11px;
        color: var(--muted);
      }
      @media (max-width: 720px) {
        header { flex-direction: column; align-items: flex-start; }
      }
    </style>
  </head>
  <body>
    <header>
      <div class="brand">
        <div class="halo" aria-hidden="true"></div>
        <div>
          <h1>HAL 9000</h1>
          <p>Interface immersive unifiée — Nostromo / HAL</p>
        </div>
      </div>
      <nav>
        <button data-tab="statut" class="active">Statut</button>
        <button data-tab="pensees">Pensées</button>
        <button data-tab="donnees">Données</button>
        <button data-tab="audio">Audio</button>
        <button data-tab="reglages">Réglages</button>
        <button data-tab="journal">Journal</button>
      </nav>
    </header>

    <main>
      <section id="statut" class="panel">
        <h2>STATUT OPÉRATIONNEL</h2>
        <div class="thinking hidden" id="thinking-indicator">
          <span>Analyse</span><span class="dots"></span>
        </div>
        <div class="thought-display" id="thought-display">Chargement de la dernière pensée...</div>
        <div class="meta">
          <div>
            <span>Source</span>
            <strong id="thought-source">-</strong>
          </div>
          <div>
            <span>Dernière mise à jour</span>
            <strong id="thought-updated">-</strong>
          </div>
        </div>
        <div class="grid" style="margin-top: 16px;">
          <div class="status-card">
            <h3>Profit</h3>
            <div id="status-profit"></div>
            <div class="muted" id="status-profit-detail"></div>
          </div>
          <div class="status-card">
            <h3>IA Groq</h3>
            <div id="status-groq"></div>
            <div class="muted" id="status-groq-detail"></div>
          </div>
          <div class="status-card">
            <h3>Voix</h3>
            <div id="status-audio"></div>
            <div class="muted" id="status-audio-detail"></div>
          </div>
        </div>
      </section>

      <section id="pensees" class="panel hidden">
        <h2>ARCHIVES DE PENSÉES</h2>
        <button id="clear-thoughts">Effacer</button>
        <div id="thoughts-list" class="list" style="margin-top: 12px;"></div>
      </section>

      <section id="donnees" class="panel hidden">
        <h2>DONNÉES</h2>
        <div class="grid">
          <div class="status-card">
            <h3>Dernier snapshot profit</h3>
            <pre id="profit-json">{}</pre>
          </div>
          <div class="status-card">
            <h3>Contexte IA</h3>
            <pre id="groq-json">{}</pre>
          </div>
        </div>
      </section>

      <section id="audio" class="panel hidden">
        <h2>AUDIO</h2>
        <div id="audio-status" class="muted"></div>
        <audio id="audio-player" controls style="margin-top: 12px; width: 100%;"></audio>
        <div class="footer-note">
          La lecture audio est désactivée si la voix est coupée dans les réglages.
        </div>
      </section>

      <section id="reglages" class="panel hidden">
        <h2>RÉGLAGES UTILISATEUR</h2>
        <div class="controls">
          <div class="control toggle">
            <input type="checkbox" id="voice-enabled" />
            <label for="voice-enabled">Voix HAL active</label>
          </div>
          <div class="control toggle">
            <input type="checkbox" id="notification-enabled" />
            <label for="notification-enabled">Son de notification</label>
          </div>
          <div class="control">
            <label for="speech-rate">Vitesse de parole: <span id="speech-rate-value"></span></label>
            <input type="range" id="speech-rate" min="0.7" max="1.4" step="0.05" />
          </div>
          <div class="control">
            <label for="text-speed">Vitesse affichage texte: <span id="text-speed-value"></span></label>
            <input type="range" id="text-speed" min="0.6" max="1.8" step="0.05" />
          </div>
        </div>
        <div class="footer-note">
          Les réglages sont stockés localement (localStorage). Audio OFF = silence total.
        </div>
      </section>

      <section id="journal" class="panel hidden">
        <h2>JOURNAL SYSTÈME</h2>
        <div id="journal-list" class="list"></div>
      </section>
    </main>

    <script>
      const tabButtons = document.querySelectorAll('nav button');
      const sections = document.querySelectorAll('main section');
      tabButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
          tabButtons.forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          const target = btn.dataset.tab;
          sections.forEach((section) => {
            section.classList.toggle('hidden', section.id !== target);
          });
        });
      });

      const elements = {
        thoughtDisplay: document.getElementById('thought-display'),
        thoughtSource: document.getElementById('thought-source'),
        thoughtUpdated: document.getElementById('thought-updated'),
        thinkingIndicator: document.getElementById('thinking-indicator'),
        statusProfit: document.getElementById('status-profit'),
        statusProfitDetail: document.getElementById('status-profit-detail'),
        statusGroq: document.getElementById('status-groq'),
        statusGroqDetail: document.getElementById('status-groq-detail'),
        statusAudio: document.getElementById('status-audio'),
        statusAudioDetail: document.getElementById('status-audio-detail'),
        profitJson: document.getElementById('profit-json'),
        groqJson: document.getElementById('groq-json'),
        thoughtsList: document.getElementById('thoughts-list'),
        journalList: document.getElementById('journal-list'),
        audioStatus: document.getElementById('audio-status'),
        audioPlayer: document.getElementById('audio-player'),
        clearThoughts: document.getElementById('clear-thoughts'),
        voiceEnabled: document.getElementById('voice-enabled'),
        notificationEnabled: document.getElementById('notification-enabled'),
        speechRate: document.getElementById('speech-rate'),
        speechRateValue: document.getElementById('speech-rate-value'),
        textSpeed: document.getElementById('text-speed'),
        textSpeedValue: document.getElementById('text-speed-value')
      };

      const defaultSettings = {
        voiceEnabled: true,
        notificationEnabled: true,
        speechRate: 1.0,
        textSpeed: 1.0
      };

      let displayTimeouts = [];
      let lastThoughtSignature = null;

      function loadSettings() {
        try {
          const raw = localStorage.getItem('hal-settings');
          if (!raw) return { ...defaultSettings };
          const parsed = JSON.parse(raw);
          return { ...defaultSettings, ...parsed };
        } catch (error) {
          return { ...defaultSettings };
        }
      }

      function saveSettings(settings) {
        localStorage.setItem('hal-settings', JSON.stringify(settings));
      }

      function applySettings(settings) {
        elements.voiceEnabled.checked = settings.voiceEnabled;
        elements.notificationEnabled.checked = settings.notificationEnabled;
        elements.speechRate.value = settings.speechRate;
        elements.textSpeed.value = settings.textSpeed;
        elements.speechRateValue.textContent = `${settings.speechRate.toFixed(2)}x`;
        elements.textSpeedValue.textContent = `${settings.textSpeed.toFixed(2)}x`;

        if (!settings.voiceEnabled) {
          stopAudio();
        } else {
          elements.audioPlayer.playbackRate = settings.speechRate;
        }
      }

      function stopAudio() {
        elements.audioPlayer.pause();
        elements.audioPlayer.removeAttribute('src');
        elements.audioPlayer.load();
      }

      function formatStatus(text, status) {
        const span = document.createElement('span');
        span.classList.add('pill');
        if (status === 'ok') span.classList.add('status-ok');
        if (status === 'warning' || status === 'disabled' || status === 'skipped') {
          span.classList.add('status-warn');
        }
        if (status === 'error') span.classList.add('status-error');
        span.textContent = text;
        return span.outerHTML;
      }

      function statusLabel(status) {
        switch (status) {
          case 'ok':
            return 'OK';
          case 'disabled':
            return 'Désactivé';
          case 'skipped':
            return 'Ignoré';
          case 'warning':
            return 'Attention';
          case 'error':
            return 'Erreur';
          default:
            return status || 'Inconnu';
        }
      }

      async function fetchJson(path) {
        const response = await fetch(path, { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`${path} -> ${response.status}`);
        }
        return response.json();
      }

      function clearDisplayTimers() {
        displayTimeouts.forEach((timeout) => clearTimeout(timeout));
        displayTimeouts = [];
      }

      function calculateTextDuration(text, textSpeed) {
        const base = Math.max(text.length * 45, 2000);
        return base / Math.max(textSpeed, 0.1);
      }

      async function getAudioDurationMs(settings, audioInfo, token) {
        if (!settings.voiceEnabled || !audioInfo.available) {
          return null;
        }
        return new Promise((resolve) => {
          const player = elements.audioPlayer;
          const done = () => {
            const duration = Number.isFinite(player.duration) ? player.duration : 0;
            const adjusted = duration > 0 ? (duration * 1000) / settings.speechRate : null;
            resolve(adjusted);
          };
          player.onloadedmetadata = done;
          player.onerror = () => resolve(null);
          player.src = `${audioInfo.url}?t=${token}`;
          player.load();
        });
      }

      async function playAudio(settings, audioInfo, token) {
        if (!settings.voiceEnabled || !audioInfo.available) {
          stopAudio();
          return;
        }
        const player = elements.audioPlayer;
        player.playbackRate = settings.speechRate;
        player.src = `${audioInfo.url}?t=${token}`;
        player.load();
        try {
          await player.play();
        } catch (error) {
          elements.audioStatus.textContent = "Lecture audio bloquée par le navigateur (interaction requise).";
        }
      }

      function playNotification(settings) {
        if (!settings.voiceEnabled || !settings.notificationEnabled) return;
        try {
          const context = new (window.AudioContext || window.webkitAudioContext)();
          const oscillator = context.createOscillator();
          const gain = context.createGain();
          oscillator.type = 'sine';
          oscillator.frequency.value = 880;
          gain.gain.value = 0.08;
          oscillator.connect(gain);
          gain.connect(context.destination);
          oscillator.start();
          oscillator.stop(context.currentTime + 0.15);
          oscillator.onended = () => context.close();
        } catch (error) {
          // Ignore if browser blocks audio context.
        }
      }

      function presentThought(text, segments, durationMs) {
        clearDisplayTimers();
        elements.thoughtDisplay.textContent = '';
        elements.thinkingIndicator.classList.remove('hidden');

        const safeSegments = segments && segments.length ? segments : [text];
        const totalChars = safeSegments.reduce((sum, segment) => sum + segment.length, 0) || 1;
        const totalDuration = durationMs || calculateTextDuration(text, currentSettings.textSpeed);

        let elapsed = 0;
        safeSegments.forEach((segment, index) => {
          const sliceDuration = (segment.length / totalChars) * totalDuration;
          const timeoutId = setTimeout(() => {
            const prefix = elements.thoughtDisplay.textContent ? ' ' : '';
            elements.thoughtDisplay.textContent += `${prefix}${segment}`;
            if (index === safeSegments.length - 1) {
              elements.thinkingIndicator.classList.add('hidden');
            }
          }, elapsed);
          displayTimeouts.push(timeoutId);
          elapsed += sliceDuration;
        });
      }

      let currentSettings = loadSettings();
      applySettings(currentSettings);

      function updateSettings() {
        currentSettings = {
          voiceEnabled: elements.voiceEnabled.checked,
          notificationEnabled: elements.notificationEnabled.checked,
          speechRate: Number(elements.speechRate.value),
          textSpeed: Number(elements.textSpeed.value)
        };
        saveSettings(currentSettings);
        applySettings(currentSettings);
      }

      elements.voiceEnabled.addEventListener('change', updateSettings);
      elements.notificationEnabled.addEventListener('change', updateSettings);
      elements.speechRate.addEventListener('input', updateSettings);
      elements.textSpeed.addEventListener('input', updateSettings);

      async function refresh() {
        try {
          const [health, profit, thoughts, audio] = await Promise.all([
            fetchJson('/api/health'),
            fetchJson('/api/profit'),
            fetchJson('/api/thoughts'),
            fetchJson('/api/audio')
          ]);

          const thought = health.thought || { text: health.last_thought, segments: [] };

          elements.thoughtSource.textContent = thought.source || 'inconnu';
          elements.thoughtUpdated.textContent = thought.last_update || '-';

          elements.statusProfit.innerHTML = formatStatus(statusLabel(health.profit.status), health.profit.status);
          elements.statusProfitDetail.textContent = health.profit.last_error || 'Flux profit nominal.';

          elements.statusGroq.innerHTML = formatStatus(statusLabel(health.groq.status), health.groq.status);
          elements.statusGroqDetail.textContent = health.groq.last_error || 'Synthèse HAL nominale.';

          elements.statusAudio.innerHTML = formatStatus(statusLabel(health.audio.status), health.audio.status);
          elements.statusAudioDetail.textContent = health.audio.last_error || (health.audio.available ? 'Audio disponible.' : 'Audio indisponible.');

          elements.profitJson.textContent = JSON.stringify(profit, null, 2);
          elements.groqJson.textContent = JSON.stringify(health.groq, null, 2);

          if (thoughts.items.length === 0) {
            elements.thoughtsList.textContent = 'Aucune pensée enregistrée.';
          } else {
            elements.thoughtsList.innerHTML = thoughts.items
              .map((item) => `<div class="list-item"><strong>${item.created_at}</strong> — ${item.text}</div>`)
              .join('');
          }

          if (health.issues.length === 0) {
            elements.journalList.textContent = 'Aucun incident signalé.';
          } else {
            elements.journalList.innerHTML = health.issues
              .map((issue) => `<div class="list-item">⚠️ ${issue}</div>`)
              .join('');
          }

          if (!currentSettings.voiceEnabled) {
            elements.audioStatus.textContent = 'Voix désactivée — aucun son ne sera joué.';
          } else if (audio.available) {
            elements.audioStatus.textContent = `Audio disponible (${audio.url}).`;
          } else {
            elements.audioStatus.textContent = 'Audio indisponible.';
          }

          if (currentSettings.voiceEnabled && audio.available) {
            elements.audioPlayer.classList.remove('hidden');
          } else {
            elements.audioPlayer.classList.add('hidden');
          }

          const signature = `${thought.last_update || 'no-ts'}::${thought.text}`;
          if (signature !== lastThoughtSignature) {
            lastThoughtSignature = signature;
            const token = Date.now();
            playNotification(currentSettings);
            const durationMs = await getAudioDurationMs(currentSettings, audio, token);
            presentThought(thought.text, thought.segments || [], durationMs);
            await playAudio(currentSettings, audio, token);
          }
        } catch (error) {
          elements.journalList.textContent = `Erreur UI: ${error.message}`;
        }
      }

      elements.clearThoughts.addEventListener('click', async () => {
        await fetch('/api/thoughts/clear', { method: 'POST' });
        refresh();
      });

      refresh();
      setInterval(refresh, 9000);
    </script>
  </body>
</html>
"""


@ui_bp.route("/")
def index() -> str:
    """Serve the main HAL brain UI."""
    return render_template_string(_PAGE)
