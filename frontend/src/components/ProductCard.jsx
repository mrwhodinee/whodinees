import React from 'react'
import { Link } from 'react-router-dom'

export default function ProductCard({ product }) {
  return (
    <Link to={`/shop/${product.slug}`} className="card">
      <div className="image">
        {product.image_url_resolved
          ? <img src={product.image_url_resolved} alt={product.name} loading="lazy" />
          : <span style={{color:'#fff', fontWeight:700, fontSize:'1.2rem'}}>{product.name}</span>}
      </div>
      <div className="body">
        <h3>{product.name}</h3>
        <div className="price">${Number(product.price).toFixed(2)}</div>
      </div>
    </Link>
  )
}
