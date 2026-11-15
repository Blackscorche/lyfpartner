import React from 'react'

export default function MessagesView({ message, onBack }) {
  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      background: '#000000',
      color: '#FFFFFF',
      padding: '8px 16px 20px'
    }}>
      {/* Messages Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: 12,
        borderBottom: '1px solid #1C1C1E'
      }}>
        <button
          onClick={onBack}
          style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#0A84FF', fontSize: 15 }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          <span>Back</span>
        </button>

        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: '#2C2C2E',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 2px',
            fontSize: 12,
            fontWeight: 700,
            color: '#8E8E93'
          }}>
            333
          </div>
          <span style={{ fontSize: 11, color: '#8E8E93' }}>Lyfpartner Bank</span>
        </div>

        <div style={{ width: 50 }} />
      </div>

      {/* Date Header */}
      <div style={{ textAlign: 'center', margin: '20px 0 12px', fontSize: 11, color: '#636366', fontWeight: 600 }}>
        Today &bull; SMS Delivery
      </div>

      {/* Received SMS Bubble */}
      <div style={{
        maxWidth: '85%',
        alignSelf: 'flex-start',
        background: '#26252A',
        borderRadius: '18px 18px 18px 4px',
        padding: '12px 14px',
        fontSize: 14,
        lineHeight: 1.45,
        color: '#FFFFFF',
        fontFamily: 'var(--font-mono)'
      }}>
        <p style={{ margin: 0 }}>
          {message || 'Lyfpartner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8831. Bal: NGN 244,990.00'}
        </p>
      </div>

      <div style={{ marginTop: 'auto', textAlign: 'center' }}>
        <button
          onClick={onBack}
          style={{
            padding: '8px 18px',
            background: '#1C1C1E',
            borderRadius: 20,
            fontSize: 12,
            color: '#8E8E93',
            border: '1px solid #2C2C2E'
          }}
        >
          Tap to return to dialer
        </button>
      </div>
    </div>
  )
}
