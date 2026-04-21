import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { api } from '../api.js'

const MATERIAL_LABEL = {
  plastic: 'Plastic',
  silver: 'Sterling Silver',
  gold_14k_yellow: '14K Yellow Gold',
  gold_14k_rose: '14K Rose Gold',
  gold_14k_white: '14K White Gold',
  gold_18k_yellow: '18K Yellow Gold',
  platinum: 'Platinum',
}

function PayForm({ portraitId, orderToken }) {
  const stripe = useStripe()
  const elements = useElements()
  const navigate = useNavigate()
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    if (!stripe || !elements) return
    setBusy(true); setErr('')
    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
      confirmParams: { return_url: `${window.location.origin}/portraits/${portraitId}/confirmation?order=${orderToken}` },
    })
    if (error) { setErr(error.message || 'Payment failed'); setBusy(false); return }
    if (paymentIntent && paymentIntent.status === 'succeeded') {
      navigate(`/portraits/${portraitId}/confirmation?order=${orderToken}`)
    } else { setBusy(false) }
  }

  return (
    <form onSubmit={onSubmit} className="checkout">
      <div className="stripe-box"><PaymentElement /></div>
      {err && <div className="notice">{err}</div>}
      <button disabled={!stripe || busy}>{busy ? 'Processing…' : 'Place order'}</button>
    </form>
  )
}

export default function PortraitCheckout() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [portrait, setPortrait] = useState(null)
  const [material, setMaterial] = useState('silver')
  const [priceBreakdown, setPriceBreakdown] = useState(null)
  const [loadingPrice, setLoadingPrice] = useState(false)
  const [shipping, setShipping] = useState({
    shipping_name: '', shipping_address1: '', shipping_address2: '',
    shipping_city: '', shipping_region: '', shipping_postcode: '', shipping_country: 'US',
  })
  const [stripePromise, setStripePromise] = useState(null)
  const [clientSecret, setClientSecret] = useState('')
  const [orderToken, setOrderToken] = useState('')
  const [step, setStep] = useState('pick') // pick -> pay
  const [err, setErr] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api.getPortrait(id).then(p => {
      setPortrait(p)
      if (!['approved', 'ordered'].includes(p.status)) {
        navigate(`/portraits/${id}`)
      }
    }).catch(e => setErr(String(e.message || e)))
  }, [id, navigate])

  // Load pricing when material changes
  useEffect(() => {
    if (!portrait) return
    setLoadingPrice(true)
    api.calculatePortraitPrice(id, material)
      .then(setPriceBreakdown)
      .catch(() => setPriceBreakdown(null))
      .finally(() => setLoadingPrice(false))
  }, [id, material, portrait])

  async function submit(e) {
    e.preventDefault()
    setSubmitting(true); setErr('')
    try {
      const resp = await api.createPortraitOrder(id, { material, ...shipping })
      setClientSecret(resp.client_secret)
      setOrderToken(resp.order.token)
      setStripePromise(loadStripe(resp.publishable_key))
      setStep('pay')
    } catch (e) { setErr(String(e.message || e)) }
    finally { setSubmitting(false) }
  }

  function setShipField(k, v) { setShipping(s => ({ ...s, [k]: v })) }

  if (err && !portrait) return <section className="container page"><h1>Error</h1><div className="notice">{err}</div></section>
  if (!portrait) return <section className="container page"><div className="loading">Loading…</div></section>

  if (step === 'pay') {
    return (
      <section className="container page" style={{maxWidth:640}}>
        <h1>Payment</h1>
        {stripePromise && clientSecret ? (
          <Elements stripe={stripePromise} options={{ clientSecret, appearance: { theme: 'stripe', variables: { colorPrimary: '#8a5cff' } } }}>
            <PayForm portraitId={id} orderToken={orderToken} />
          </Elements>
        ) : (
          <div className="loading">Preparing payment…</div>
        )}
      </section>
    )
  }

  return (
    <section className="container page">
      <h1>Order your portrait</h1>
      
      <div style={{display:'grid', gridTemplateColumns:'1fr 360px', gap:'2.5rem', alignItems:'start'}}>
        <form onSubmit={submit} className="checkout">
          <h2>Material</h2>
          <div className="material-grid" style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(140px, 1fr))', gap:'1rem', marginBottom:'2rem'}}>
            {Object.entries(MATERIAL_LABEL).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={material === key ? 'material-btn active' : 'material-btn'}
                onClick={() => setMaterial(key)}
              >
                {label}
              </button>
            ))}
          </div>

          <h2>Shipping</h2>
          <label>Name<input required value={shipping.shipping_name} onChange={e => setShipField('shipping_name', e.target.value)} /></label>
          <label>Address<input required value={shipping.shipping_address1} onChange={e => setShipField('shipping_address1', e.target.value)} /></label>
          <label>Apt/Suite (optional)<input value={shipping.shipping_address2} onChange={e => setShipField('shipping_address2', e.target.value)} /></label>
          <div className="row2">
            <label>City<input required value={shipping.shipping_city} onChange={e => setShipField('shipping_city', e.target.value)} /></label>
            <label>State/Region<input required value={shipping.shipping_region} onChange={e => setShipField('shipping_region', e.target.value)} /></label>
          </div>
          <div className="row2">
            <label>ZIP/Postal<input required value={shipping.shipping_postcode} onChange={e => setShipField('shipping_postcode', e.target.value)} /></label>
            <label>Country
              <select value={shipping.shipping_country} onChange={e => setShipField('shipping_country', e.target.value)}>
                <option value="US">United States</option>
                <option value="CA">Canada</option>
                <option value="GB">United Kingdom</option>
                <option value="AU">Australia</option>
              </select>
            </label>
          </div>

          {err && <div className="notice">{err}</div>}
          <button disabled={submitting || loadingPrice}>{submitting ? 'Processing…' : 'Continue to payment'}</button>
        </form>

        <div className="order-summary" style={{position:'sticky', top:'2rem'}}>
          <h3>Price Breakdown</h3>
          {loadingPrice && <div className="loading">Calculating…</div>}
          {!loadingPrice && priceBreakdown && (
            <div className="price-breakdown">
              <div className="breakdown-row">
                <span>Material weight:</span>
                <strong>{priceBreakdown.weight_grams}g</strong>
              </div>
              {priceBreakdown.spot_price_per_gram > 0 && (
                <div className="breakdown-row">
                  <span>{priceBreakdown.metal_name} spot price:</span>
                  <span>${priceBreakdown.spot_price_per_gram}/g (live)</span>
                </div>
              )}
              <div className="breakdown-row">
                <span>Material cost:</span>
                <span>${priceBreakdown.material_cost}</span>
              </div>
              <div style={{borderTop:'1px solid var(--border)', margin:'0.75rem 0'}}></div>
              <div className="breakdown-row">
                <span>Production & casting (Shapeways):</span>
                <span>${priceBreakdown.shapeways_cost}</span>
              </div>
              <div style={{borderTop:'1px solid var(--border)', margin:'0.75rem 0'}}></div>
              <div className="breakdown-row">
                <span>Design fee:</span>
                <span>${priceBreakdown.design_fee}</span>
              </div>
              <div className="breakdown-row">
                <span>AI model generation:</span>
                <span>${priceBreakdown.ai_processing_fee}</span>
              </div>
              <div className="breakdown-row">
                <span>Platform & processing:</span>
                <span>${priceBreakdown.platform_fee}</span>
              </div>
              <div style={{borderTop:'1px solid var(--border)', margin:'0.75rem 0'}}></div>
              <div className="breakdown-row total">
                <span>Total:</span>
                <strong>${priceBreakdown.total}</strong>
              </div>
              <p style={{fontSize:'0.85rem', color:'var(--ink-soft)', marginTop:'1rem', lineHeight:'1.4'}}>
                {material !== 'plastic' 
                  ? `Your price includes live ${priceBreakdown.metal_name} spot price on ${new Date().toLocaleDateString()}, Shapeways production and casting, AI model generation from your photo, and our platform fee. The metal value of your piece reflects today's market rate.`
                  : 'Your price includes Shapeways production, AI model generation from your photo, design work, and our platform fee.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
