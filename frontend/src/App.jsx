import React from 'react'
import { Routes, Route, Link, NavLink } from 'react-router-dom'
import Logo from './Logo.jsx'
import { useCart } from './cart.jsx'
import Home from './pages/Home.jsx'
import Shop from './pages/Shop.jsx'
import ProductPage from './pages/ProductPage.jsx'
import Cart from './pages/Cart.jsx'
import Checkout from './pages/Checkout.jsx'
import OrderConfirmation from './pages/OrderConfirmation.jsx'
import PortraitsLanding from './pages/PortraitsLanding.jsx'
import PortraitUpload from './pages/PortraitUpload.jsx'
import PortraitDeposit from './pages/PortraitDeposit.jsx'
import PortraitStatus from './pages/PortraitStatus.jsx'
import PortraitCheckout from './pages/PortraitCheckout.jsx'
import PortraitConfirmation from './pages/PortraitConfirmation.jsx'

function Header() {
  const { count } = useCart()
  return (
    <header className="site-header">
      <div className="container row">
        <Link to="/" className="brand" aria-label="Whodinees home">
          <Logo size={36} />
          <span>Whodinees</span>
        </Link>
        <nav className="nav">
          <NavLink to="/portraits">How it works</NavLink>
        </nav>
      </div>
    </header>
  )
}

function Footer() {
  return (
    <footer className="footer">
      <div className="container row">
        <div>
          © {new Date().getFullYear()} Whodinees · <em>tiny figurines of your tiny best friend</em>
        </div>
        <div><Link to="/portraits">Get Started</Link></div>
      </div>
    </footer>
  )
}

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/portraits" element={<PortraitsLanding />} />
          <Route path="/portraits/upload" element={<PortraitUpload />} />
          <Route path="/portraits/:id" element={<PortraitStatus />} />
          <Route path="/portraits/:id/deposit" element={<PortraitDeposit />} />
          <Route path="/portraits/:id/checkout" element={<PortraitCheckout />} />
          <Route path="/portraits/:id/confirmation" element={<PortraitConfirmation />} />
          <Route path="/shop" element={<Shop />} />
          <Route path="/shop/:slug" element={<ProductPage />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/order/:token" element={<OrderConfirmation />} />
          <Route path="*" element={<div className="container page"><h1>Not found</h1><Link to="/">Go home →</Link></div>} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}
