/**
 * Recordings view — date selector, clip list, download manager, video player.
 */
const RecordingsView = {
  _selectedClip: null,
  _activeDate: null,

  async render(container) {
    container.innerHTML = `
      <div class="view-page">
        <div class="page-header">
          <h1>Recordings</h1>
          <p>Browse and download SD card recordings from your Tapo C500</p>
        </div>

        <div class="section">
          <div class="card">
            <div class="card-title">Recording Dates</div>
            <div id="date-selector"><div class="loading-center"><div class="spinner"></div></div></div>
          </div>
        </div>

        <div class="section split-layout">
          <div>
            <div class="card" style="min-height:300px">
              <div class="card-title" id="clips-title">Clips</div>
              <div id="clips-container">
                <div class="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>
                  </svg>
                  <h3>Select a date</h3>
                  <p>Choose a date above to see recordings</p>
                </div>
              </div>
            </div>
          </div>
          <div>
            <div class="card" id="player-card">
              <div class="card-title">Preview</div>
              <div class="video-player-wrap">
                <div class="video-placeholder">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/>
                  </svg>
                  <p>Select a downloaded clip to play</p>
                </div>
              </div>
              <div id="clip-detail" style="margin-top:16px;display:none">
                <div id="clip-detail-content"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    await this._loadDates();
  },

  async _loadDates() {
    const el = document.getElementById('date-selector');
    try {
      const data = await API.getRecordingDates();
      const dates = data.dates;
      if (!dates.length) {
        el.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No recordings found on SD card</p>`;
        return;
      }
      el.innerHTML = `
        <div class="date-grid">
          ${dates.map(d => `
            <button class="date-chip" data-date="${d}" id="chip-${d}">
              ${this._formatDate(d)}
            </button>`).join('')}
        </div>`;
      el.querySelectorAll('.date-chip').forEach(chip => {
        chip.addEventListener('click', () => this._selectDate(chip.dataset.date));
      });
    } catch (e) {
      el.innerHTML = `<p style="color:var(--accent-red);font-size:13px;">Failed to load dates: ${e.message}</p>`;
    }
  },

  async _selectDate(date) {
    // Update chip selection
    document.querySelectorAll('.date-chip').forEach(c => c.classList.remove('selected'));
    const chip = document.getElementById(`chip-${date}`);
    if (chip) chip.classList.add('selected');
    this._activeDate = date;

    const container = document.getElementById('clips-container');
    const title = document.getElementById('clips-title');
    title.textContent = `Clips — ${this._formatDate(date)}`;
    container.innerHTML = `<div class="loading-center"><div class="spinner"></div></div>`;

    try {
      const data = await API.getClips(date);
      const clips = data.clips;
      if (!clips.length) {
        container.innerHTML = `<p style="color:var(--text-muted);font-size:13px;">No clips for this date</p>`;
        return;
      }
      container.innerHTML = `<div class="clip-list">${clips.map(c => this._clipRow(c)).join('')}</div>`;
      container.querySelectorAll('.clip-row').forEach(row => {
        row.addEventListener('click', () => {
          const clip = clips.find(c => c.start_time === +row.dataset.start);
          if (clip) this._selectClip(clip);
        });
      });
    } catch (e) {
      container.innerHTML = `<p style="color:var(--accent-red);font-size:13px;">Error: ${e.message}</p>`;
    }
  },

  _clipRow(clip) {
    const start = new Date(clip.start_time * 1000);
    const badge = clip.clip_type === 'motion'
      ? `<span class="badge badge-motion">Motion</span>`
      : `<span class="badge badge-continuous">Continuous</span>`;
    const dlBadge = clip.downloaded
      ? `<span class="badge badge-downloaded">Downloaded</span>`
      : '';
    const fileSz = clip.file_size ? ` · ${(clip.file_size / 1024 / 1024).toFixed(1)} MB` : '';

    return `
      <div class="clip-row" data-start="${clip.start_time}" data-id="${clip.id ?? ''}">
        <div class="clip-info">
          <div class="clip-time">${start.toLocaleTimeString()}</div>
          <div class="clip-meta">${clip.duration}s${fileSz}</div>
        </div>
        ${badge}
        ${dlBadge}
        <div id="dl-btn-${clip.start_time}">
          ${clip.downloaded
            ? `<button class="btn btn-ghost btn-sm" onclick="RecordingsView._playClip('${clip.filename}',event)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>Play</button>`
            : `<button class="btn btn-primary btn-sm" onclick="RecordingsView._startDownload(${clip.start_time},${clip.end_time},'${this._activeDate}',event)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>Download</button>`}
        </div>
      </div>`;
  },

  _selectClip(clip) {
    this._selectedClip = clip;
    if (clip.downloaded && clip.filename) {
      this._playClip(clip.filename);
    }
    const detail = document.getElementById('clip-detail');
    const content = document.getElementById('clip-detail-content');
    detail.style.display = 'block';

    const canAnalyze = clip.downloaded && clip.id;
    content.innerHTML = `
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-analyze btn-sm"
          ${canAnalyze ? '' : 'disabled'}
          onclick="RecordingsView._analyzeClip(${clip.id},'${clip.filename}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8"/>
          </svg>Video Analysis
        </button>
        <button class="btn btn-ghost btn-sm"
          ${canAnalyze ? '' : 'disabled'}
          onclick="RecordingsView._analyzeFrame(${clip.id},'${clip.filename}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>Frame Vision
        </button>
      </div>
      ${!canAnalyze ? '<p style="font-size:11px;color:var(--text-muted);margin-top:8px;">Download the clip first to analyze it</p>' : ''}
    `;
  },

  _playClip(filename, event) {
    if (event) event.stopPropagation();
    const wrap = document.querySelector('.video-player-wrap');
    wrap.innerHTML = `<video controls autoplay src="${API.videoUrl(filename)}"></video>`;
  },

  async _startDownload(startTime, endTime, date, event) {
    event.stopPropagation();
    const btnWrap = document.getElementById(`dl-btn-${startTime}`);
    btnWrap.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;flex-direction:column;width:120px">
        <div class="progress-bar-container" style="width:100%">
          <div class="progress-bar" id="pb-${startTime}"></div>
        </div>
        <span style="font-size:11px;color:var(--text-muted)" id="dl-status-${startTime}">Starting…</span>
      </div>`;

    try {
      const response = await API.downloadClip(startTime, endTime, date);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split('\n').filter(l => l.startsWith('data:'));
        for (const line of lines) {
          const data = JSON.parse(line.slice(5));
          if (data.error) { showToast(data.error, 'error'); break; }
          if (data.done) {
            showToast(`Downloaded ${data.filename}`, 'success');
            // Refresh clip list
            await this._selectDate(date);
            return;
          }
          if (data.progress && data.total) {
            const pct = Math.round((data.progress / data.total) * 100);
            const pb = document.getElementById(`pb-${startTime}`);
            const st = document.getElementById(`dl-status-${startTime}`);
            if (pb) pb.style.width = pct + '%';
            if (st) st.textContent = `${pct}%`;
          }
        }
      }
    } catch (e) {
      showToast(`Download failed: ${e.message}`, 'error');
    }
  },

  async _analyzeClip(recordingId, filename) {
    showToast('Submitting to Video Intelligence API…', 'info');
    try {
      const result = await API.analyzeVideo(recordingId, filename);
      showToast('Video analysis complete!', 'success');
      App.navigate('analysis');
    } catch (e) {
      showToast(e.message, 'error');
    }
  },

  async _analyzeFrame(recordingId, filename) {
    showToast('Extracting keyframe and analyzing…', 'info');
    try {
      await API.analyzeFrame(recordingId, filename);
      showToast('Frame analysis complete!', 'success');
      App.navigate('analysis');
    } catch (e) {
      showToast(e.message, 'error');
    }
  },

  _formatDate(d) {
    const y = d.slice(0, 4), m = d.slice(4, 6), day = d.slice(6, 8);
    return new Date(`${y}-${m}-${day}`).toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric' });
  },
};
