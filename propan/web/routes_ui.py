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
    <title>HAL Brain</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #0b0b0f;
        --panel: #15151c;
        --accent: #e63946;
        --text: #f1f1f5;
        --muted: #a0a0b2;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Inter", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      header {
        padding: 20px 24px;
        border-bottom: 1px solid #242433;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        justify-content: space-between;
      }
      header h1 {
        margin: 0;
        font-size: 20px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent);
      }
      nav {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      nav button {
        background: transparent;
        border: 1px solid #2c2c3c;
        color: var(--text);
        padding: 8px 14px;
        border-radius: 6px;
        cursor: pointer;
      }
      nav button.active {
        background: var(--accent);
        border-color: var(--accent);
      }
      main {
        padding: 24px;
        display: grid;
        gap: 16px;
      }
      .panel {
        background: var(--panel);
        border: 1px solid #252534;
        border-radius: 12px;
        padding: 16px;
      }
      .panel h2 {
        margin-top: 0;
        font-size: 16px;
        color: var(--accent);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      .muted { color: var(--muted); }
      .hidden { display: none; }
      pre {
        white-space: pre-wrap;
        word-break: break-word;
        margin: 0;
      }
      .pill {
        display: inline-flex;
        padding: 2px 8px;
        border-radius: 999px;
        background: #2b2b3a;
        font-size: 12px;
      }
      .status-ok { background: rgba(70, 170, 90, 0.2); }
      .status-warn { background: rgba(255, 184, 77, 0.2); }
      .status-error { background: rgba(230, 57, 70, 0.25); }
      @media (max-width: 720px) {
        header { flex-direction: column; align-items: flex-start; }
      }
    </style>
  </head>
  <body>
    <header>
      <h1>HAL Brain</h1>
      <nav>
        <button data-tab="overview" class="active">Overview</button>
        <button data-tab="profit">Profit</button>
        <button data-tab="thoughts">Thoughts</button>
        <button data-tab="logs">Logs</button>
        <button data-tab="audio">Audio</button>
        <button data-tab="settings">Settings</button>
      </nav>
    </header>
    <main>
      <section id="overview" class="panel">
        <h2>Overview</h2>
        <div class="grid">
          <div>
            <div class="muted">Dernière pensée</div>
            <p id="overview-thought">Chargement...</p>
          </div>
          <div>
            <div class="muted">Profit status</div>
            <p id="overview-profit">-</p>
          </div>
          <div>
            <div class="muted">Groq status</div>
            <p id="overview-groq">-</p>
          </div>
          <div>
            <div class="muted">Audio status</div>
            <p id="overview-audio">-</p>
          </div>
        </div>
      </section>

      <section id="profit" class="panel hidden">
        <h2>Profit</h2>
        <p class="muted">Données brutes du moteur profit.</p>
        <pre id="profit-json">{}</pre>
      </section>

      <section id="thoughts" class="panel hidden">
        <h2>Thoughts</h2>
        <button id="clear-thoughts">Effacer</button>
        <div id="thoughts-list" class="muted" style="margin-top: 12px;"></div>
      </section>

      <section id="logs" class="panel hidden">
        <h2>Logs</h2>
        <div id="logs-list" class="muted"></div>
      </section>

      <section id="audio" class="panel hidden">
        <h2>Audio</h2>
        <div id="audio-status" class="muted"></div>
        <audio id="audio-player" controls style="margin-top: 12px; width: 100%;"></audio>
      </section>

      <section id="settings" class="panel hidden">
        <h2>Settings</h2>
        <pre id="settings-json">{}</pre>
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
        overviewThought: document.getElementById('overview-thought'),
        overviewProfit: document.getElementById('overview-profit'),
        overviewGroq: document.getElementById('overview-groq'),
        overviewAudio: document.getElementById('overview-audio'),
        profitJson: document.getElementById('profit-json'),
        thoughtsList: document.getElementById('thoughts-list'),
        logsList: document.getElementById('logs-list'),
        audioStatus: document.getElementById('audio-status'),
        audioPlayer: document.getElementById('audio-player'),
        settingsJson: document.getElementById('settings-json'),
        clearThoughts: document.getElementById('clear-thoughts')
      };

      function formatStatus(text, status) {
        const span = document.createElement('span');
        span.classList.add('pill');
        if (status === 'ok') span.classList.add('status-ok');
        if (status === 'warning' || status === 'disabled') span.classList.add('status-warn');
        if (status === 'error') span.classList.add('status-error');
        span.textContent = text;
        return span.outerHTML;
      }

      async function fetchJson(path) {
        const response = await fetch(path);
        if (!response.ok) {
          throw new Error(`${path} -> ${response.status}`);
        }
        return response.json();
      }

      async function refresh() {
        try {
          const [health, profit, thoughts, audio] = await Promise.all([
            fetchJson('/api/health'),
            fetchJson('/api/profit'),
            fetchJson('/api/thoughts'),
            fetchJson('/api/audio')
          ]);

          elements.overviewThought.textContent = health.last_thought || 'Aucune pensée.';
          elements.overviewProfit.innerHTML = formatStatus(
            health.profit.status,
            health.profit.status
          );
          elements.overviewGroq.innerHTML = formatStatus(
            health.groq.status,
            health.groq.status
          );
          elements.overviewAudio.innerHTML = formatStatus(
            health.audio.status,
            health.audio.status
          );

          elements.profitJson.textContent = JSON.stringify(profit, null, 2);

          if (thoughts.items.length === 0) {
            elements.thoughtsList.textContent = 'Aucune pensée enregistrée.';
          } else {
            elements.thoughtsList.innerHTML = thoughts.items
              .map((item) => `<div><strong>${item.created_at}</strong> - ${item.text}</div>`)
              .join('');
          }

          if (health.issues.length === 0) {
            elements.logsList.textContent = 'Aucun incident.';
          } else {
            elements.logsList.innerHTML = health.issues
              .map((issue) => `<div>⚠️ ${issue}</div>`)
              .join('');
          }

          elements.audioStatus.textContent = audio.available
            ? `Audio disponible (${audio.url}).`
            : 'Audio indisponible.';
          if (audio.available) {
            elements.audioPlayer.src = audio.url;
            elements.audioPlayer.classList.remove('hidden');
          } else {
            elements.audioPlayer.removeAttribute('src');
          }

          elements.settingsJson.textContent = JSON.stringify(health.settings, null, 2);
        } catch (error) {
          elements.logsList.textContent = `Erreur UI: ${error.message}`;
        }
      }

      elements.clearThoughts.addEventListener('click', async () => {
        await fetch('/api/thoughts/clear', { method: 'POST' });
        refresh();
      });

      refresh();
      setInterval(refresh, 10000);
    </script>
  </body>
</html>
"""


@ui_bp.route("/")
def index() -> str:
    """Serve the main HAL brain UI."""
    return render_template_string(_PAGE)
