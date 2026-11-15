import React from 'react'

export default function FeaturePhone({
  inCall = false,
  callDuration = 0,
  captionText = '',
  onCall,
  onEndCall
}) {
  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`
  }

  return (
    <div style={{
      width: 240,
      height: 520,
      background: '#2B2B28',
      borderRadius: 'var(--radius-xl)',
      border: '3.5px solid #1C1C1A',
      padding: '16px 14px',
      margin: '0 auto',
      boxShadow: 'var(--shadow-card)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      userSelect: 'none',
      flexShrink: 0
    }}>
      {/* Speaker grill */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 3, marginBottom: 8 }}>
        {[...Array(5)].map((_, i) => (
          <div key={i} style={{ width: 3.5, height: 3.5, borderRadius: '50%', background: '#111' }} />
        ))}
      </div>

      {/* Small Monochrome Green Backlit LCD Screen */}
      <div style={{
        height: 135,
        background: '#8DA385',
        border: '2.5px solid #1A1A18',
        borderRadius: 'var(--radius-sm)',
        padding: '8px 10px',
        color: '#1A2E19',
        fontFamily: 'var(--font-mono)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.35)'
      }}>
        {/* Status Line */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9.5, fontWeight: 800 }}>
          <span>MTN-NG [333]</span>
          <span style={{
            background: inCall ? '#1A2E19' : 'transparent',
            color: inCall ? '#8DA385' : '#1A2E19',
            padding: '1px 4px',
            borderRadius: 2
          }}>
            {inCall ? 'IN CALL' : 'STANDBY'}
          </span>
        </div>

        {/* Center Display */}
        <div style={{ textAlign: 'center' }}>
          {inCall ? (
            <>
              <div style={{ fontSize: 16, fontWeight: 900, letterSpacing: 0.5 }}>LYFPARTNER</div>
              <div style={{ fontSize: 11, fontWeight: 700, marginTop: 2 }}>TIME: {formatTimer(callDuration)}</div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 14, fontWeight: 900 }}>SHORTCODE: 333</div>
              <div style={{ fontSize: 9.5, marginTop: 2, fontWeight: 700 }}>NO SMARTPHONE NEEDED</div>
            </>
          )}
        </div>

        {/* Bottom LCD Caption Line */}
        <div style={{
          fontSize: 9,
          borderTop: '1px solid rgba(26, 46, 25, 0.4)',
          paddingTop: 3,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          fontWeight: 700
        }}>
          {captionText ? `> ${captionText}` : 'Press Green to Call 333'}
        </div>
      </div>

      {/* Hardware Nav & Softkeys */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '8px 2px 4px' }}>
        {/* Call (Green) */}
        <button
          onClick={inCall ? onEndCall : onCall}
          style={{
            padding: '6px 12px',
            borderRadius: 'var(--radius-xs)',
            background: inCall ? '#B4532A' : '#34C759',
            color: '#FFFFFF',
            fontSize: 10,
            fontWeight: 900,
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
        >
          {inCall ? 'END' : 'CALL'}
        </button>

        {/* Center 4-way Nav D-Pad */}
        <div style={{
          width: 44,
          height: 30,
          background: '#3A3A36',
          borderRadius: 6,
          border: '1.5px solid #1C1C1A',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'inset 0 1px 2px rgba(255,255,255,0.1)'
        }}>
          <div style={{ width: 14, height: 10, borderRadius: 2, background: '#222' }} />
        </div>

        {/* Clear / Power (Red) */}
        <button
          onClick={onEndCall}
          style={{
            padding: '6px 12px',
            borderRadius: 'var(--radius-xs)',
            background: '#444440',
            color: '#DDD',
            fontSize: 10,
            fontWeight: 800,
            cursor: 'pointer'
          }}
        >
          CLR
        </button>
      </div>

      {/* Classic Physical Keypad */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '6px',
        padding: '4px 2px 0'
      }}>
        {['1', '2 ABC', '3 DEF', '4 GHI', '5 JKL', '6 MNO', '7 PQRS', '8 TUV', '9 WXYZ', '*', '0 +', '#'].map((k) => (
          <div
            key={k}
            style={{
              height: 34,
              background: '#383834',
              borderRadius: 'var(--radius-xs)',
              border: '1px solid #1C1C1A',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#DDD',
              fontSize: 11,
              fontWeight: 700,
              boxShadow: '0 1px 2px rgba(0,0,0,0.3)',
              cursor: 'pointer'
            }}
          >
            {k}
          </div>
        ))}
      </div>
    </div>
  )
}
