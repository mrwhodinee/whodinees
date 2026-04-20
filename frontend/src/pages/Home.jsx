import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ProductCard from '../components/ProductCard.jsx'

export default function Home() {
  const [products, setProducts] = useState(null)
  useEffect(() => { api.listProducts().then(setProducts).catch(() => setProducts([])) }, [])
  const featured = (products || []).slice(0, 4)

  return (
    <>
      <section className="hero">
        <div className="container">
          <div className="sparkles">✨ introducing Whodinees Portraits</div>
          <h1>tiny figurines of your<br/>tiny best friend.</h1>
          <p className="tagline">
            Custom 3D pet portraits from your photo — in plastic, bronze, silver, or gold.
          </p>
          <div className="ctas">
            <Link className="button" to="/portraits">Start your portrait →</Link>
            <Link className="button-ghost" to="/shop">Shop the sculptural dinees</Link>
          </div>
          <p className="coming-soon">$19 refundable deposit · 3 variants to pick from</p>
        </div>
      </section>

      <section className="container">
        <h2>Also: small sculptural dinees</h2>
        <p style={{color:'var(--ink-soft)'}}>
          Our first drop — tiny sculptural things for your desk, shelf, your life. 3D-printed to order.
        </p>
        {products === null && <div className="loading">Loading…</div>}
        {products !== null && featured.length === 0 && (
          <div className="empty">No products yet — check back soon.</div>
        )}
        {featured.length > 0 && (
          <div className="grid">
            {featured.map(p => <ProductCard key={p.slug} product={p} />)}
          </div>
        )}
      </section>
    </>
  )
}
