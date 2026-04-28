import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import * as Sentry from '@sentry/react'
import App from './App.jsx'
import { CartProvider } from './cart.jsx'
import './styles.css'

// Initialize Sentry for error monitoring
if (import.meta.env.PROD) {
  Sentry.init({
    dsn: 'https://449044596d856269142fffc5a5b544c7@o4511297467842560.ingest.us.sentry.io/4511297532592128',
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions
    // Session Replay
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors
    environment: 'production',
  })
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Sentry.ErrorBoundary fallback={<div style={{padding: '2rem', textAlign: 'center'}}>Something went wrong. Please refresh the page.</div>}>
      <BrowserRouter>
        <CartProvider>
          <App />
        </CartProvider>
      </BrowserRouter>
    </Sentry.ErrorBoundary>
  </React.StrictMode>
)
