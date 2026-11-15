import React, { useState, useEffect } from 'react'

export default function NotificationBanner({ message, onOpen }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Delay slightly to let call-ended transition settle, then spring in
    const timer = setTimeout(() => setVisible(true), 600)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div
      onClick={onOpen}
      style={{
        position: 'absolute',
        top: 54,
        left: 12,
        right: 12,
        background: 'rgba(30, 30, 32, 0.94)',
        backdropFilter: 'blur(30px)',
        WebkitBackdropFilter: 'blur(30px)',
        borderRadius: 20,
        padding: '12px 16px',
        border: '1px solid rgba(255, 255, 255, 0.14)',
        boxShadow: 'var(--shadow-notification)',
        color: '#FFFFFF',
        cursor: 'pointer',
        zIndex: 50,
        transform: visible ? 'translateY(0)' : 'translateY(-120%)',
        opacity: visible ? 1 : 0,
        transition: 'transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* Messages app icon SVG */}
          <div style={{
            width: 20,
            height: 20,
            borderRadius: 5,
            background: '#34C759',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="#FFFFFF">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
            </svg>
          </div>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#FFFFFF', letterSpacing: -0.1 }}>
            MESSAGES &bull; 333
          </span>
        </div>
        <span style={{ fontSize: 11, color: '#8E8E93' }}>now</span>
      </div>

      <p style={{
        fontSize: 13,
        fontWeight: 400,
        color: '#E5E5EA',
        lineHeight: 1.35,
        margin: 0,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden'
      }}>
        {message || 'Lyfpartner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8831. Bal: NGN 244,990.00'}
      </p>
    </div>
  )
}
