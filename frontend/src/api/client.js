const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000';

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    });
  } catch (error) {
    throw new Error('Cannot connect to API server. Please make sure backend is running on port 5000.');
  }

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    if (isJson && payload?.error) {
      throw new Error(payload.error);
    }
    if (typeof payload === 'string' && payload.trim()) {
      throw new Error(`Request failed (${response.status}): ${payload.slice(0, 160)}`);
    }
    throw new Error(`Request failed: ${response.status}`);
  }

  if (!isJson) {
    throw new Error('API returned an unexpected response format. Expected JSON.');
  }

  return payload;
}

export function getConfig() {
  return request('/api/config');
}

export function simulate(payload) {
  return request('/api/simulate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function compareStrategies(payload) {
  return request('/api/simulate/compare', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
