import React, { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { api } from '../api.js'

const MATERIAL_LABEL = {
  plastic:  'Plastic',
  bronze:   'Bronze',
  silver:   'Sterling Silver',
  gold_14k: '14K Gold',
  platinum: 'Platinum',
}
const SIZES = [40, 60, 80, 100]

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
  const [pricing, setPricing] = useState(null)
  const [material, setMaterial] = useState('plastic')
  const [sizeMm, setSizeMm] = useState(60)
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
    api.getPortraitPricing().then(setPricing).catch(() => setPricing({}))
  }, [id, navigate])

  const currentPrice = useMemo(() => {
    if (!pricing || !pricing.materials) return null
    return pricing.materials[material]?.by_size?.[String(sizeMm)] || null
  }, [pricing, material, sizeMm])

  async function submit(e) {
    e.preventDefault()
    setSubmitting(true); setErr('')
    try {
      const resp = await api.createPortraitOrder(id, { material, size_mm: sizeMm, ...shipping })
      setClientSecret(resp.client_secret)
      setOrderToken(resp.order.token)
      setStripePromise(loadStripe(resp.publishable_key))
      setStep('pay')
    } catch (e) { setErr(String(e.message || e)) }
    finally { setSubmitting(false) }
  }

  function setShipField(k, v) { setShipping(s => ({ ...s, [k]: v })) }

  if (err) return <section className="container page"><h1>Error</h1><div className="notice">{err}</div></section>
  if (!portrait || !pricing) return <section className="container page"><div className="loading">Loading…</div></section>

  return (
    <section className="container page" style={{display:'grid', gridTemplateColumns:'1fr minmax(260px, 360px)', gap:'2.5rem'}}>
      <div>
        <h1>Choose your material</h1>
        {step === 'pick' && (
          <form onSubmit={submit} className="checkout">
            <fieldset style={{border:'none', padding:0, margin:'0 0 1rem'}}>
              <legend style={{fontWeight:600, marginBottom:'0.5rem'}}>Material</legend>
              <div className="material-picker">
                {Object.entries(pricing.materials || {}).map(([mat, info]) => {
                  const price = info.by_size?.[String(sizeMm)]?.retail
                  return (
                    <label key={mat} className={`material-option ${material === mat ? 'selected' : ''}`}>
                      <input type="radio" name="material" value={mat} checked={material === mat} onChange={() => setMaterial(mat)} />
                      <div>
                        <strong>{MATERIAL_LABEL[mat] || mat}</strong>
                        <div className="price">${price}</div>
                      </div>
                    </label>
                  )
                })}
              </div>
            </fieldset>

            <fieldset style={{border:'none', padding:0, margin:'0 0 1rem'}}>
              <legend style={{fontWeight:600, marginBottom:'0.5rem'}}>Size (longest dimension)</legend>
              <div className="size-picker">
                {SIZES.map(sz => (
                  <label key={sz} className={`size-option ${sizeMm === sz ? 'selected' : ''}`}>
                    <input type="radio" name="size" value={sz} checked={sizeMm === sz} onChange={() => setSizeMm(sz)} />
                    <strong>{sz}mm</strong>
                    <small>{sz === 40 ? 'keychain' : sz === 60 ? 'desk' : sz === 80 ? 'shelf' : 'statement'}</small>
                  </label>
                ))}
              </div>
            </fieldset>

            <h2 style={{fontSize:'1.1rem', marginTop:'1rem'}}>Shipping</h2>
            <label>Full name<input required value={shipping.shipping_name} onChange={e => setShipField('shipping_name', e.target.value)} /></label>
            <label>Address line 1<input required value={shipping.shipping_address1} onChange={e => setShipField('shipping_address1', e.target.value)} /></label>
            <label>Address line 2 (optional)<input value={shipping.shipping_address2} onChange={e => setShipField('shipping_address2', e.target.value)} /></label>
            <div className="row3">
              <label>City<input required value={shipping.shipping_city} onChange={e => setShipField('shipping_city', e.target.value)} /></label>
              <label>Region<input value={shipping.shipping_region} onChange={e => setShipField('shipping_region', e.target.value)} /></label>
              <label>Postcode<input required value={shipping.shipping_postcode} onChange={e => setShipField('shipping_postcode', e.target.value)} /></label>
            </div>
            <label>Country (2-letter)<input required maxLength={2} value={shipping.shipping_country} onChange={e => setShipField('shipping_country', e.target.value.toUpperCase())} /></label>

            <button disabled={submitting}>{submitting ? 'Preparing payment…' : 'Continue to payment →'}</button>
          </form>
        )}

        {step === 'pay' && stripePromise && clientSecret && (
          <Elements stripe={stripePromise} options={{ clientSecret, appearance: { theme: 'stripe', variables: { colorPrimary: '#8a5cff' } } }}>
            <PayForm portraitId={id} orderToken={orderToken} />
          </Elements>
        )}
      </div>

      <aside>
        <h2 style={{fontSize:'1.2rem'}}>Price breakdown</h2>
        {currentPrice ? (
          <div className="summary">
            <div className="row"><span>Design fee</span><span>${currentPrice.design_fee}</span></div>
            <div className="row"><span>Material ({currentPrice.estimated_weight_g}g est.)</span><span>${currentPrice.metal_cost}</span></div>
            <div className="row"><span>Printing & handling</span><span>${currentPrice.shapeways_cost_with_handling}</span></div>
            <div className="row total"><span>Total</span><span>${currentPrice.retail}</span></div>
            <p style={{color:'var(--ink-soft)', fontSize:'0.8rem', marginTop:'0.6rem'}}>
              Final price confirmed at checkout. Metal weight is an estimate; we'll quote exactly from the 3D model.
            </p>
          </div>
        ) : <div className="loading">Pricing…</div>}
      </aside>
    </section>
  )
}
