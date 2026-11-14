import React from 'react'

export default function CaptionStrip({ text, language = 'ha', isAssistant = false }) {
  if (!text) return null

  const langTag = (language || 'ha').toUpperCase()

  return (
    <div style={{
      margin: '0 16px 12px',
      background: 'rgba(28, 28, 30, 0.88)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderRadius: 16,
      padding: '10px 14px',
      border: '1px solid rgba(255, 255, 255, 0.12)',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
      transition: 'all 0.25s ease-out'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            fontSize: 9.5,
            fontWeight: 800,
            padding: '1px 5px',
            borderRadius: 4,
            background: isAssistant ? '#0E5A3C' : '#2A6496',
            color: '#FFFFFF',
            fontFamily: 'var(--font-mono)'
          }}>
            {langTag}
          </span>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#A1A1A6' }}>
            {isAssistant ? 'Lyfpatner Voice' : 'Caller'}
          </span>
        </div>
        <span style={{ fontSize: 9.5, color: '#636366', fontWeight: 500 }}>
          iOS Live Captions
        </span>
      </div>

      <p style={{
        fontSize: 13.5,
        fontWeight: 400,
        color: '#F2F2F7',
        lineHeight: 1.35,
        margin: 0
      }}>
        {text}
      </p>
    </div>
  )
}
