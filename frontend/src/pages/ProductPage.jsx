import React, { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { api } from '../api.js'
import { useCart } from '../cart.jsx'

export default function ProductPage() {
  const { slug } = useParams()
  const [product, setProduct] = useState(null)
  const [err, setErr] = useState('')
  const { add } = useCart()
  const navigate = useNavigate()

  useEffect(() => {
    api.getProduct(slug).then(setProduct).catch(e => setErr(String(e)))
  }, [slug])

  if (err) return <div className="container page"><div className="notice">Not found: {err}</div><Link to="/shop">← back to shop</Link></div>
  if (!product) return <div className="loading">Loading…</div>

  return (
    <section className="container product-detail">
      <div className="img">
        {product.image_url_resolved && <img src={product.image_url_resolved} alt={product.name} />}
      </div>
      <div>
        <h1>{product.name}</h1>
        <div className="price">${Number(product.price).toFixed(2)}</div>
        <p>{product.description}</p>
        <div style={{display:'flex', gap:'0.8rem', marginTop:'1.5rem'}}>
          <button onClick={() => { add(product, 1); navigate('/cart') }}>Add to cart</button>
          <Link to="/shop" className="button ghost">← back to shop</Link>
        </div>
      </div>
    </section>
  )
}
