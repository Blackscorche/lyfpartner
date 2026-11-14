import React, { useState } from 'react'
import { ShieldIcon, LockIcon, KeyIcon, UserIcon, CheckIcon } from '../common/Icons'

export default function AdminAuthGate({ onAuthenticated }) {
  const [staffId, setStaffId] = useState('OP-77402')
  const [passcode, setPasscode] = useState('lyfpartner2026')
  const [department, setDepartment] = useState('Tier 2 Telephony & Fraud Audit')
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = (e) => {
    if (e) e.preventDefault()
    setError(null)
    setIsLoading(true)

    // Simulate enterprise bank authentication
    setTimeout(() => {
      if (!staffId.trim() || !passcode.trim()) {
        setError('Staff ID and security authorization token are required.')
        setIsLoading(false)
        return
      }

      const session = {
        staffId,
        department,
        officerName: 'Zainab Dahiru',
        role: 'Senior Operations & Risk Officer',
        authenticatedAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 3600000).toISOString()
      }

      localStorage.setItem('lyfpartner_staff_session', JSON.stringify(session))
      setIsLoading(false)
      onAuthenticated(session)
    }, 400)
  }

  const handleQuickDemoLogin = () => {
    setStaffId('OP-77402')
    setPasscode('lyfpartner2026')
    setDepartment('Central Fraud & NIP Telephony Operations')
    handleLogin()
  }

  return (
    <div style={{
      minHeight: 'calc(100vh - 120px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px 20px',
      background: 'var(--bg-paper)'
    }}>
      <div style={{
        width: '100%',
        maxWidth: 440,
        background: 'var(--bg-white)',
        border: '1.5px solid var(--color-border)',
        borderRadius: 'var(--radius-2xl)',
        padding: '36px 32px',
        boxShadow: 'var(--shadow-card-hover)',
        display: 'flex',
        flexDirection: 'column',
        gap: 20
      }}>
        {/* Bank Security Badge */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 52,
            height: 52,
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-ink)',
            color: '#FFFFFF',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 14,
            boxShadow: '0 4px 14px rgba(20, 19, 15, 0.25)'
          }}>
            <ShieldIcon size={24} color="#FFFFFF" />
          </div>

          <h2 style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 26,
            fontWeight: 400,
            margin: '0 0 6px',
            color: 'var(--color-ink)'
          }}>
            Bank Operations Portal
          </h2>

          <span style={{
            fontSize: 10.5,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            padding: '2px 10px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-accent-green-subtle)',
            color: 'var(--color-accent-green)',
            border: '1px solid var(--color-accent-green-border)'
          }}>
            RESTRICTED ACCESS &bull; NIP TELEPHONY NODE
          </span>
        </div>

        {/* Security Warning Notice */}
        <div style={{
          background: 'var(--bg-paper-surface)',
          border: '1px solid var(--color-border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          fontSize: 11,
          color: 'var(--color-ink-secondary)',
          lineHeight: 1.45
        }}>
          This terminal is restricted to authorized banking personnel, N-ATLAS telephony supervisors, and compliance officers. All queries are audited and logged with immutable timestamps.
        </div>

        {error && (
          <div style={{
            background: 'var(--color-accent-clay-subtle)',
            border: '1px solid var(--color-accent-clay-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 12px',
            fontSize: 11.5,
            color: 'var(--color-accent-clay)',
            fontWeight: 600
          }}>
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{
              fontSize: 11,
              fontWeight: 800,
              color: 'var(--color-ink-secondary)',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              display: 'block',
              marginBottom: 6
            }}>
              Staff Officer ID
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={staffId}
                onChange={(e) => setStaffId(e.target.value)}
                placeholder="e.g. OP-77402"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1.5px solid var(--color-border)',
                  fontSize: 13,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--color-ink)',
                  background: 'var(--bg-paper-surface)',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{
              fontSize: 11,
              fontWeight: 800,
              color: 'var(--color-ink-secondary)',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              display: 'block',
              marginBottom: 6
            }}>
              Authorization Token / Passcode
            </label>
            <input
              type="password"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              placeholder="••••••••••••"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                border: '1.5px solid var(--color-border)',
                fontSize: 13,
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-ink)',
                background: 'var(--bg-paper-surface)',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{
              fontSize: 11,
              fontWeight: 800,
              color: 'var(--color-ink-secondary)',
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              display: 'block',
              marginBottom: 6
            }}>
              Security Role / Domain
            </label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                border: '1.5px solid var(--color-border)',
                fontSize: 12,
                fontFamily: 'var(--font-mono)',
                color: 'var(--color-ink)',
                background: 'var(--bg-paper-surface)',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="Tier 2 Telephony & Fraud Audit">Tier 2 Telephony & Fraud Audit</option>
              <option value="Central Bank Compliance & NIP Oversight">Central Bank Compliance & NIP Oversight</option>
              <option value="Branch Escalation Desk & Caregiver Verification">Branch Escalation Desk & Caregiver Verification</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: 6,
              padding: '12px',
              borderRadius: 'var(--radius-full)',
              background: 'var(--color-ink)',
              color: '#FFFFFF',
              fontSize: 12.5,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              border: 'none',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              boxShadow: '0 4px 12px rgba(20, 19, 15, 0.2)',
              transition: 'all 0.15s ease'
            }}
          >
            <LockIcon size={14} color="#FFFFFF" />
            <span>{isLoading ? 'Verifying Credentials...' : 'Authenticate & Enter Operations Portal'}</span>
          </button>
        </form>

        {/* 1-Click Judge / Demo Quick Access */}
        <div style={{
          borderTop: '1px solid var(--color-border-subtle)',
          paddingTop: 16,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8
        }}>
          <span style={{ fontSize: 11, color: 'var(--color-ink-tertiary)', fontFamily: 'var(--font-mono)' }}>
            Hackathon Judge Quick Sign-In:
          </span>
          <button
            type="button"
            onClick={handleQuickDemoLogin}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius-full)',
              background: 'var(--color-accent-green-subtle)',
              border: '1.5px solid var(--color-accent-green-border)',
              color: 'var(--color-accent-green)',
              fontSize: 11,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            <CheckIcon size={12} color="var(--color-accent-green)" />
            <span>1-Click Demo Login as Lead Officer</span>
          </button>
        </div>
      </div>
    </div>
  )
}
