import React from 'react'
import { Link } from 'react-router-dom'
import { useCart } from '../cart.jsx'

export default function Cart() {
  const { items, setQty, remove, subtotal, clear } = useCart()
  if (items.length === 0) {
    return (
      <section className="container page">
        <h1>Your cart</h1>
        <div className="empty">Cart's empty. <Link to="/shop">Find a dinee →</Link></div>
      </section>
    )
  }
  const shipping = 6
  const total = subtotal + shipping
  return (
    <section className="container page">
      <h1>Your cart</h1>
      <table className="cart-table">
        <thead><tr><th>Item</th><th>Price</th><th>Qty</th><th style={{textAlign:'right'}}>Line</th></tr></thead>
        <tbody>
          {items.map(i => (
            <tr key={i.slug}>
              <td>
                <Link to={`/shop/${i.slug}`} style={{fontWeight:600, color:'var(--ink)'}}>{i.name}</Link>{' '}
                <button onClick={() => remove(i.slug)} className="ghost" style={{marginLeft:'0.6rem', padding:'0.1rem 0.6rem', fontSize:'0.8rem'}}>remove</button>
              </td>
              <td>${i.price.toFixed(2)}</td>
              <td>
                <span className="qty">
                  <button onClick={() => setQty(i.slug, i.quantity - 1)} disabled={i.quantity <= 1}>−</button>
                  <span>{i.quantity}</span>
                  <button onClick={() => setQty(i.slug, i.quantity + 1)}>+</button>
                </span>
              </td>
              <td style={{textAlign:'right'}}>${(i.price * i.quantity).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="summary">
        <div className="row"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
        <div className="row"><span>Shipping</span><span>${shipping.toFixed(2)}</span></div>
        <div className="row total"><span>Total</span><span>${total.toFixed(2)}</span></div>
      </div>
      <div style={{display:'flex', gap:'0.8rem', marginTop:'1.5rem'}}>
        <Link className="button" to="/checkout">Checkout →</Link>
        <button className="ghost" onClick={clear}>Clear cart</button>
      </div>
    </section>
  )
}
