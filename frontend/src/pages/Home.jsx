import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ProductCard from '../components/ProductCard.jsx'

export default function Home() {
  const [products, setProducts] = useState(null)
  useEffect(() => {
    api.listProducts().then(setProducts).catch(() => setProducts([]))
  }, [])

  const featured = (products || []).slice(0, 4)

  return (
    <>
      <section className="hero">
        <div className="container">
          <div className="sparkles">✨ first drop — dinees are here</div>
          <h1>small objects,<br/>big magic.</h1>
          <p className="tagline">tiny sculptural things for your desk, your shelf, your life. designed by hand, 3D-printed to order.</p>
          <div className="ctas">
            <Link className="button" to="/shop">Shop the dinees</Link>
          </div>
          <p className="coming-soon">🪴 functional planters coming soon</p>
        </div>
      </section>

      <section className="container">
        <h2>The first dinees</h2>
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
