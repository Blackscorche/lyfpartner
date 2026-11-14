import React from 'react'
import { LANGUAGES } from '../../data/languages'
import { FlagNG, PhoneIcon, MicIcon } from '../common/Icons'

export default function WalkthroughGuide({
  currentLang = 'ha',
  onSelectLang,
  onSimulatePhrase,
  phoneState = 'lock',
  onStartCall,
  isReplayRunning = false,
  onStartReplay
}) {
  const langData = LANGUAGES[currentLang] || LANGUAGES.ha
  const inCall = phoneState === 'incall'

  return (
    <div style={{
      background: 'var(--bg-white)',
      border: '1.5px solid var(--color-border)',
      borderRadius: 'var(--radius-xl)',
      padding: '16px 20px',
      boxShadow: 'var(--shadow-card)',
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }}>
      {/* Step 1 Header: Language Selection */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            width: 22,
            height: 22,
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-ink)',
            color: '#FFFFFF',
            fontSize: 11,
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-mono)'
          }}>
            1
          </span>
          <span style={{
            fontSize: 12,
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: 0.8,
            color: 'var(--color-ink)',
            fontFamily: 'var(--font-mono)'
          }}>
            Select Indigenous Language
          </span>
        </div>

        <span style={{
          fontSize: 11,
          fontFamily: 'var(--font-mono)',
          color: 'var(--color-accent-green)',
          fontWeight: 700
        }}>
          {langData.region}
        </span>
      </div>

      {/* 4 Big Rounded Language Switcher Buttons */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 8
      }}>
        {Object.values(LANGUAGES).map(l => {
          const isSelected = currentLang === l.id
          return (
            <button
              key={l.id}
              onClick={() => onSelectLang(l.id)}
              style={{
                padding: '10px 8px',
                borderRadius: 'var(--radius-lg)',
                border: `2px solid ${isSelected ? 'var(--color-accent-green)' : 'var(--color-border)'}`,
                background: isSelected ? 'var(--color-accent-green-subtle)' : 'var(--bg-paper-surface)',
                color: isSelected ? 'var(--color-accent-green-hover)' : 'var(--color-ink)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: isSelected ? '0 4px 14px rgba(14, 90, 60, 0.15)' : 'none',
                transform: isSelected ? 'translateY(-2px)' : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <FlagNG size={14} />
                <span style={{ fontSize: 13, fontWeight: 800, fontFamily: 'var(--font-sans)' }}>
                  {l.name}
                </span>
              </div>
              <span style={{
                fontSize: 9.5,
                fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                color: isSelected ? 'var(--color-accent-green)' : 'var(--color-ink-tertiary)'
              }}>
                [{l.code}] &bull; {l.caller.name.split(' ')[0]}
              </span>
            </button>
          )
        })}
      </div>

      {/* Step 2 & 3: Interactive Spoken Testing Guidance */}
      <div style={{
        background: 'var(--bg-paper-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border-subtle)',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              width: 20,
              height: 20,
              borderRadius: 'var(--radius-full)',
              background: 'var(--color-accent-green)',
              color: '#FFFFFF',
              fontSize: 10,
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'var(--font-mono)'
            }}>
              2
            </span>
            <span style={{ fontSize: 11.5, fontWeight: 800, color: 'var(--color-ink)', fontFamily: 'var(--font-mono)' }}>
              Interactive Test Phrases (Click to Speak Live)
            </span>
          </div>

          {!inCall ? (
            <button
              onClick={() => onStartCall('333')}
              style={{
                padding: '5px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: 10.5,
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                background: '#34C759',
                color: '#FFFFFF',
                boxShadow: '0 2px 8px rgba(52, 199, 89, 0.4)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              <PhoneIcon size={12} color="#FFFFFF" />
              <span>Dial 333 to Begin</span>
            </button>
          ) : (
            <span style={{
              fontSize: 10,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              color: '#34C759',
              background: 'rgba(52, 199, 89, 0.12)',
              padding: '3px 10px',
              borderRadius: 'var(--radius-full)',
              display: 'flex',
              alignItems: 'center',
              gap: 5
            }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#34C759' }} />
              CALL CONNECTED (333)
            </span>
          )}
        </div>

        {/* 3 Quick Phrase Action Pills */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 8
        }}>
          {langData.quickPhrases.map((phrase) => (
            <button
              key={phrase.id}
              onClick={() => onSimulatePhrase(phrase)}
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-white)',
                border: '1.5px solid var(--color-border)',
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                flexDirection: 'column',
                gap: 3,
                transition: 'all 0.15s ease',
                boxShadow: 'var(--shadow-key)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-accent-green)'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)'
                e.currentTarget.style.transform = 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <MicIcon size={13} color="var(--color-accent-green)" />
                <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--color-ink)', fontFamily: 'var(--font-sans)' }}>
                  {phrase.label}
                </span>
              </div>
              <span style={{
                fontSize: 10,
                color: 'var(--color-accent-green)',
                fontWeight: 600,
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                "{phrase.text}"
              </span>
              <span style={{ fontSize: 9.5, color: 'var(--color-ink-tertiary)', fontStyle: 'italic' }}>
                {phrase.translation}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
