import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { api } from '../api.js'

function PayForm({ portraitId }) {
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
      confirmParams: { return_url: `${window.location.origin}/portraits/${portraitId}` },
    })
    if (error) { setErr(error.message || 'Payment failed'); setBusy(false); return }
    if (paymentIntent && paymentIntent.status === 'succeeded') {
      navigate(`/portraits/${portraitId}`)
    } else { setBusy(false) }
  }

  return (
    <form onSubmit={onSubmit} className="checkout">
      <div className="stripe-box"><PaymentElement /></div>
      {err && <div className="notice">{err}</div>}
      <button disabled={!stripe || busy}>{busy ? 'Processing…' : 'Pay $19 deposit'}</button>
      <p style={{color:'var(--ink-soft)', fontSize:'0.85rem'}}>
        Test card: <code>4242 4242 4242 4242</code>, any future date, any CVC.
      </p>
    </form>
  )
}

export default function PortraitDeposit() {
  const { id } = useParams()
  const [portrait, setPortrait] = useState(null)
  const [stripePromise, setStripePromise] = useState(null)
  const [clientSecret, setClientSecret] = useState('')
  const [err, setErr] = useState('')

  useEffect(() => {
    (async () => {
      try {
        const p = await api.getPortrait(id)
        setPortrait(p)
        if (p.deposit_paid) return // already paid
        if (p.status === 'photo_rejected') return
        const resp = await api.startGeneration(id)
        setClientSecret(resp.client_secret)
        setStripePromise(loadStripe(resp.publishable_key))
      } catch (e) { setErr(String(e.message || e)) }
    })()
  }, [id])

  if (err) return <section className="container page"><h1>Oops</h1><div className="notice">{err}</div></section>
  if (!portrait) return <section className="container page"><div className="loading">Loading…</div></section>

  if (portrait.status === 'photo_rejected') {
    return (
      <section className="container page">
        <h1>Photo didn't make the cut</h1>
        <ul>{(portrait.photo_issues || []).map((i, k) => <li key={k}>{i}</li>)}</ul>
        <Link className="button" to="/portraits/upload">Try another photo →</Link>
      </section>
    )
  }

  if (portrait.deposit_paid) {
    return (
      <section className="container page">
        <h1>Deposit received</h1>
        <p>We're generating your 3 variants. This takes a few minutes.</p>
        <Link className="button" to={`/portraits/${id}`}>View progress →</Link>
      </section>
    )
  }

  return (
    <section className="container page" style={{maxWidth:640}}>
      <h1>Confirm your portrait</h1>
      <div className="summary">
        <div className="row"><span>Pet</span><span>{portrait.pet_name || portrait.pet_type}</span></div>
        <div className="row"><span>Photo quality</span><span>{portrait.photo_quality_score}/100</span></div>
        <div className="row total"><span>Deposit</span><span>$19.00</span></div>
      </div>
      <p style={{color:'var(--ink-soft)', fontSize:'0.9rem', margin:'1rem 0'}}>
        Your deposit covers generating 3 unique 3D variants. When you order a physical print,
        this $19 is credited toward your total. If none of the variants work, we'll refund it.
      </p>
      {stripePromise && clientSecret ? (
        <Elements stripe={stripePromise} options={{ clientSecret, appearance: { theme: 'stripe', variables: { colorPrimary: '#8a5cff' } } }}>
          <PayForm portraitId={id} />
        </Elements>
      ) : (
        <div className="loading">Preparing payment…</div>
      )}
    </section>
  )
}
