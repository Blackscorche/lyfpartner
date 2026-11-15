import React, { useEffect, useRef } from 'react'
import { MicIcon, PhoneIcon, UserIcon, BotIcon } from '../common/Icons'

export default function TranscriptView({ entries = [] }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  const LANG_NAMES = {
    HA: 'Hausa',
    YO: 'Yoruba',
    IG: 'Igbo',
    EN: 'Nigerian English'
  }

  return (
    <div style={{
      background: 'var(--bg-white)',
      border: '1.5px solid var(--color-border)',
      borderRadius: 'var(--radius-xl)',
      display: 'flex',
      flexDirection: 'column',
      height: 280,
      overflow: 'hidden',
      boxShadow: 'var(--shadow-card)'
    }}>
      {/* Title Bar with Live Audio Visualizer */}
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-paper-surface)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28,
            height: 28,
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-ink)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <MicIcon size={14} color="#FFFFFF" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                fontSize: 12,
                fontWeight: 800,
                textTransform: 'uppercase',
                letterSpacing: 1,
                color: 'var(--color-ink)',
                fontFamily: 'var(--font-mono)'
              }}>
                Dual-Voice Audio Stream
              </span>
              <span style={{
                fontSize: 10,
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                background: 'var(--bg-subtle)',
                color: 'var(--color-ink-secondary)',
                border: '1px solid var(--color-border-subtle)'
              }}>
                {entries.length} {entries.length === 1 ? 'turn' : 'turns'}
              </span>
            </div>
            <span style={{ fontSize: 10.5, color: 'var(--color-ink-tertiary)', fontFamily: 'var(--font-mono)' }}>
              N-ATLAS Multilingual Whisper ASR &bull; End-to-End
            </span>
          </div>
        </div>

        {/* Dancing Audio Equalizer */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 3,
          background: 'var(--color-accent-green-subtle)',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--color-accent-green-border)'
        }}>
          {[6, 12, 18, 10, 16, 8].map((initH, i) => (
            <span
              key={i}
              style={{
                width: 2.5,
                height: initH,
                background: 'var(--color-accent-green)',
                borderRadius: 2,
                animation: `liveWaveDance 0.8s infinite alternate ease-in-out ${i * 0.12}s`,
                transformOrigin: 'bottom'
              }}
            />
          ))}
          <span style={{
            fontSize: 10,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-accent-green)',
            marginLeft: 4
          }}>
            STREAMING
          </span>
        </div>
      </div>

      {/* Transcript Log Stream */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        fontFamily: 'var(--font-mono)',
        fontSize: 12.5
      }}>
        {entries.length === 0 ? (
          <div style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-ink-tertiary)',
            textAlign: 'center',
            padding: '20px 40px'
          }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              background: 'var(--bg-paper-surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 10,
              color: 'var(--color-ink-tertiary)'
            }}>
              <PhoneIcon size={20} />
            </div>
            <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--color-ink-secondary)' }}>
              Awaiting Voice Turn Input
            </p>
            <p style={{ margin: '4px 0 0', fontSize: 11.5, color: 'var(--color-ink-tertiary)' }}>
              Spoken dialogue in Hausa, Yoruba, Igbo, and English will stream and transcribe here live.
            </p>
          </div>
        ) : (
          entries.map((entry, idx) => {
            const isCaller = entry.speaker === 'caller'
            const time = entry.timestamp || new Date().toLocaleTimeString('en-GB')
            const langCode = (entry.language || 'ha').toUpperCase()
            const langLabel = LANG_NAMES[langCode] || langCode
            const conf = entry.confidence ? Math.round(entry.confidence * 100) : 98

            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  gap: 12,
                  alignItems: 'flex-start',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-lg)',
                  background: isCaller ? 'var(--bg-paper-surface)' : 'var(--color-accent-green-subtle)',
                  border: `1.5px solid ${isCaller ? 'var(--color-border-subtle)' : 'var(--color-accent-green-border)'}`,
                  animation: 'slideInUp 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
                }}
              >
                {/* Avatar Icon Circle */}
                <div style={{
                  width: 34,
                  height: 34,
                  borderRadius: 'var(--radius-full)',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: isCaller ? 'var(--color-ink)' : 'var(--color-accent-green)',
                  color: '#FFFFFF',
                  boxShadow: isCaller ? '0 2px 6px rgba(0,0,0,0.2)' : '0 2px 6px rgba(14,90,60,0.3)'
                }}>
                  {isCaller ? <UserIcon size={15} color="#FFFFFF" /> : <BotIcon size={16} color="#FFFFFF" />}
                </div>

                {/* Content Bubble */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        fontWeight: 800,
                        color: isCaller ? 'var(--color-ink)' : 'var(--color-accent-green)',
                        fontSize: 11.5,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5
                      }}>
                        {isCaller ? 'Caller (Customer)' : 'Lyfpartner AI Voice'}
                      </span>

                      <span style={{
                        fontSize: 9.5,
                        fontWeight: 800,
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-full)',
                        background: 'var(--bg-white)',
                        color: 'var(--color-ink-secondary)',
                        border: '1px solid var(--color-border)'
                      }}>
                        {langCode} &bull; {langLabel}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10.5, color: 'var(--color-ink-tertiary)' }}>
                      <span style={{
                        background: 'rgba(255,255,255,0.7)',
                        padding: '1px 6px',
                        borderRadius: 4,
                        border: '1px solid var(--color-border-subtle)'
                      }}>
                        conf: {conf}%
                      </span>
                      <span>{time}</span>
                    </div>
                  </div>

                  <p style={{
                    margin: 0,
                    fontSize: 13,
                    lineHeight: 1.5,
                    color: 'var(--color-ink)',
                    wordBreak: 'break-word',
                    fontFamily: 'var(--font-sans)',
                    fontWeight: 500
                  }}>
                    {entry.text}
                  </p>
                </div>
              </div>
            )
          })
        )}
        <div ref={scrollRef} />
      </div>
    </div>
  )
}
