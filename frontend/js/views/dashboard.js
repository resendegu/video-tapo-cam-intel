/**
 * Dashboard view — camera status, quota gauges, recent activity.
 */
const DashboardView = {
  async render(container) {
    container.innerHTML = `
      <div class="view-page">
        <div class="page-header">
          <h1>Dashboard</h1>
          <p>Camera health, quota usage, and recent activity</p>
        </div>

        <div class="section grid-4" id="stat-cards">
          ${['', '', '', ''].map(() => `
            <div class="stat-card">
              <div class="loading-center"><div class="spinner"></div></div>
            </div>`).join('')}
        </div>

        <div class="section grid-2">
          <div class="card quota-card">
            <div class="card-title">GCP Free Tier Usage</div>
            <div id="quota-content"><div class="loading-center"><div class="spinner"></div></div></div>
          </div>
          <div class="card">
            <div class="card-title">Camera Information</div>
            <div id="camera-info-content"><div class="loading-center"><div class="spinner"></div></div></div>
          </div>
        </div>

        <div class="section">
          <div class="card">
            <div class="card-title">Recent Activity</div>
            <div id="activity-content"><div class="loading-center"><div class="spinner"></div></div></div>
          </div>
        </div>
      </div>
    `;

    // Load all data in parallel
    const [quotaData, cameraData, analysesData] = await Promise.allSettled([
      API.getQuota(),
      API.getCameraInfo(),
      API.listAnalyses(),
    ]);

    this._renderStats(quotaData, cameraData);
    this._renderQuota(quotaData);
    this._renderCameraInfo(cameraData);
    this._renderActivity(analysesData);
  },

  _renderStats(quotaResult, cameraResult) {
    const quota = quotaResult.status === 'fulfilled' ? quotaResult.value : null;
    const camera = cameraResult.status === 'fulfilled' ? cameraResult.value : null;

    const videoUsed = quota?.video_intelligence?.used ?? '—';
    const visionUsed = quota?.vision?.used ?? '—';
    const model = camera?.info?.device_model ?? '—';
    const status = camera?.status ?? 'offline';

    document.getElementById('stat-cards').innerHTML = `
      <div class="stat-card">
        <div class="stat-icon cyan">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M20.188 10.934c.212.592.312 1.219.312 1.866 0 .647-.1 1.274-.312 1.866l2.119 1.524a10.016 10.016 0 000-6.78l-2.119 1.524z"/>
          </svg>
        </div>
        <div class="stat-value">${model}</div>
        <div class="stat-label">Camera Model</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon ${status === 'online' ? 'green' : 'amber'}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <div class="stat-value">${status === 'online' ? 'Online' : 'Offline'}</div>
        <div class="stat-label">Camera Status</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>
          </svg>
        </div>
        <div class="stat-value">${videoUsed}</div>
        <div class="stat-label">Video Minutes Used</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon amber">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </div>
        <div class="stat-value">${visionUsed}</div>
        <div class="stat-label">Vision Units Used</div>
      </div>
    `;
  },

  _renderQuota(result) {
    const el = document.getElementById('quota-content');
    if (result.status !== 'fulfilled') {
      el.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">Could not load quota data</p>`;
      return;
    }
    const q = result.value;
    const vi = q.video_intelligence;
    const vs = q.vision;
    const viPct = Math.min(100, (vi.used / vi.limit) * 100);
    const vsPct = Math.min(100, (vs.used / vs.limit) * 100);
    const viClass = viPct > 90 ? 'danger' : viPct > 70 ? 'warning' : '';
    const vsClass = vsPct > 90 ? 'danger' : vsPct > 70 ? 'warning' : '';

    el.innerHTML = `
      <div class="quota-row">
        <div class="quota-header">
          <span class="quota-name">Video Intelligence</span>
          <span class="quota-numbers">${vi.used} / ${vi.limit} min</span>
        </div>
        <div class="quota-bar-bg">
          <div class="quota-bar ${viClass}" style="width:${viPct}%"></div>
        </div>
      </div>
      <div class="quota-row">
        <div class="quota-header">
          <span class="quota-name">Cloud Vision</span>
          <span class="quota-numbers">${vs.used} / ${vs.limit} units</span>
        </div>
        <div class="quota-bar-bg">
          <div class="quota-bar ${vsClass}" style="width:${vsPct}%"></div>
        </div>
      </div>
      <p style="font-size:11px;color:var(--text-muted);margin-top:14px;">
        Month: ${q.month} · Resets on 1st of next month
      </p>
    `;
  },

  _renderCameraInfo(result) {
    const el = document.getElementById('camera-info-content');
    if (result.status !== 'fulfilled') {
      el.innerHTML = `<p style="color:var(--accent-red);font-size:13px;">Camera offline or unreachable</p>`;
      return;
    }
    const info = result.value.info;
    const rows = [
      ['Model', info.device_model ?? '—'],
      ['Alias', info.device_alias ?? '—'],
      ['Firmware', info.sw_version ?? '—'],
      ['Hardware', info.hw_version ?? '—'],
      ['MAC', info.mac ?? '—'],
      ['Region', info.region ?? '—'],
    ];
    el.innerHTML = `
      <table class="info-table">
        ${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join('')}
      </table>
    `;
  },

  _renderActivity(result) {
    const el = document.getElementById('activity-content');
    if (result.status !== 'fulfilled' || !result.value.analyses?.length) {
      el.innerHTML = `
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
          </svg>
          <p>No analysis activity yet</p>
        </div>`;
      return;
    }
    const analyses = result.value.analyses.slice(0, 8);
    el.innerHTML = `
      <div class="activity-list">
        ${analyses.map(a => {
          const date = new Date(a.created_at + 'Z');
          const label = a.service === 'video_intelligence' ? 'Video Intelligence' : 'Cloud Vision';
          const dot = a.service === 'vision' ? 'analysis' : 'download';
          return `
            <div class="activity-item">
              <div class="activity-dot ${dot}"></div>
              <div class="activity-text">
                <strong>${label}</strong> — ${a.filename ?? a.recording_id}
                <span style="margin-left:6px;font-size:11px;padding:2px 6px;border-radius:4px;
                  background:${a.status==='completed'?'rgba(16,185,129,0.1)':'rgba(239,68,68,0.1)'};
                  color:${a.status==='completed'?'var(--accent-green)':'#f87171'}">${a.status}</span>
              </div>
              <div class="activity-time">${date.toLocaleTimeString()}</div>
            </div>`;
        }).join('')}
      </div>`;
  },
};
