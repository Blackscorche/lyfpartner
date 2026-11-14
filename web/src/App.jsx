import React, { useState, useEffect } from 'react'
import StageView from './components/StageView'
import StandalonePhoneView from './components/StandalonePhoneView'
import AdminCalls from './components/admin/AdminCalls'
import AdminAuthGate from './components/admin/AdminAuthGate'
import { FlagNG, LockIcon, PhoneIcon, ZapIcon } from './components/common/Icons'
import './tokens.css'

function getInitialRoute() {
  const path = window.location.pathname
  if (path.startsWith('/admin')) return 'admin'
  if (path.startsWith('/stage') || path.startsWith('/console')) return 'stage'
  return 'phone'
}

export default function App() {
  const [currentRoute, setCurrentRoute] = useState(getInitialRoute)
  const [isPresenterMode, setIsPresenterMode] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState('ha')
  const [staffSession, setStaffSession] = useState(() => {
    try {
      const saved = localStorage.getItem('lyfpartner_staff_session')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  // URL route sync
  useEffect(() => {
    const syncRoute = () => {
      const path = window.location.pathname
      if (path.startsWith('/admin')) setCurrentRoute('admin')
      else if (path.startsWith('/stage') || path.startsWith('/console')) setCurrentRoute('stage')
      else setCurrentRoute('phone')
    }
    window.addEventListener('popstate', syncRoute)
    return () => window.removeEventListener('popstate', syncRoute)
  }, [])

  // Presenter mode body class
  useEffect(() => {
    document.body.classList.toggle('presenter-mode', isPresenterMode)
  }, [isPresenterMode])

  // 'P' keyboard shortcut for stage mode
  useEffect(() => {
    const handleKey = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
      if (e.key === 'p' || e.key === 'P') setIsPresenterMode(prev => !prev)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  const navigate = (route, path) => {
    setCurrentRoute(route)
    window.history.pushState({}, '', path)
  }

  const handleStaffAuthenticated = (session) => setStaffSession(session)
  const handleStaffSignOut = () => {
    localStorage.removeItem('lyfpartner_staff_session')
    setStaffSession(null)
  }

  /* ─────────────────────────────────────────────
     PHONE SIMULATOR PAGE  (default: /)
     Clean minimal chrome — no route pills, no admin links
     Mobile-first centered layout
  ───────────────────────────────────────────── */
  if (currentRoute === 'phone') {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-paper)',
        color: 'var(--color-ink)'
      }}>
        {/* Minimal Phone Header */}
        <header style={{
          height: 52,
          borderBottom: '1.5px solid var(--color-border)',
          background: 'var(--bg-paper-surface)',
          padding: '0 clamp(14px, 4vw, 24px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          userSelect: 'none',
          boxSizing: 'border-box'
        }}>
          {/* Wordmark */}
          <span style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 'clamp(20px, 5vw, 25px)',
            fontWeight: 400,
            letterSpacing: -0.5,
            color: 'var(--color-ink)',
          }}>
            Lyfpartner
          </span>

          {/* Right: Language selector + nav pill to admin */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Language Switcher */}
            <div style={{
              display: 'flex',
              gap: 2,
              background: 'var(--bg-white)',
              padding: '3px 4px',
              borderRadius: 'var(--radius-full)',
              border: '1.5px solid var(--color-border)'
            }}>
              {[
                { id: 'ha', label: 'HA' },
                { id: 'yo', label: 'YO' },
                { id: 'ig', label: 'IG' },
                { id: 'en', label: 'EN' }
              ].map(l => (
                <button
                  key={l.id}
                  onClick={() => setSelectedLanguage(l.id)}
                  style={{
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: 10,
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    background: selectedLanguage === l.id ? 'var(--color-ink)' : 'transparent',
                    color: selectedLanguage === l.id ? '#FFFFFF' : 'var(--color-ink-secondary)',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>

            {/* Navigation links — icon-only on mobile */}
            <div style={{
              display: 'flex',
              gap: 2,
              background: 'var(--bg-white)',
              padding: '3px 4px',
              borderRadius: 'var(--radius-full)',
              border: '1.5px solid var(--color-border)'
            }}>
              <button
                onClick={() => navigate('stage', '/stage')}
                title="Live Stage Console"
                style={{
                  padding: '5px 10px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 10,
                  fontWeight: 800,
                  fontFamily: 'var(--font-mono)',
                  background: 'transparent',
                  color: 'var(--color-ink-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}
              >
                <ZapIcon size={12} color="var(--color-ink-secondary)" />
                <span style={{ display: 'none' }} className="label-wide">Stage</span>
              </button>
              <button
                onClick={() => navigate('admin', '/admin')}
                title="Bank Admin Portal"
                style={{
                  padding: '5px 10px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 10,
                  fontWeight: 800,
                  fontFamily: 'var(--font-mono)',
                  background: 'transparent',
                  color: 'var(--color-ink-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}
              >
                <LockIcon size={12} color="var(--color-ink-secondary)" />
                <span style={{ display: 'none' }} className="label-wide">Admin</span>
              </button>
            </div>
          </div>
        </header>

        {/* Phone Simulator Only */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <StandalonePhoneView
            selectedLanguage={selectedLanguage}
            onSelectLanguage={setSelectedLanguage}
          />
        </main>
      </div>
    )
  }

  /* ─────────────────────────────────────────────
     ADMIN PORTAL  (/admin)
     Auth-gated, completely separate from simulator
     Full enterprise chrome
  ───────────────────────────────────────────── */
  if (currentRoute === 'admin') {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-paper)',
        color: 'var(--color-ink)'
      }}>
        {/* Admin Header */}
        <header style={{
          height: 60,
          borderBottom: '1.5px solid var(--color-border)',
          background: 'var(--bg-paper-surface)',
          padding: '0 28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          userSelect: 'none',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{
              fontFamily: 'var(--font-serif)',
              fontSize: 25,
              fontWeight: 400,
              letterSpacing: -0.5,
              color: 'var(--color-ink)',
            }}>
              Lyfpartner
            </span>
            <span style={{
              fontSize: 10,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              padding: '3px 10px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(180, 83, 42, 0.1)',
              color: 'var(--color-accent-clay)',
              border: '1px solid rgba(180, 83, 42, 0.25)',
              letterSpacing: 0.5
            }}>
              BANK ADMIN PORTAL
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {staffSession && (
              <span style={{ fontSize: 12, color: 'var(--color-ink-secondary)', fontFamily: 'var(--font-mono)' }}>
                {staffSession.officerName} · {staffSession.staffId}
              </span>
            )}
            <button
              onClick={() => navigate('phone', '/')}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: 11,
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                background: 'var(--bg-white)',
                color: 'var(--color-ink)',
                border: '1.5px solid var(--color-border)',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                cursor: 'pointer'
              }}
            >
              <PhoneIcon size={11} color="var(--color-ink)" />
              Phone Simulator
            </button>
          </div>
        </header>

        <main style={{ flex: 1 }}>
          {staffSession ? (
            <AdminCalls
              staffSession={staffSession}
              onSignOut={handleStaffSignOut}
            />
          ) : (
            <AdminAuthGate onAuthenticated={handleStaffAuthenticated} />
          )}
        </main>
      </div>
    )
  }

  /* ─────────────────────────────────────────────
     STAGE CONSOLE  (/stage)
     Presenter mode with keyboard shortcuts
     Full chrome with stage controls
  ───────────────────────────────────────────── */
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-paper)',
      color: 'var(--color-ink)'
    }}>
      {/* Stage Header */}
      <header style={{
        height: 60,
        borderBottom: '1.5px solid var(--color-border)',
        background: 'var(--bg-paper-surface)',
        padding: '0 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        userSelect: 'none',
        boxShadow: '0 1px 3px rgba(0,0,0,0.02)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span
            onClick={() => navigate('phone', '/')}
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: 27,
              fontWeight: 400,
              letterSpacing: -0.5,
              color: 'var(--color-ink)',
              cursor: 'pointer'
            }}
          >
            Lyfpartner
          </span>
          <span style={{
            fontSize: 10.5,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            padding: '3px 10px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-accent-green-subtle)',
            color: 'var(--color-accent-green)',
            border: '1px solid var(--color-accent-green-border)'
          }}>
            NODE 01 &bull; NIP SANDBOX
          </span>
          {!isPresenterMode && (
            <span style={{ fontSize: 12, color: 'var(--color-ink-tertiary)' }}>
              Inclusive Voice Banking &bull; Stage Evaluation Build
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Language Selector */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            background: 'var(--bg-white)',
            border: '1.5px solid var(--color-border)',
            borderRadius: 'var(--radius-full)',
            padding: '3px 5px'
          }}>
            {[
              { id: 'ha', label: 'Hausa' },
              { id: 'yo', label: 'Yoruba' },
              { id: 'ig', label: 'Igbo' },
              { id: 'en', label: 'English' }
            ].map(lang => (
              <button
                key={lang.id}
                onClick={() => setSelectedLanguage(lang.id)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 11,
                  fontWeight: 800,
                  fontFamily: 'var(--font-mono)',
                  background: selectedLanguage === lang.id ? 'var(--color-ink)' : 'transparent',
                  color: selectedLanguage === lang.id ? '#FFFFFF' : 'var(--color-ink-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                  transition: 'all 0.15s ease'
                }}
              >
                <FlagNG size={12} />
                <span>{lang.label}</span>
              </button>
            ))}
          </div>

          {/* Nav pills */}
          <div style={{
            display: 'flex',
            background: 'var(--bg-white)',
            border: '1.5px solid var(--color-border)',
            borderRadius: 'var(--radius-full)',
            padding: '3px',
            gap: 2
          }}>
            <button
              onClick={() => navigate('phone', '/')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: 11,
                fontWeight: 800,
                background: 'transparent',
                color: 'var(--color-ink-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <PhoneIcon size={12} color="var(--color-ink-secondary)" />
              <span>Phone Simulator</span>
            </button>
            <button
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: 11,
                fontWeight: 800,
                background: 'var(--color-ink)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <ZapIcon size={12} color="#FFFFFF" />
              <span>Live Console</span>
            </button>
            <button
              onClick={() => navigate('admin', '/admin')}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: 11,
                fontWeight: 800,
                background: 'transparent',
                color: 'var(--color-ink-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <LockIcon size={12} color="var(--color-ink-secondary)" />
              <span>Bank Admin</span>
            </button>
          </div>

          {/* Stage Mode Toggle */}
          <button
            onClick={() => setIsPresenterMode(!isPresenterMode)}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              background: isPresenterMode ? 'var(--color-accent-green)' : 'var(--bg-white)',
              color: isPresenterMode ? '#FFFFFF' : 'var(--color-ink)',
              border: `1.5px solid ${isPresenterMode ? 'var(--color-accent-green)' : 'var(--color-border)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
            title="Presenter Mode (Key: P)"
          >
            <span style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: isPresenterMode ? '#FFFFFF' : 'var(--color-accent-green)'
            }} />
            {isPresenterMode ? 'STAGE MODE ON' : 'STAGE MODE'}
          </button>
        </div>
      </header>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <StageView
          isPresenterMode={isPresenterMode}
          selectedLanguage={selectedLanguage}
          onSelectLanguage={setSelectedLanguage}
        />
      </main>

      {/* Keyboard shortcut bar */}
      {!isPresenterMode && (
        <div style={{
          height: 32,
          borderTop: '1px solid var(--color-border-subtle)',
          background: 'var(--bg-paper-surface)',
          padding: '0 28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: 11,
          color: 'var(--color-ink-tertiary)',
          fontFamily: 'var(--font-mono)'
        }}>
          <div>
            Shortcuts: <kbd style={{ padding: '1px 5px', background: 'var(--bg-white)', border: '1px solid var(--color-border)', borderRadius: 3 }}>Space</kbd> Call/End &bull;{' '}
            <kbd style={{ padding: '1px 5px', background: 'var(--bg-white)', border: '1px solid var(--color-border)', borderRadius: 3 }}>P</kbd> Stage Mode
          </div>
          <div>
            Phone Simulator (/) &bull; Live Console (/stage) &bull; Bank Admin (/admin)
          </div>
        </div>
      )}
    </div>
  )
}
