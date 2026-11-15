import React, { useState, useEffect } from 'react'

export default function LockScreen({ onUnlock }) {
  const [dateStr, setDateStr] = useState('')
  const [timeStr, setTimeStr] = useState('')

  useEffect(() => {
    const now = new Date()
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    setDateStr(`${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}`)
    
    let hours = now.getHours()
    let mins = now.getMinutes()
    mins = mins < 10 ? '0' + mins : mins
    setTimeStr(`${hours}:${mins}`)
  }, [])

  return (
    <div
      onClick={onUnlock}
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '30px 20px 40px',
        color: '#FFFFFF',
        cursor: 'pointer',
        background: 'radial-gradient(ellipse at top, #1e293b 0%, #000000 80%)'
      }}
    >
      {/* Top Lock Icon & Clock */}
      <div style={{ textAlign: 'center', marginTop: 20 }}>
        {/* Subtle lock icon SVG */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ margin: '0 auto 12px', opacity: 0.7 }}>
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>

        <p style={{ fontSize: 16, fontWeight: 500, opacity: 0.85, letterSpacing: -0.2 }}>
          {dateStr}
        </p>
        <h1 style={{
          fontSize: 78,
          fontWeight: 200,
          letterSpacing: -2,
          lineHeight: 1,
          margin: '6px 0 0',
          fontFamily: 'var(--font-sans)'
        }}>
          {timeStr || '09:41'}
        </h1>
      </div>

      {/* Lyfpartner Service Notification Card */}
      <div style={{
        width: '100%',
        background: 'rgba(255, 255, 255, 0.12)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: 18,
        padding: '14px 16px',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{
              width: 18,
              height: 18,
              borderRadius: 4,
              background: '#0E5A3C',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              fontWeight: 800,
              color: '#FFFFFF'
            }}>
              ₦
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: -0.1 }}>Lyfpartner Voice</span>
          </div>
          <span style={{ fontSize: 11, opacity: 0.6 }}>now</span>
        </div>
        <p style={{ fontSize: 13, fontWeight: 600, margin: '0 0 2px' }}>
          Toll-Free Inclusive Banking Shortcode
        </p>
        <p style={{ fontSize: 12, opacity: 0.8, lineHeight: 1.35 }}>
          Tap to open dialer. Call <strong>333</strong> to speak in Hausa, Igbo, Yoruba or Nigerian English.
        </p>
      </div>

      {/* Bottom Hint */}
      <div style={{ textAlign: 'center', opacity: 0.65, fontSize: 13, fontWeight: 500 }}>
        <span>Tap screen to open dialer</span>
      </div>
    </div>
  )
}
