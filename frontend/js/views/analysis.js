/**
 * Analysis view — browse GCP analysis results with labels, objects, and keyframes.
 */
const AnalysisView = {
  async render(container) {
    container.innerHTML = `
      <div class="view-page">
        <div class="page-header">
          <h1>Analysis Results</h1>
          <p>AI-powered insights from Google Cloud Video Intelligence and Vision APIs</p>
        </div>
        <div class="section">
          <div class="card">
            <div class="card-title">All Analyses</div>
            <div id="analysis-list"><div class="loading-center"><div class="spinner"></div></div></div>
          </div>
        </div>
        <div class="section" id="analysis-detail-section" style="display:none">
          <div class="card">
            <div class="card-title" id="detail-title">Result Detail</div>
            <div id="analysis-detail-content"></div>
          </div>
        </div>
      </div>`;

    await this._loadList();
  },

  async _loadList() {
    const el = document.getElementById('analysis-list');
    try {
      const data = await API.listAnalyses();
      const analyses = data.analyses;
      if (!analyses.length) {
        el.innerHTML = `
          <div class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8"/>
            </svg>
            <h3>No analyses yet</h3>
            <p>Download a recording and click Analyze to get started</p>
          </div>`;
        return;
      }

      el.innerHTML = `
        <div class="clip-list">
          ${analyses.map(a => this._analysisRow(a)).join('')}
        </div>`;
      el.querySelectorAll('[data-analysis-id]').forEach(row => {
        row.addEventListener('click', () => this._showDetail(row.dataset.analysisId, row.dataset.recordingId));
      });
    } catch (e) {
      el.innerHTML = `<p style="color:var(--accent-red);font-size:13px;">Error: ${e.message}</p>`;
    }
  },

  _analysisRow(a) {
    const created = new Date(a.created_at + 'Z');
    const serviceLabel = a.service === 'video_intelligence' ? 'Video Intelligence' : 'Cloud Vision';
    const serviceColor = a.service === 'video_intelligence' ? '#a78bfa' : 'var(--accent-cyan)';
    const statusColor = a.status === 'completed' ? 'var(--accent-green)' : a.status === 'failed' ? 'var(--accent-red)' : 'var(--accent-amber)';

    return `
      <div class="clip-row" style="cursor:pointer" data-analysis-id="${a.id}" data-recording-id="${a.recording_id}">
        <div class="clip-info">
          <div class="clip-time">${a.filename ?? `Recording #${a.recording_id}`}</div>
          <div class="clip-meta">${created.toLocaleString()}</div>
        </div>
        <span style="font-size:12px;font-weight:600;color:${serviceColor}">${serviceLabel}</span>
        <span style="font-size:12px;font-weight:600;color:${statusColor}">${a.status}</span>
        ${a.units_used ? `<span style="font-size:11px;color:var(--text-muted)">${a.units_used.toFixed ? a.units_used.toFixed(2) : a.units_used} units</span>` : ''}
      </div>`;
  },

  async _showDetail(analysisId, recordingId) {
    const section = document.getElementById('analysis-detail-section');
    const content = document.getElementById('analysis-detail-content');
    const title = document.getElementById('detail-title');
    section.style.display = 'block';
    content.innerHTML = `<div class="loading-center"><div class="spinner"></div></div>`;
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    try {
      const data = await API.getAnalysis(recordingId);
      const analyses = data.analyses;
      const a = analyses.find(x => x.id === +analysisId) || analyses[0];
      if (!a || !a.result) {
        content.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No result data available</p>`;
        return;
      }
      title.textContent = `${a.service === 'video_intelligence' ? 'Video Intelligence' : 'Cloud Vision'} — ${a.completed_at ? new Date(a.completed_at + 'Z').toLocaleString() : ''}`;

      const result = a.result;

      if (a.service === 'video_intelligence') {
        content.innerHTML = this._renderVideoResult(result);
      } else {
        content.innerHTML = this._renderVisionResult(result);
      }
    } catch (e) {
      content.innerHTML = `<p style="color:var(--accent-red);font-size:13px;">Error: ${e.message}</p>`;
    }
  },

  _renderVideoResult(result) {
    const labels = result.labels || [];
    const objects = result.objects || [];
    const shots = result.shots || [];

    return `
      <div>
        <div class="analysis-section-title">Detected Labels (${labels.length})</div>
        <div class="label-tags">
          ${labels.length ? labels.map(l => {
            const maxConf = Math.max(...(l.segments || []).map(s => s.confidence), 0);
            return `<span class="label-tag">${l.description}<span class="label-score">${(maxConf * 100).toFixed(0)}%</span></span>`;
          }).join('') : '<span style="color:var(--text-muted);font-size:13px">None detected</span>'}
        </div>

        <div class="analysis-section-title">Tracked Objects (${objects.length})</div>
        <div class="label-tags">
          ${objects.length ? objects.map(o =>
            `<span class="label-tag">${o.description}<span class="label-score">${(o.confidence * 100).toFixed(0)}%</span></span>`
          ).join('') : '<span style="color:var(--text-muted);font-size:13px">None detected</span>'}
        </div>

        <div class="analysis-section-title">Shot Changes (${shots.length})</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap">
          ${shots.length ? shots.map(s =>
            `<span style="font-size:11px;padding:3px 7px;border-radius:4px;background:var(--bg-elevated);color:var(--text-muted)">
              ${s.start_s.toFixed(1)}s – ${s.end_s.toFixed(1)}s
            </span>`
          ).join('') : '<span style="color:var(--text-muted);font-size:13px">No shot changes</span>'}
        </div>
      </div>`;
  },

  _renderVisionResult(result) {
    const labels = result.labels || [];
    const objects = result.objects || [];
    const frame = result.frame_path;

    return `
      <div class="grid-2" style="gap:24px">
        <div>
          ${frame ? `<img class="keyframe-img" src="/api/frames/${frame}" alt="Keyframe" loading="lazy"/>` : ''}
        </div>
        <div>
          <div class="analysis-section-title">Labels (${labels.length})</div>
          <div class="label-tags" style="margin-bottom:20px">
            ${labels.map(l =>
              `<span class="label-tag">${l.description}<span class="label-score">${(l.score * 100).toFixed(0)}%</span></span>`
            ).join('')}
          </div>

          <div class="analysis-section-title">Localized Objects (${objects.length})</div>
          <div style="display:flex;flex-direction:column;gap:6px">
            ${objects.length ? objects.map(o => `
              <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 12px;background:var(--bg-elevated);border-radius:6px;font-size:13px">
                <span style="color:var(--text-primary)">${o.name}</span>
                <span style="color:var(--accent-cyan)">${(o.score * 100).toFixed(0)}%</span>
              </div>`).join('')
              : '<span style="color:var(--text-muted);font-size:13px">No objects detected</span>'}
          </div>
        </div>
      </div>`;
  },
};
