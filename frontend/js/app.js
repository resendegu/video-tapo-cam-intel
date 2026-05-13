/**
 * App router and global utilities.
 */

const VIEWS = {
  dashboard:  DashboardView,
  recordings: RecordingsView,
  analysis:   AnalysisView,
};

const App = {
  _current: null,

  init() {
    // Hash-based routing
    window.addEventListener('hashchange', () => this._handleRoute());
    this._handleRoute();
    this._pollCameraStatus();
  },

  _handleRoute() {
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    const view = VIEWS[hash] || VIEWS.dashboard;
    this._activateView(hash, view);
  },

  navigate(view) {
    window.location.hash = view;
  },

  _activateView(name, view) {
    if (this._current === name) return;
    this._current = name;

    // Update nav
    document.querySelectorAll('.nav-link').forEach(l => {
      l.classList.toggle('active', l.dataset.view === name);
    });

    const container = document.getElementById('view-container');
    view.render(container);
  },

  async _pollCameraStatus() {
    const update = async () => {
      const el = document.getElementById('camera-status-indicator');
      if (!el) return;
      try {
        const data = await API.getCameraStatus();
        const online = data.status === 'online';
        el.innerHTML = `
          <div class="status-dot ${online ? 'status-online' : 'status-offline'}"></div>
          <span>${online ? 'Camera Online' : 'Camera Offline'}</span>`;
      } catch {
        el.innerHTML = `<div class="status-dot status-offline"></div><span>Camera Offline</span>`;
      }
    };
    await update();
    setInterval(update, 30_000);
  },
};

// ── Global helpers ────────────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
  }[type] || 'ℹ';

  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => App.init());
