import React from 'react'

/**
 * Whodinees logo — a stylized rounded "W" with two little pointy ears
 * peeking over the top. Symmetric, clean, reads at 24px and up.
 */
export default function Logo({ size = 36 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Whodinees logo"
    >
      <defs>
        <linearGradient id="whodinees-g" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#b388ff" />
          <stop offset="1" stopColor="#7c4dff" />
        </linearGradient>
      </defs>
      {/* rounded square tile */}
      <rect x="2" y="2" width="60" height="60" rx="16" fill="url(#whodinees-g)" />
      {/* two little ears peeking over the top of the W */}
      <path d="M16 20 L22 10 L24 20 Z" fill="#fff" />
      <path d="M48 20 L42 10 L40 20 Z" fill="#fff" />
      {/* stylized rounded "W": two linked U-curves */}
      <path
        d="M12 22
           C 12 18, 20 18, 22 26
           L 26 44
           C 28 50, 30 50, 32 44
           L 32 30
           L 32 44
           C 34 50, 36 50, 38 44
           L 42 26
           C 44 18, 52 18, 52 22"
        fill="none"
        stroke="#fff"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* tiny nose dot between the humps */}
      <circle cx="32" cy="36" r="2.2" fill="#fff" />
    </svg>
  )
}
