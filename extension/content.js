/**
 * TRANSLARA — Multilingual Classroom Subtitle HUD (Injected Content Script).
 */

(function () {
  let hudContainer = null;
  let isMinimized = false;

  function createHUD() {
    if (document.getElementById('translara-hud')) return;

    hudContainer = document.createElement('div');
    hudContainer.id = 'translara-hud';
    hudContainer.innerHTML = `
      <div id="translara-hud-header">
        <div class="translara-hud-title">
          <span class="translara-hud-badge">TRANSLARA</span>
          <span id="translara-hud-pair">TA ⇄ ML</span>
        </div>
        <div class="translara-hud-controls">
          <button id="translara-hud-min-btn" title="Minimize">_</button>
          <button id="translara-hud-close-btn" title="Close">✕</button>
        </div>
      </div>
      <div id="translara-hud-content">
        <div class="translara-hud-row">
          <span class="translara-hud-lang-tag">தமிழ் / TAMIL</span>
          <p id="translara-hud-transcript">வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?</p>
        </div>
        <div class="translara-hud-divider"></div>
        <div class="translara-hud-row">
          <span class="translara-hud-lang-tag south" id="translara-hud-target-tag">മലയാളം / MALAYALAM</span>
          <p id="translara-hud-translation">നമസ്കാരം, സുഖമാണോ?</p>
        </div>
        <div id="translara-hud-footer">
          <div id="translara-hud-entities"></div>
          <div id="translara-hud-meta">
            <span id="translara-hud-latency" class="translara-hud-pill green">1.4s</span>
            <span id="translara-hud-mode" class="translara-hud-pill">Live AI</span>
          </div>
        </div>
      </div>
    `;

    // Inject Styles
    const style = document.createElement('style');
    style.textContent = `
      #translara-hud {
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        width: 620px;
        background: rgba(15, 23, 42, 0.94);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 14px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), 0 0 20px rgba(13, 148, 136, 0.2);
        color: #f8fafc;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        z-index: 2147483647;
        overflow: hidden;
        user-select: none;
        transition: height 0.2s ease, opacity 0.2s ease;
      }
      #translara-hud-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 14px;
        background: rgba(30, 41, 59, 0.8);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        cursor: grab;
      }
      .translara-hud-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        font-weight: 700;
      }
      .translara-hud-badge {
        background: linear-gradient(135deg, #0d9488, #059669);
        color: #fff;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.5px;
      }
      #translara-hud-pair {
        color: #94a3b8;
        font-size: 10px;
        letter-spacing: 1px;
      }
      .translara-hud-controls button {
        background: transparent;
        border: none;
        color: #94a3b8;
        cursor: pointer;
        font-size: 12px;
        padding: 2px 6px;
        border-radius: 4px;
      }
      .translara-hud-controls button:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
      }
      #translara-hud-content {
        padding: 12px 16px;
      }
      .translara-hud-row {
        margin-bottom: 6px;
      }
      .translara-hud-lang-tag {
        font-size: 9.5px;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 2px;
      }
      .translara-hud-lang-tag.south {
        color: #34d399;
      }
      #translara-hud-transcript {
        font-size: 14px;
        margin: 0;
        color: #cbd5e1;
        line-height: 1.4;
      }
      #translara-hud-translation {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        color: #f1f5f9;
        line-height: 1.4;
      }
      .translara-hud-divider {
        height: 1px;
        background: rgba(255, 255, 255, 0.08);
        margin: 8px 0;
      }
      #translara-hud-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 8px;
      }
      #translara-hud-entities {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .translara-entity-pill {
        font-size: 10px;
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
      }
      #translara-hud-meta {
        display: flex;
        gap: 6px;
      }
      .translara-hud-pill {
        font-size: 9.5px;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.05);
        color: #94a3b8;
        border: 1px solid rgba(255, 255, 255, 0.1);
      }
      .translara-hud-pill.green {
        color: #34d399;
        border-color: rgba(52, 211, 153, 0.3);
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(hudContainer);

    makeDraggable(hudContainer, document.getElementById('translara-hud-header'));

    document.getElementById('translara-hud-close-btn').onclick = () => {
      hudContainer.style.display = 'none';
    };

    document.getElementById('translara-hud-min-btn').onclick = () => {
      isMinimized = !isMinimized;
      document.getElementById('translara-hud-content').style.display = isMinimized ? 'none' : 'block';
    };
  }

  function makeDraggable(el, handle) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    handle.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
      e.preventDefault();
      pos3 = e.clientX;
      pos4 = e.clientY;
      document.onmouseup = closeDragElement;
      document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
      e.preventDefault();
      pos1 = pos3 - e.clientX;
      pos2 = pos4 - e.clientY;
      pos3 = e.clientX;
      pos4 = e.clientY;
      el.style.top = `${el.offsetTop - pos2}px`;
      el.style.left = `${el.offsetLeft - pos1}px`;
      el.style.transform = 'none';
      el.style.bottom = 'auto';
    }

    function closeDragElement() {
      document.onmouseup = null;
      document.onmousemove = null;
    }
  }

  // Listen for messages from extension popup
  chrome.runtime.onMessage.addListener((request) => {
    if (request.action === 'UPDATE_TRANSLARA_SUBTITLE') {
      createHUD();
      hudContainer.style.display = 'block';

      const data = request.data;
      document.getElementById('translara-hud-pair').textContent = `${(data.source_lang || 'TA').toUpperCase()} ⇄ ${(data.target_lang || 'ML').toUpperCase()}`;
      document.getElementById('translara-hud-transcript').textContent = data.transcript || '';
      document.getElementById('translara-hud-translation').textContent = data.translation || '';

      const latEl = document.getElementById('translara-hud-latency');
      const latSec = ((data.latency_ms || 1400) / 1000).toFixed(2);
      latEl.textContent = `${latSec}s`;

      const entContainer = document.getElementById('translara-hud-entities');
      entContainer.innerHTML = '';
      if (data.entities_locked && data.entities_locked.length > 0) {
        data.entities_locked.forEach((ent) => {
          const pill = document.createElement('span');
          pill.className = 'translara-entity-pill';
          pill.textContent = `🔒 ${ent.text}`;
          entContainer.appendChild(pill);
        });
      }
    }
  });
})();
