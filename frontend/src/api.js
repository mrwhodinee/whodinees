// Frontend is served from the same origin as the API in prod.
// In dev, Vite proxy forwards /api -> backend.
const BASE = ''

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`
    try { const b = await resp.json(); msg = b.error || b.detail || JSON.stringify(b) } catch {}
    throw new Error(msg)
  }
  if (resp.status === 204) return null
  return resp.json()
}

async function postForm(path, formData) {
  const resp = await fetch(`${BASE}${path}`, { method: 'POST', body: formData })
  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`
    try { const b = await resp.json(); msg = b.error || b.detail || JSON.stringify(b) } catch {}
    throw new Error(msg)
  }
  return resp.json()
}

export const api = {
  // Store (existing sculptural dinees)
  listProducts: () => request('/api/products/'),
  getProduct:   (slug) => request(`/api/products/${slug}/`),
  createOrder:  (payload) => request('/api/orders/', { method: 'POST', body: JSON.stringify(payload) }),
  getOrder:     (token) => request(`/api/orders/${token}/`),

  // Portraits
  createPortrait:     (fd) => postForm('/api/portraits/', fd),
  getPortrait:        (id) => request(`/api/portraits/${id}/`),
  startGeneration:    (id) => request(`/api/portraits/${id}/start-generation`, { method: 'POST', body: '{}' }),
  approveVariant:     (id, taskId) => request(`/api/portraits/${id}/approve`, { method: 'POST', body: JSON.stringify({ task_id: taskId }) }),
  createPortraitOrder:(id, payload) => request(`/api/portraits/${id}/order`, { method: 'POST', body: JSON.stringify(payload) }),
  calculatePortraitPrice:(id, material) => request(`/api/portraits/${id}/calculate-price`, { method: 'POST', body: JSON.stringify({ material }) }),
  getPortraitPricing: () => request('/api/pricing/portrait'),
}
