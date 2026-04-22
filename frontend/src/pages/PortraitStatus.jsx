import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../api.js'

// Lazy-load @google/model-viewer from CDN — no npm install needed.
function ensureModelViewer() {
  if (typeof window === 'undefined') return
  if (window.__modelViewerLoaded) return
  const s = document.createElement('script')
  s.type = 'module'
  s.src = 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js'
  document.head.appendChild(s)
  window.__modelViewerLoaded = true
}

function VariantCard({ variant, index, selected, onSelect, onPick, disabled }) {
  const status = (variant.status || '').toUpperCase()
  const succeeded = status === 'SUCCEEDED' || status === 'SUCCESS' || status === 'COMPLETED'
  const failed = ['FAILED','CANCELED','EXPIRED','ERROR'].includes(status)
  const progress = variant.progress || 0

  return (
    <div className={`variant-card ${selected ? 'selected' : ''}`}>
      <div className="variant-header">
        <strong>Your Model</strong>
        <span className="variant-status">{status || 'PENDING'}</span>
      </div>
      <div className="variant-preview">
        {succeeded && variant.glb_url ? (
          <model-viewer
            src={variant.glb_url}
            alt={`Variant ${index + 1}`}
            camera-controls
            auto-rotate
            shadow-intensity="0.8"
            style={{ width: '100%', height: '240px', background: '#f4f0ff', borderRadius: 12 }}
          />
        ) : succeeded && variant.preview_url ? (
          <img src={variant.preview_url} alt="" style={{width:'100%', borderRadius:12}} />
        ) : failed ? (
          <div className="variant-fail">Generation failed</div>
        ) : (
          <div className="variant-progress">
            <div className="spinner" />
            <div>Generating… {progress}%</div>
          </div>
        )}
      </div>
      {succeeded && (
        <button
          onClick={() => onPick(variant.task_id)}
          disabled={disabled}
          className={selected ? 'selected' : ''}
        >
          {selected ? '✓ Ready to order' : 'Select this model'}
        </button>
      )}
    </div>
  )
}

export default function PortraitStatus() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [portrait, setPortrait] = useState(null)
  const [err, setErr] = useState('')
  const [approving, setApproving] = useState(false)
  const [selectedTaskId, setSelectedTaskId] = useState('')
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false)

  useEffect(() => { ensureModelViewer() }, [])
  
  useEffect(() => {
    // Check if redirected from successful payment
    const params = new URLSearchParams(window.location.search)
    if (params.get('payment') === 'success') {
      setShowPaymentSuccess(true)
      // Clear the URL parameter
      window.history.replaceState({}, '', window.location.pathname)
      // Hide message after 5 seconds
      setTimeout(() => setShowPaymentSuccess(false), 5000)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function tick() {
      try {
        const p = await api.getPortrait(id)
        if (cancelled) return
        setPortrait(p)
        if (p.selected_variant_task_id) setSelectedTaskId(p.selected_variant_task_id)
      } catch (e) { setErr(String(e.message || e)) }
    }
    tick()
    const int = setInterval(tick, 8000)
    return () => { cancelled = true; clearInterval(int) }
  }, [id])

  async function pick(taskId) {
    setSelectedTaskId(taskId)
  }

  async function approve() {
    if (!selectedTaskId) return
    setApproving(true); setErr('')
    try {
      await api.approveVariant(id, selectedTaskId)
      navigate(`/portraits/${id}/checkout`)
    } catch (e) { setErr(String(e.message || e)); setApproving(false) }
  }

  if (err) return <section className="container page"><h1>Error</h1><div className="notice">{err}</div></section>
  if (!portrait) return <section className="container page"><div className="loading">Loading…</div></section>

  const variants = portrait.meshy_variants || []
  const status = portrait.status

  return (
    <section className="container page">
      {showPaymentSuccess && (
        <div style={{
          background: '#4CAF50',
          color: 'white',
          padding: '1rem 1.5rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          fontWeight: '600',
          textAlign: 'center'
        }}>
          ✓ Payment successful! Your 3D model is being generated now...
        </div>
      )}
      <h1>Your portrait</h1>
      <p style={{color:'var(--ink-soft)'}}>
        {status === 'deposit_pending' && 'Your photo passed quality review! Pay the $19 deposit to generate your 3D model.'}
        {status === 'generating' && (
          <>
            <strong style={{color:'var(--accent)'}}>Generating your 3D model...</strong><br/>
            This usually takes 3-5 minutes. You can leave and come back — we'll email you when it's ready.<br/>
            <span style={{fontSize:'0.85rem'}}>Refresh this page to check progress, or we'll notify you via email.</span>
          </>
        )}
        {status === 'awaiting_approval' && 'Your model is ready! Review it below — you can rotate it in 3D.'}
        {status === 'approved' && 'Approved! Choose a material and size →'}
        {status === 'ordered' && 'Order placed. Check your email.'}
      </p>

      {status === 'deposit_pending' && (
        <Link className="button" to={`/portraits/${id}/deposit`}>Pay $19 deposit →</Link>
      )}
      
      {status === 'generating' && variants.length === 0 && (
        <div style={{
          background: 'var(--accent-soft)',
          padding: '1.5rem',
          borderRadius: '12px',
          marginTop: '1rem',
          textAlign: 'center'
        }}>
          <div className="loading" style={{margin: '0 auto 1rem'}}>Processing...</div>
          <p style={{margin: 0, color: 'var(--ink-soft)', fontSize: '0.9rem'}}>
            Our AI is analyzing your photo and building a 3D model.<br/>
            This page will update automatically when ready.
          </p>
        </div>
      )}

      {variants.length > 0 && (
        <div className="variant-grid">
          {variants.map((v, i) => (
            <VariantCard
              key={v.task_id || i}
              variant={v}
              index={i}
              selected={selectedTaskId === v.task_id}
              onSelect={() => pick(v.task_id)}
              onPick={pick}
              disabled={status === 'ordered'}
            />
          ))}
        </div>
      )}

      {(status === 'awaiting_approval' || status === 'approved') && selectedTaskId && status !== 'approved' && (
        <div style={{marginTop:'1.5rem'}}>
          <button onClick={approve} disabled={approving}>
            {approving ? 'Confirming…' : 'Confirm & choose material →'}
          </button>
        </div>
      )}

      {status === 'approved' && (
        <div style={{marginTop:'1.5rem'}}>
          <Link className="button" to={`/portraits/${id}/checkout`}>Choose material & order →</Link>
        </div>
      )}
    </section>
  )
}
