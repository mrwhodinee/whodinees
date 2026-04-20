import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import ProductCard from '../components/ProductCard.jsx'

export default function Shop() {
  const [products, setProducts] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    api.listProducts().then(setProducts).catch(e => setErr(String(e)))
  }, [])
  return (
    <section className="container page">
      <h1>All dinees</h1>
      <p style={{color:'var(--ink-soft)', marginTop:'-0.5rem'}}>Tiny 3D printed planters. Pick your favorite.</p>
      {err && <div className="notice">Failed to load: {err}</div>}
      {products === null && !err && <div className="loading">Loading products…</div>}
      {products && products.length === 0 && <div className="empty">No products yet.</div>}
      {products && products.length > 0 && (
        <div className="grid">
          {products.map(p => <ProductCard key={p.slug} product={p} />)}
        </div>
      )}
    </section>
  )
}
