import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api.js'

export default function OrderConfirmation() {
  const { token } = useParams()
  const [order, setOrder] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.getOrder(token).then(setOrder).catch(e => setErr(String(e.message || e)))
  }, [token])

  return (
    <section className="container page">
      <div className="success-hero">
        <div className="big">✨</div>
        <h1>Thanks for your order!</h1>
        <p style={{color:'var(--ink-soft)'}}>Small objects, big magic. We're on it.</p>
      </div>
      {err && <div className="notice">Couldn't load order: {err}</div>}
      {!err && !order && <div className="loading">Loading order…</div>}
      {order && (
        <div style={{maxWidth:560, margin:'0 auto'}}>
          <h2>Order details</h2>
          <p><strong>Status:</strong> {order.status}</p>
          <table className="cart-table">
            <thead><tr><th>Item</th><th>Qty</th><th style={{textAlign:'right'}}>Line</th></tr></thead>
            <tbody>
              {order.items.map((it, idx) => (
                <tr key={idx}>
                  <td>{it.product.name}</td>
                  <td>{it.quantity}</td>
                  <td style={{textAlign:'right'}}>${Number(it.line_total).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="summary">
            <div className="row"><span>Subtotal</span><span>${Number(order.subtotal).toFixed(2)}</span></div>
            <div className="row"><span>Shipping</span><span>${Number(order.shipping_cost).toFixed(2)}</span></div>
            <div className="row total"><span>Total</span><span>${Number(order.total).toFixed(2)} {order.currency.toUpperCase()}</span></div>
          </div>
          <p style={{marginTop:'1.5rem'}}>We'll email <strong>{order.customer_email}</strong> with updates.</p>
          <Link to="/shop" className="button ghost">Keep shopping →</Link>
        </div>
      )}
    </section>
  )
}
