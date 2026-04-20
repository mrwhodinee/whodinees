import React from 'react'
import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <section className="hero">
      <div className="container">
        <div className="sparkles">✨ Whodinees Portraits</div>
        <h1>tiny figurines of your<br/>tiny best friend.</h1>
        <p className="tagline">
          From your photo, in plastic, bronze, silver, or gold. Custom 3D-printed pet portraits,
          hand-finished, built to last longer than a shelf.
        </p>
        <div className="ctas">
          <Link className="button" to="/portraits">Start your portrait →</Link>
        </div>
        <p className="coming-soon">$19 refundable deposit · 3 variants to choose from</p>
      </div>
    </section>
  )
}
