import React from 'react'
import { ShieldIcon, LockIcon, KeyIcon, CheckIcon, CloseIcon, ActivityIcon } from '../common/Icons'

export default function AuthState({
  authLevel = 'none',
  pinVerified = false,
  voiceScore = 0.0,
  isLocked = false,
  failedAttempts = 0
}) {
  const isFull = authLevel === 'full'
  const isBasic = authLevel === 'basic'

  return (
    <div style={{
      background: 'var(--bg-white)',
      border: '1.5px solid var(--color-border)',
      borderRadius: 'var(--radius-xl)',
      padding: '16px 20px',
      boxShadow: 'var(--shadow-card)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28,
            height: 28,
            borderRadius: 'var(--radius-full)',
            background: isLocked ? 'var(--color-accent-clay-subtle)' : 'var(--color-accent-green-subtle)',
            border: `1px solid ${isLocked ? 'var(--color-accent-clay-border)' : 'var(--color-accent-green-border)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isLocked ? 'var(--color-accent-clay)' : 'var(--color-accent-green)'
          }}>
            {isLocked ? <LockIcon size={14} /> : isFull ? <ShieldIcon size={14} /> : <KeyIcon size={14} />}
          </div>

          <div>
            <span style={{
              fontSize: 12,
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: 1,
              color: 'var(--color-ink)',
              fontFamily: 'var(--font-mono)'
            }}>
              Voiceprint & Biometric Gate
            </span>
            <span style={{ fontSize: 10.5, color: 'var(--color-ink-tertiary)', display: 'block', fontFamily: 'var(--font-mono)' }}>
              Argon2 multi-factor spoken PIN + 128-d acoustic vector
            </span>
          </div>
        </div>

        {/* Status Pill */}
        <span style={{
          fontSize: 10,
          fontWeight: 800,
          fontFamily: 'var(--font-mono)',
          padding: '4px 12px',
          borderRadius: 'var(--radius-full)',
          background: isLocked
            ? 'var(--color-accent-clay-subtle)'
            : isFull
            ? 'var(--color-accent-green-subtle)'
            : 'var(--bg-subtle)',
          color: isLocked
            ? 'var(--color-accent-clay)'
            : isFull
            ? 'var(--color-accent-green)'
            : 'var(--color-ink-secondary)',
          border: `1.5px solid ${isLocked ? 'var(--color-accent-clay-border)' : isFull ? 'var(--color-accent-green-border)' : 'var(--color-border)'}`
        }}>
          {isLocked ? 'ACCOUNT LOCKED' : isFull ? 'TIER 2 (FULL AUTH)' : isBasic ? 'TIER 1 (BASIC)' : 'UNAUTHENTICATED'}
        </span>
      </div>

      {/* 3 Squircle Status Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 12
      }}>
        {/* Tier Card */}
        <div style={{
          background: 'var(--bg-paper-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 14px',
          transition: 'all 0.2s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 9.5, color: 'var(--color-ink-tertiary)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.8 }}>
              SESSION PRIVILEGE
            </span>
            <ShieldIcon size={12} color="var(--color-ink-tertiary)" />
          </div>
          <span style={{
            fontSize: 15,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            color: isFull ? 'var(--color-accent-green)' : isBasic ? 'var(--color-blue-carrier)' : 'var(--color-ink-secondary)',
            marginTop: 4,
            display: 'block'
          }}>
            {authLevel.toUpperCase()}
          </span>
          <span style={{ fontSize: 10.5, color: 'var(--color-ink-tertiary)', display: 'block', marginTop: 3 }}>
            {isFull ? '₦50,000 max / transfer' : 'Inquiries & balances only'}
          </span>
        </div>

        {/* PIN Verification Card (Keypad DTMF or Spoken Voice) */}
        <div style={{
          background: 'var(--bg-paper-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 14px',
          transition: 'all 0.2s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 9.5, color: 'var(--color-ink-tertiary)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.8 }}>
              PIN AUTH (KEYPAD / VOICE)
            </span>
            {pinVerified ? (
              <CheckIcon size={13} color="var(--color-accent-green)" />
            ) : isLocked ? (
              <CloseIcon size={13} color="var(--color-accent-clay)" />
            ) : (
              <LockIcon size={12} color="var(--color-ink-tertiary)" />
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: pinVerified ? 'var(--color-accent-green)' : isLocked ? 'var(--color-accent-clay)' : 'var(--color-border-strong)',
              boxShadow: pinVerified ? '0 0 6px var(--color-accent-green)' : 'none'
            }} />
            <span style={{
              fontSize: 15,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              color: pinVerified ? 'var(--color-accent-green)' : isLocked ? 'var(--color-accent-clay)' : 'var(--color-ink-secondary)'
            }}>
              {pinVerified ? 'VERIFIED' : isLocked ? 'LOCKED' : failedAttempts > 0 ? `${failedAttempts}/3 FAILED` : 'PENDING'}
            </span>
          </div>
          <span style={{ fontSize: 10.5, color: 'var(--color-ink-tertiary)', display: 'block', marginTop: 3 }}>
            DTMF keypad & spoken voice hash
          </span>
        </div>

        {/* Voice Biometric Card */}
        <div style={{
          background: 'var(--bg-paper-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 14px',
          transition: 'all 0.2s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 9.5, color: 'var(--color-ink-tertiary)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.8 }}>
              VOICEPRINT MATCH
            </span>
            <ActivityIcon size={12} color="var(--color-ink-tertiary)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <span style={{
              fontSize: 15,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              color: voiceScore >= 0.85 ? 'var(--color-accent-green)' : 'var(--color-ink-secondary)'
            }}>
              {voiceScore > 0 ? `${Math.round(voiceScore * 100)}% SIMILAR` : '-- NO VECTOR --'}
            </span>
          </div>
          {/* Audio vector mini-bars */}
          <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: 8, marginTop: 4 }}>
            {[0.4, 0.7, 0.9, 0.6, 0.85, 0.5, 0.95, 0.6].map((ratio, i) => (
              <span
                key={i}
                style={{
                  flex: 1,
                  height: voiceScore > 0 ? `${ratio * 100}%` : '2px',
                  background: voiceScore >= 0.85 ? 'var(--color-accent-green)' : 'var(--color-border-strong)',
                  borderRadius: 1
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
