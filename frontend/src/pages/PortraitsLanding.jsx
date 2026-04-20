import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'

const MATERIAL_LABEL = {
  plastic:  'Plastic',
  bronze:   'Bronze',
  silver:   'Sterling Silver',
  gold_14k: '14K Gold',
  platinum: 'Platinum',
}

export default function PortraitsLanding() {
  const [pricing, setPricing] = useState(null)
  useEffect(() => { api.getPortraitPricing().then(setPricing).catch(() => setPricing({})) }, [])

  return (
    <>
      <section className="hero">
        <div className="container">
          <div className="sparkles">✨ Whodinees Portraits</div>
          <h1>tiny figurines of your<br/>tiny best friend.</h1>
          <p className="tagline">
            From your photo, in plastic, bronze, silver, or gold. Custom 3D-printed pet portraits,
            hand-finished, built to last longer than a shelf.
          </p>
          <div className="ctas">
            <Link className="button" to="/portraits/upload">Start your portrait →</Link>
            <Link className="button-ghost" to="/shop">Or browse the sculptural shop</Link>
          </div>
          <p className="coming-soon">$19 refundable deposit · 3 variants to choose from</p>
        </div>
      </section>

      <section className="container">
        <h2>How it works</h2>
        <div className="grid" style={{gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))'}}>
          <Step n="1" title="Upload a photo">A clear, well-lit shot of your pet — face visible, in focus. We'll check it's sharp enough.</Step>
          <Step n="2" title="Pay the $19 deposit">We use it to generate three unique 3D variants from your photo. Takes ~5 minutes.</Step>
          <Step n="3" title="Pick your favorite">Rotate each variant in 3D. Approve the one that nails them.</Step>
          <Step n="4" title="Choose your material">Plastic, bronze, silver, 14K gold, or platinum. We print, finish, and ship.</Step>
        </div>
      </section>

      <section className="container" style={{marginTop:'3rem'}}>
        <h2>Materials & pricing</h2>
        <p style={{color:'var(--ink-soft)'}}>
          Prices are starting retail for a small (40mm) figurine. Metal prices update daily — final quote at checkout.
        </p>
        {!pricing && <div className="loading">Loading pricing…</div>}
        {pricing && pricing.materials && (
          <div className="grid" style={{gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))', marginTop:'1rem'}}>
            {Object.entries(pricing.materials).map(([mat, info]) => {
              const startPrice = info.by_size?.['40']?.retail || info.design_fee
              return (
                <div key={mat} className="material-card">
                  <h3>{MATERIAL_LABEL[mat] || mat}</h3>
                  <div className="price-from">from <strong>${startPrice}</strong></div>
                  <div className="size-range" style={{color:'var(--ink-soft)', fontSize:'0.85rem'}}>
                    40–100mm · design fee ${info.design_fee}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>

      <section className="container" style={{margin:'3rem 0'}}>
        <div className="ctas" style={{justifyContent:'center'}}>
          <Link className="button" to="/portraits/upload">Start your portrait →</Link>
        </div>
      </section>
    </>
  )
}

function Step({ n, title, children }) {
  return (
    <div className="step-card">
      <div className="step-num">{n}</div>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  )
}
