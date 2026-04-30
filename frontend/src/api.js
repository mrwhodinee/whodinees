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

  // Portraits (SECURE - use UUID token + email)
  createPortrait:     (fd) => postForm('/api/portraits/', fd),
  getPortrait:        (token, email) => request(`/api/portraits/${token}/?email=${encodeURIComponent(email)}`),
  startGeneration:    (token, email) => request(`/api/portraits/${token}/start-generation`, { method: 'POST', body: JSON.stringify({ email }) }),
  approveVariant:     (token, taskId, email) => request(`/api/portraits/${token}/approve`, { method: 'POST', body: JSON.stringify({ task_id: taskId, email }) }),
  createPortraitOrder:(token, payload) => request(`/api/portraits/${token}/order`, { method: 'POST', body: JSON.stringify(payload) }),
  calculatePortraitPrice:(token, material, email) => request(`/api/portraits/${token}/calculate-price`, { method: 'POST', body: JSON.stringify({ material, email }) }),
  getPortraitPricing: () => request('/api/pricing/portrait'),
}
