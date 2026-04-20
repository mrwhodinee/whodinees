import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'

const MIN_SHORTEST_SIDE = 1400
const MAX_BYTES = 15 * 1024 * 1024
const MIN_BYTES = 100 * 1024

export default function PortraitUpload() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ customer_email: '', pet_name: '', pet_type: 'dog' })
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [clientIssues, setClientIssues] = useState([])
  const [serverIssues, setServerIssues] = useState([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const inputRef = useRef(null)

  function setField(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function onFileChange(e) {
    setClientIssues([])
    setServerIssues([])
    setErr('')
    const f = e.target.files?.[0]
    if (!f) { setFile(null); setPreviewUrl(''); return }
    const issues = []
    if (f.size > MAX_BYTES) issues.push(`File is too large (${(f.size/1024/1024).toFixed(1)}MB, max 15MB)`)
    if (f.size < MIN_BYTES) issues.push(`File is too small (${(f.size/1024).toFixed(0)}KB) — we need a high-resolution photo (min 100KB)`)

    const url = URL.createObjectURL(f)
    const dims = await new Promise(res => {
      const img = new Image()
      img.onload = () => res({ w: img.naturalWidth, h: img.naturalHeight })
      img.onerror = () => res({ w: 0, h: 0 })
      img.src = url
    })
    if (dims.w && Math.min(dims.w, dims.h) < MIN_SHORTEST_SIDE) {
      issues.push(`Image is ${dims.w}×${dims.h}. Need at least ${MIN_SHORTEST_SIDE}px on the shortest side.`)
    }
    setClientIssues(issues)
    setFile(f)
    setPreviewUrl(url)
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!file) { setErr('Please choose a photo'); return }
    if (clientIssues.length) { setErr('Please fix the photo issues first'); return }
    setBusy(true); setErr('')
    try {
      const fd = new FormData()
      fd.append('customer_email', form.customer_email)
      fd.append('pet_name', form.pet_name)
      fd.append('pet_type', form.pet_type)
      fd.append('photo', file)
      const resp = await api.createPortrait(fd)
      if (!resp.passed) {
        setServerIssues(resp.issues || [])
        setBusy(false)
        return
      }
      navigate(`/portraits/${resp.portrait.id}/deposit`)
    } catch (e) {
      setErr(String(e.message || e))
      setBusy(false)
    }
  }

  return (
    <section className="container page">
      <h1>Upload a photo</h1>
      <p style={{color:'var(--ink-soft)', maxWidth:'52ch'}}>
        <strong>Premium quality required:</strong> Sharp focus, good lighting, face clearly visible, eyes open, single subject. Minimum 1400px shortest side. We reject blurry or low-res photos.
      </p>

      <form className="checkout" onSubmit={onSubmit} style={{maxWidth:'560px'}}>
        <label>Your email<input required type="email" value={form.customer_email} onChange={e => setField('customer_email', e.target.value)} /></label>
        <div className="row2">
          <label>Pet's name<input value={form.pet_name} onChange={e => setField('pet_name', e.target.value)} placeholder="Optional" /></label>
          <label>Type
            <select value={form.pet_type} onChange={e => setField('pet_type', e.target.value)}>
              <option value="dog">Dog</option>
              <option value="cat">Cat</option>
              <option value="other">Other</option>
            </select>
          </label>
        </div>

        <label>Photo
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={onFileChange}
            required
          />
        </label>

        {previewUrl && (
          <div className="photo-preview" style={{margin:'0.5rem 0'}}>
            <img src={previewUrl} alt="preview" style={{maxWidth:'100%', maxHeight:320, borderRadius:12}} />
          </div>
        )}

        {clientIssues.length > 0 && (
          <div className="notice">
            <strong>Photo needs work:</strong>
            <ul>{clientIssues.map((i, k) => <li key={k}>{i}</li>)}</ul>
          </div>
        )}
        {serverIssues.length > 0 && (
          <div className="notice">
            <strong>We ran some quality checks and found:</strong>
            <ul>{serverIssues.map((i, k) => <li key={k}>{i}</li>)}</ul>
            <p>Try a sharper, higher-resolution photo.</p>
          </div>
        )}
        {err && <div className="notice">{err}</div>}

        <button disabled={busy || !file || clientIssues.length > 0}>
          {busy ? 'Uploading…' : 'Continue to deposit →'}
        </button>
        <p style={{color:'var(--ink-soft)', fontSize:'0.85rem'}}>
          Next step: a $19 deposit, which we use to generate 3 unique 3D variants. You pick your favorite.
        </p>
      </form>
    </section>
  )
}
