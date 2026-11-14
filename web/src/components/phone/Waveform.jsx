import React, { useEffect, useRef } from 'react'

export default function Waveform({ isActive = false, isSpeaking = false }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animationId
    let phase = 0

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const centerY = canvas.height / 2

      // Draw restrained audio wave lines
      const lineCount = 3
      const numPoints = 40
      const width = canvas.width
      const step = width / (numPoints - 1)

      for (let l = 0; l < lineCount; l++) {
        ctx.beginPath()
        const alpha = l === 0 ? 0.9 : 0.45 - l * 0.15
        ctx.strokeStyle = isSpeaking
          ? `rgba(52, 199, 89, ${alpha})`
          : isActive
          ? `rgba(255, 255, 255, ${alpha})`
          : `rgba(255, 255, 255, 0.15)`
        ctx.lineWidth = l === 0 ? 2 : 1

        for (let i = 0; i < numPoints; i++) {
          const x = i * step
          // Windowing envelope so ends are zero
          const window = Math.sin((Math.PI * i) / (numPoints - 1))
          const amp = isActive
            ? (isSpeaking ? 16 : 8) * window * (0.8 + 0.3 * Math.sin(phase * 1.5 + l))
            : 1.5 * window

          const freq = 0.05 + l * 0.02
          const y = centerY + Math.sin(x * freq + phase + l * 0.8) * amp

          if (i === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        }
        ctx.stroke()
      }

      if (isActive) {
        phase += isSpeaking ? 0.08 : 0.04
      } else {
        phase += 0.01
      }
      animationId = requestAnimationFrame(render)
    }

    render()
    return () => cancelAnimationFrame(animationId)
  }, [isActive, isSpeaking])

  return (
    <div style={{ width: '100%', height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <canvas
        ref={canvasRef}
        width={240}
        height={44}
        style={{ display: 'block', width: 240, height: 44 }}
      />
    </div>
  )
}
