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

export const api = {
  listProducts: () => request('/api/products/'),
  getProduct:   (slug) => request(`/api/products/${slug}/`),
  createOrder:  (payload) => request('/api/orders/', { method: 'POST', body: JSON.stringify(payload) }),
  getOrder:     (token) => request(`/api/orders/${token}/`),
}
