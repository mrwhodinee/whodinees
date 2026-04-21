import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import EnhancedShowcase from '../components/EnhancedShowcase'

const MATERIAL_LABEL = {
  plastic: 'Plastic',
  silver: 'Sterling Silver',
  gold_14k_yellow: '14K Yellow Gold',
  gold_14k_rose: '14K Rose Gold',
  gold_14k_white: '14K White Gold',
  gold_18k_yellow: '18K Yellow Gold',
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
            From your photo, in plastic or precious metals. Custom 3D-printed pet portraits with transparent spot pricing.
          </p>
          <div className="ctas">
            <Link className="button" to="/portraits/upload">Start your portrait →</Link>
          </div>
          <p className="coming-soon">$19 non-refundable deposit · You keep the digital files</p>
        </div>
      </section>

      <section className="container" style={{marginTop:'3rem'}}>
        <h2>Your pet. Immortalized in precious metal. Priced at today's market rate — forever.</h2>
        <p style={{color:'var(--ink-soft)', marginBottom:'2rem', fontSize:'18px', maxWidth:'800px', margin:'0 auto 2rem'}}>From photo to 3D model in minutes. See the transformation yourself.</p>
        <div className="showcase-grid" style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(320px, 1fr))', gap:'2rem'}}>
          <EnhancedShowcase
            photo="/static/showcase/golden-retriever.jpg" 
            model="/static/showcase/golden-retriever_3d_preview.png"
            glbUrl="/static/showcase/golden-retriever.glb"
            label="Golden Retriever"
            pricing={pricing}
          />
          <EnhancedShowcase
            photo="/static/showcase/tabby-cat.jpg" 
            model="/static/showcase/tabby-cat_3d_preview.png"
            glbUrl="/static/showcase/tabby-cat.glb"
            label="Tabby Cat"
            pricing={pricing}
          />
          <EnhancedShowcase
            photo="/static/showcase/corgi.jpg" 
            model="/static/showcase/corgi_3d_preview.png"
            glbUrl="/static/showcase/corgi.glb"
            label="Corgi"
            pricing={pricing}
          />
        </div>
      </section>

      <section className="container">
        <h2>How it works</h2>
        <div className="grid" style={{gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))'}}>
          <Step n="1" title="Upload a premium photo">Sharp, well-lit, face clearly visible. We reject blurry or low-res photos — 8/10+ quality only.</Step>
          <Step n="2" title="Pay $19 deposit">Non-refundable (covers AI cost). We generate your custom 3D model from your photos and hold it securely until your order is complete.</Step>
          <Step n="3" title="Review & approve">View your 3D models, pick your favorite. Decide if you want a physical print.</Step>
          <Step n="4" title="Choose material & order">Plastic, silver, 14K/18K gold, or platinum. Live spot pricing + transparent breakdown.</Step>
        </div>
      </section>

      <section className="container" style={{marginTop:'3rem'}}>
        <h2>Materials & pricing</h2>
        <p style={{color:'var(--ink-soft)'}}>
          Live spot prices for precious metals. Final price calculated from your actual 3D model at checkout.
        </p>
        {!pricing && <div className="loading">Loading pricing…</div>}
        {pricing && pricing.materials && (
          <div className="grid" style={{gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))', marginTop:'1rem'}}>
            {Object.entries(pricing.materials).map(([mat, info]) => (
              <div key={mat} className="material-card">
                <h3>{MATERIAL_LABEL[mat] || mat}</h3>
                {info.spot_price_per_gram > 0 && (
                  <div style={{fontSize:'0.85rem', color:'var(--ink-soft)', marginBottom:'0.5rem'}}>
                    ${info.spot_price_per_gram}/g (live)
                  </div>
                )}
                <div className="price-from">from <strong>${info.typical_total}</strong></div>
                <div className="size-range" style={{color:'var(--ink-soft)', fontSize:'0.85rem'}}>
                  design fee ${info.design_fee}
                </div>
              </div>
            ))}
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


