import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { api } from '../api.js'
import { useCart } from '../cart.jsx'

function PayForm({ orderToken }) {
  const stripe = useStripe()
  const elements = useElements()
  const navigate = useNavigate()
  const { clear } = useCart()
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    if (!stripe || !elements) return
    setBusy(true); setErr('')
    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
      confirmParams: { return_url: `${window.location.origin}/order/${orderToken}` },
    })
    if (error) {
      setErr(error.message || 'Payment failed')
      setBusy(false)
      return
    }
    if (paymentIntent && paymentIntent.status === 'succeeded') {
      clear()
      navigate(`/order/${orderToken}`)
    } else {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="checkout">
      <div className="stripe-box"><PaymentElement /></div>
      {err && <div className="notice">{err}</div>}
      <button disabled={!stripe || busy}>{busy ? 'Processing…' : 'Pay now'}</button>
      <p style={{color:'var(--ink-soft)', fontSize:'0.85rem'}}>
        Use test card <code>4242 4242 4242 4242</code>, any future date, any CVC.
      </p>
    </form>
  )
}

export default function Checkout() {
  const { items, subtotal } = useCart()
  const [step, setStep] = useState('details') // details -> pay
  const [form, setForm] = useState({
    customer_name: '', customer_email: '',
    shipping_line1: '', shipping_line2: '',
    shipping_city: '', shipping_state: '', shipping_postal_code: '',
    shipping_country: 'US',
  })
  const [stripePromise, setStripePromise] = useState(null)
  const [clientSecret, setClientSecret] = useState('')
  const [orderToken, setOrderToken] = useState('')
  const [err, setErr] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const shipping = 6
  const total = subtotal + shipping

  function setField(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function startPayment(e) {
    e.preventDefault()
    if (items.length === 0) return
    setSubmitting(true); setErr('')
    try {
      const payload = {
        ...form,
        items: items.map(i => ({ product_slug: i.slug, quantity: i.quantity })),
      }
      const resp = await api.createOrder(payload)
      setClientSecret(resp.client_secret)
      setOrderToken(resp.order_token)
      setStripePromise(loadStripe(resp.publishable_key))
      setStep('pay')
    } catch (e) {
      setErr(String(e.message || e))
    } finally {
      setSubmitting(false)
    }
  }

  if (items.length === 0) {
    return (
      <section className="container page">
        <h1>Checkout</h1>
        <div className="empty">Cart's empty. <Link to="/shop">Shop dinees →</Link></div>
      </section>
    )
  }

  return (
    <section className="container page" style={{display:'grid', gridTemplateColumns:'1fr minmax(260px, 340px)', gap:'2.5rem'}}>
      <div>
        <h1>Checkout</h1>
        {step === 'details' && (
          <form className="checkout" onSubmit={startPayment}>
            <div className="row2">
              <label>Full name<input required value={form.customer_name} onChange={e => setField('customer_name', e.target.value)} /></label>
              <label>Email<input required type="email" value={form.customer_email} onChange={e => setField('customer_email', e.target.value)} /></label>
            </div>
            <label>Address line 1<input required value={form.shipping_line1} onChange={e => setField('shipping_line1', e.target.value)} /></label>
            <label>Address line 2 (optional)<input value={form.shipping_line2} onChange={e => setField('shipping_line2', e.target.value)} /></label>
            <div className="row3">
              <label>City<input required value={form.shipping_city} onChange={e => setField('shipping_city', e.target.value)} /></label>
              <label>State/Region<input value={form.shipping_state} onChange={e => setField('shipping_state', e.target.value)} /></label>
              <label>Postal code<input required value={form.shipping_postal_code} onChange={e => setField('shipping_postal_code', e.target.value)} /></label>
            </div>
            <label>Country (2-letter)<input required maxLength={2} value={form.shipping_country} onChange={e => setField('shipping_country', e.target.value.toUpperCase())} /></label>
            {err && <div className="notice">{err}</div>}
            <button disabled={submitting}>{submitting ? 'Preparing…' : 'Continue to payment →'}</button>
          </form>
        )}
        {step === 'pay' && stripePromise && clientSecret && (
          <Elements stripe={stripePromise} options={{ clientSecret, appearance: { theme: 'stripe', variables: { colorPrimary: '#8a5cff' } } }}>
            <PayForm orderToken={orderToken} />
          </Elements>
        )}
      </div>
      <aside>
        <h2 style={{fontSize:'1.2rem'}}>Order summary</h2>
        <div className="summary">
          {items.map(i => (
            <div className="row" key={i.slug}>
              <span>{i.quantity} × {i.name}</span>
              <span>${(i.price * i.quantity).toFixed(2)}</span>
            </div>
          ))}
          <div className="row"><span>Shipping</span><span>${shipping.toFixed(2)}</span></div>
          <div className="row total"><span>Total</span><span>${total.toFixed(2)}</span></div>
        </div>
      </aside>
    </section>
  )
}
