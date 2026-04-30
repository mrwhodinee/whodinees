import React, { useEffect } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { trackOrderCompleted } from '../analytics.js'

export default function PortraitConfirmation() {
  const { token } = useParams()
  const [searchParams] = useSearchParams()
  
  useEffect(() => {
    // Track order completion once
    // Order details would need to be fetched from API or passed via state
    // For now, just track that purchase completed
    const orderToken = searchParams.get('order')
    if (orderToken) {
      // Note: In production, fetch order details from API to get accurate price/material
      // For now, tracking basic conversion
      trackOrderCompleted(orderToken, 'unknown', 0, 0, 0)
    }
  }, [searchParams])
  
  return (
    <section className="container page" style={{maxWidth:640, textAlign:'center'}}>
      <div style={{fontSize:'3rem'}}>🎉</div>
      <h1>You're getting a figurine!</h1>
      <p>
        Thanks — we got your order. You'll get an email confirmation shortly, and another
        when your portrait ships. Production typically takes 2-3 weeks for plastic, 4-6 for metals.
      </p>
      <div className="ctas" style={{justifyContent:'center'}}>
        <Link className="button" to={`/portraits/${token}`}>Back to portrait</Link>
        <Link className="button-ghost" to="/shop">Browse the shop</Link>
      </div>
    </section>
  )
}
