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
          <NavLink to="/shop">Shop</NavLink>
          <NavLink to="/cart">
            Cart{count > 0 && <span className="cart-badge">{count}</span>}
          </NavLink>
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
          © {new Date().getFullYear()} Whodinees · <em>small objects, big magic</em>
        </div>
        <div><Link to="/shop">Shop</Link></div>
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
