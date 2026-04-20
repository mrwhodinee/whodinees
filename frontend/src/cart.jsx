import React, { createContext, useContext, useEffect, useState, useMemo } from 'react'

const CartContext = createContext(null)
const STORAGE_KEY = 'whodinees-cart-v1'

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  }, [items])

  function add(product, quantity = 1) {
    setItems(prev => {
      const idx = prev.findIndex(i => i.slug === product.slug)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = { ...next[idx], quantity: next[idx].quantity + quantity }
        return next
      }
      return [...prev, {
        slug: product.slug,
        name: product.name,
        price: Number(product.price),
        image: product.image_url_resolved || '',
        quantity,
      }]
    })
  }
  function remove(slug) { setItems(prev => prev.filter(i => i.slug !== slug)) }
  function setQty(slug, qty) {
    setItems(prev => prev.map(i => i.slug === slug ? { ...i, quantity: Math.max(1, qty) } : i))
  }
  function clear() { setItems([]) }

  const subtotal = useMemo(() => items.reduce((s, i) => s + i.price * i.quantity, 0), [items])
  const count = useMemo(() => items.reduce((n, i) => n + i.quantity, 0), [items])

  const value = { items, add, remove, setQty, clear, subtotal, count }
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used inside <CartProvider>')
  return ctx
}
