import React from 'react'
import StatusBar from './StatusBar'
import './phone.css'

export default function PhoneFrame({ children, inCall = false }) {
  return (
    <div className="pure-phone-wrapper">
      {/* Dynamic Island pill with audio state */}
      <div className={`dynamic-island-container ${inCall ? 'island-expanded' : ''}`}>
        {inCall && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="#34C759">
              <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.46.57 3.58a1 1 0 01-.24 1.01l-2.21 2.2z" />
            </svg>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#34C759', fontFamily: 'var(--font-mono)' }}>
              333
            </span>
          </div>
        )}

        {/* Front camera lens & IR sensor cluster */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 auto' }}>
          <div style={{
            width: 10,
            height: 10,
            background: 'radial-gradient(circle at 35% 35%, #1f2b42 0%, #0c1220 60%, #030508 100%)',
            borderRadius: '50%',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.12)'
          }} />
          <div style={{
            width: 7,
            height: 7,
            background: 'radial-gradient(circle at 40% 40%, #161622 0%, #06060c 80%)',
            borderRadius: '50%'
          }} />
        </div>

        {inCall && (
          <div className="island-wave-cluster">
            <span className="island-wave-bar" />
            <span className="island-wave-bar" />
            <span className="island-wave-bar" />
          </div>
        )}
      </div>

      {/* Real iOS Status Bar (MTN NG, 5G, signal, battery, live time) */}
      <StatusBar />

      {/* Interactive Screen Content */}
      <div className="real-phone-content">
        {children}
      </div>

      {/* Screen Specular Glare */}
      <div className="real-phone-glare" />

      {/* iOS Home Indicator */}
      <div className="real-phone-home-indicator" />
    </div>
  )
}
