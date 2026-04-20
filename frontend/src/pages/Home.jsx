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
          <div className="sparkles">✨ new — dinees are here</div>
          <h1>small objects,<br/>big magic.</h1>
          <p className="tagline">hand-designed, AI-dreamt, 3D-printed to order.</p>
          <div className="ctas">
            <Link className="button" to="/shop">Shop the dinees</Link>
            <Link className="button ghost" to="/shop">See the collection</Link>
          </div>
        </div>
      </section>

      <section className="container">
        <h2>Featured</h2>
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
