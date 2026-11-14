import React, { useState, useEffect } from 'react'

export default function StatusBar({ isDark = true }) {
  const [time, setTime] = useState('')

  useEffect(() => {
    const update = () => {
      const now = new Date()
      let hours = now.getHours()
      let mins = now.getMinutes()
      mins = mins < 10 ? '0' + mins : mins
      setTime(`${hours}:${mins}`)
    }
    update()
    const timer = setInterval(update, 1000)
    return () => clearInterval(timer)
  }, [])

  const strokeColor = isDark ? '#FFFFFF' : '#14130F'
  const fillColor = isDark ? '#FFFFFF' : '#14130F'

  return (
    <div style={{
      height: 48,
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      fontSize: 14,
      fontWeight: 600,
      zIndex: 25,
      color: strokeColor,
      userSelect: 'none'
    }}>
      {/* Time */}
      <span style={{ width: 60, letterSpacing: -0.2 }}>{time || '9:41'}</span>

      {/* Carrier & Hardware indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 11, fontWeight: 500, opacity: 0.85, letterSpacing: -0.1 }}>MTN NG</span>

        {/* Signal Bars SVG */}
        <svg width="17" height="11" viewBox="0 0 17 11" fill="none">
          <rect x="0.5" y="7.5" width="2.5" height="3" rx="0.75" fill={fillColor} />
          <rect x="4.5" y="5.5" width="2.5" height="5" rx="0.75" fill={fillColor} />
          <rect x="8.5" y="3.5" width="2.5" height="7" rx="0.75" fill={fillColor} />
          <rect x="12.5" y="0.5" width="2.5" height="10" rx="0.75" fill={fillColor} />
        </svg>

        {/* 5G label */}
        <span style={{ fontSize: 10, fontWeight: 700 }}>5G</span>

        {/* Battery SVG */}
        <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
          <rect x="0.5" y="0.5" width="20" height="11" rx="3.5" stroke={strokeColor} strokeOpacity="0.4" />
          <rect x="2" y="2" width="15" height="8" rx="2" fill={fillColor} />
          <path d="M22 4C22.5523 4 23 4.44772 23 5V7C23 7.55228 22.5523 8 22 8V4Z" fill={fillColor} fillOpacity="0.4" />
        </svg>
      </div>
    </div>
  )
}
