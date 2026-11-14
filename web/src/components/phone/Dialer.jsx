import React, { useState } from 'react'
import { playDTMF } from '../../utils/audio'

const KEYS = [
  { digit: '1', letters: '' },
  { digit: '2', letters: 'A B C' },
  { digit: '3', letters: 'D E F' },
  { digit: '4', letters: 'G H I' },
  { digit: '5', letters: 'J K L' },
  { digit: '6', letters: 'M N O' },
  { digit: '7', letters: 'P Q R S' },
  { digit: '8', letters: 'T U V' },
  { digit: '9', letters: 'W X Y Z' },
  { digit: '*', letters: '' },
  { digit: '0', letters: '+' },
  { digit: '#', letters: '' }
]

export default function Dialer({ onCall }) {
  const [number, setNumber] = useState('333')

  const handleKeyPress = (digit) => {
    playDTMF(digit)
    setNumber(prev => (prev.length < 15 ? prev + digit : prev))
  }

  const handleDelete = () => {
    setNumber(prev => prev.slice(0, -1))
  }

  const handleStartCall = () => {
    if (number.length > 0) {
      onCall(number)
    }
  }

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '8px 16px 20px',
      background: '#000000',
      color: '#FFFFFF'
    }}>
      {/* Number Display */}
      <div style={{ textAlign: 'center', height: 60, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{
          fontSize: number.length > 8 ? 24 : 30,
          fontWeight: 400,
          letterSpacing: 1,
          fontFamily: 'var(--font-sans)',
          minHeight: 36
        }}>
          {number}
        </div>
        {number === '333' && (
          <span style={{ fontSize: 11, color: '#34C759', fontWeight: 600 }}>
            Lyfpatner Toll-Free Hotline
          </span>
        )}
      </div>

      {/* 3x4 Keypad Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '9px 12px',
        maxWidth: 220,
        margin: '0 auto'
      }}>
        {KEYS.map(({ digit, letters }) => (
          <button
            key={digit}
            onClick={() => handleKeyPress(digit)}
            className="dialer-key"
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#242426',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background 0.15s, transform 0.05s',
              margin: '0 auto'
            }}
            onMouseDown={(e) => {
              e.currentTarget.style.background = '#404044'
              e.currentTarget.style.transform = 'scale(0.95)'
            }}
            onMouseUp={(e) => {
              e.currentTarget.style.background = '#242426'
              e.currentTarget.style.transform = 'scale(1)'
            }}
          >
            <span style={{ fontSize: 24, fontWeight: 400, lineHeight: 1 }}>{digit}</span>
            {letters && (
              <span style={{ fontSize: 8.5, fontWeight: 700, letterSpacing: 1.2, marginTop: 1, opacity: 0.8 }}>
                {letters}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Bottom Action Row: Call Button + Delete */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        alignItems: 'center',
        maxWidth: 220,
        margin: '6px auto 0'
      }}>
        <div />

        {/* Green Call Button */}
        <button
          onClick={handleStartCall}
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: '#34C759',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto',
            boxShadow: '0 4px 12px rgba(52, 199, 89, 0.4)',
            transition: 'transform 0.1s'
          }}
          onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.95)' }}
          onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)' }}
        >
          {/* Phone call icon SVG */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="#FFFFFF">
            <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.46.57 3.58a1 1 0 01-.24 1.01l-2.21 2.2z" />
          </svg>
        </button>

        {/* Delete key */}
        {number.length > 0 ? (
          <button
            onClick={handleDelete}
            style={{
              background: 'transparent',
              color: '#8E8E93',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto'
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" />
              <line x1="18" y1="9" x2="12" y2="15" />
              <line x1="12" y1="9" x2="18" y2="15" />
            </svg>
          </button>
        ) : <div />}
      </div>
    </div>
  )
}
