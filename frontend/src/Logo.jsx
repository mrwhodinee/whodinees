import React from 'react'

export default function Logo({ size = 36 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-label="Whodinees logo">
      <defs>
        <linearGradient id="whodinees-g" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#b388ff" />
          <stop offset="1" stopColor="#7c4dff" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="60" height="60" rx="16" fill="url(#whodinees-g)" />
      <path d="M18 34 h28 l-4 18 a4 4 0 0 1 -4 3 h-12 a4 4 0 0 1 -4 -3 Z" fill="#fff" />
      <rect x="16" y="30" width="32" height="6" rx="2" fill="#fff" />
      <path d="M32 30 C 32 22 26 18 22 20 C 24 26 28 30 32 30 Z" fill="#fff" />
      <path d="M32 30 C 32 22 38 18 42 20 C 40 26 36 30 32 30 Z" fill="#fff" />
      <circle cx="32" cy="18" r="3.5" fill="#fff" />
      <path d="M32 8 l1.5 3 3 1.5 -3 1.5 -1.5 3 -1.5 -3 -3 -1.5 3 -1.5 Z" fill="#fff" fillOpacity="0.9" />
    </svg>
  )
}
