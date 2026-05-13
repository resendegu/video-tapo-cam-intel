/**
 * API client — thin wrapper around fetch for all backend endpoints.
 */
const API = {
  BASE: '',  // Same origin — FastAPI serves both the API and the frontend

  async get(path) {
    const res = await fetch(this.BASE + path);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async post(path, body) {
    const res = await fetch(this.BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  // Recording endpoints
  getRecordingDates:    () => API.get('/api/recordings/dates'),
  getClips:         (date) => API.get(`/api/recordings/${date}`),
  getDownloadedFiles:   () => API.get('/api/recordings/files/list'),
  videoUrl:       (fname)  => `${API.BASE}/api/recordings/files/${fname}`,
  frameUrl:       (fname)  => `${API.BASE}/api/frames/${fname}`,

  downloadClip(startTime, endTime, date) {
    const url = `${this.BASE}/api/recordings/download`;
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start_time: startTime, end_time: endTime, date }),
    });
  },

  // Analysis endpoints
  analyzeVideo:  (recordingId, filename) => API.post('/api/analysis/video',  { recording_id: recordingId, filename }),
  analyzeFrame:  (recordingId, filename) => API.post('/api/analysis/frame',  { recording_id: recordingId, filename }),
  getAnalysis:   (recordingId)           => API.get(`/api/analysis/${recordingId}`),
  listAnalyses:  ()                      => API.get('/api/analysis'),

  // Camera
  getCameraInfo:   () => API.get('/api/camera/info'),
  getCameraStatus: () => API.get('/api/camera/status'),

  // Quota
  getQuota: () => API.get('/api/quota'),
};
