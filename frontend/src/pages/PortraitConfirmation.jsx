import React from 'react'
import { useParams, Link } from 'react-router-dom'

export default function PortraitConfirmation() {
  const { id } = useParams()
  return (
    <section className="container page" style={{maxWidth:640, textAlign:'center'}}>
      <div style={{fontSize:'3rem'}}>🎉</div>
      <h1>You're getting a figurine!</h1>
      <p>
        Thanks — we got your order. You'll get an email confirmation shortly, and another
        when your portrait ships. Production typically takes 2-3 weeks for plastic, 4-6 for metals.
      </p>
      <div className="ctas" style={{justifyContent:'center'}}>
        <Link className="button" to={`/portraits/${id}`}>Back to portrait</Link>
        <Link className="button-ghost" to="/shop">Browse the shop</Link>
      </div>
    </section>
  )
}
