import React, { useState } from 'react'
import PipelineStrip from './PipelineStrip'
import TranscriptView from './TranscriptView'
import AuthState from './AuthState'
import Ledger from './Ledger'
import WalkthroughGuide from './WalkthroughGuide'
import { BankIcon, PlayIcon, ActivityIcon } from '../common/Icons'

export default function ConsolePanel({
  pipelineStages = {},
  transcripts = [],
  authState = {},
  transactions = [],
  isRealCallMode = false,
  onToggleRealCallMode,
  isReplayRunning = false,
  onStartReplay,
  onResetSession,
  currentLang = 'ha',
  onSelectLang,
  onSimulatePhrase,
  phoneState = 'lock',
  onStartCall
}) {
  const [showInboundHelp, setShowInboundHelp] = useState(false)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      width: '100%'
    }}>
      {/* Top Operations Header Bar */}
      <div style={{
        background: 'var(--bg-white)',
        border: '1.5px solid var(--color-border)',
        borderRadius: 'var(--radius-xl)',
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-card)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-ink)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(20, 19, 15, 0.25)'
          }}>
            <BankIcon size={18} color="#FFFFFF" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h3 style={{
                fontSize: 14.5,
                fontWeight: 800,
                color: 'var(--color-ink)',
                margin: 0,
                letterSpacing: -0.3
              }}>
                Bank Operations Console
              </h3>
              <span style={{
                fontSize: 10,
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-accent-green-subtle)',
                color: 'var(--color-accent-green)',
                border: '1px solid var(--color-accent-green-border)'
              }}>
                NODE 01 &bull; ONLINE
              </span>
            </div>
            <span style={{ fontSize: 11, color: 'var(--color-ink-tertiary)', fontFamily: 'var(--font-mono)' }}>
              Core Banking &bull; N-ATLAS Speech Engine &bull; Zero-Data Retention
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Replay Full Scripted Demo Button */}
          <button
            onClick={onStartReplay}
            disabled={isReplayRunning}
            style={{
              padding: '7px 14px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 800,
              background: isReplayRunning ? 'var(--color-accent-green)' : 'var(--color-ink)',
              color: '#FFFFFF',
              border: 'none',
              cursor: isReplayRunning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              boxShadow: '0 2px 8px rgba(0,0,0,0.18)',
              transition: 'all 0.15s ease'
            }}
          >
            {isReplayRunning ? <ActivityIcon size={12} color="#FFFFFF" /> : <PlayIcon size={12} color="#FFFFFF" />}
            <span>{isReplayRunning ? 'Replaying...' : 'Replay Full Demo'}</span>
          </button>

          {/* Real Phone Call Mode Toggle */}
          <button
            onClick={() => {
              if (onToggleRealCallMode) onToggleRealCallMode()
              setShowInboundHelp(!showInboundHelp)
            }}
            style={{
              padding: '7px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 800,
              background: isRealCallMode ? 'var(--color-accent-green-subtle)' : 'var(--bg-paper-surface)',
              color: isRealCallMode ? 'var(--color-accent-green)' : 'var(--color-ink)',
              border: `1.5px solid ${isRealCallMode ? 'var(--color-accent-green)' : 'var(--color-border)'}`,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              transition: 'all 0.15s ease'
            }}
          >
            <span style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: isRealCallMode ? 'var(--color-accent-green)' : 'var(--color-ink-tertiary)',
              animation: isRealCallMode ? 'pulseGlow 2s infinite' : 'none'
            }} />
            <span>{isRealCallMode ? 'Inbound Mirror' : 'Real Phone'}</span>
          </button>

          {/* Reset Session */}
          <button
            onClick={onResetSession}
            style={{
              padding: '7px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 700,
              color: 'var(--color-ink-secondary)',
              background: 'var(--bg-paper-surface)',
              border: '1px solid var(--color-border)',
              cursor: 'pointer'
            }}
            title="Reset active voice session"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Inbound Telephony Banner */}
      {showInboundHelp && (
        <div style={{
          background: 'var(--color-accent-green-subtle)',
          border: '1px solid var(--color-accent-green-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '10px 16px',
          fontSize: 12,
          color: 'var(--color-accent-green-hover)',
          lineHeight: 1.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <strong>Live Telephony Inbound:</strong> Dial <strong>+234 1 888 3330</strong> (Africa's Talking NG) or <strong>+1 (205) 555-0199</strong> (Twilio). Inbound calls bridge into this console and mirror in the phone simulator live.
          </div>
          <button
            onClick={() => setShowInboundHelp(false)}
            style={{ color: 'var(--color-accent-green)', fontWeight: 800, fontSize: 16, marginLeft: 14 }}
          >
            &times;
          </button>
        </div>
      )}

      {/* Interactive Walkthrough & Language Guide */}
      <WalkthroughGuide
        currentLang={currentLang}
        onSelectLang={onSelectLang}
        onSimulatePhrase={onSimulatePhrase}
        phoneState={phoneState}
        onStartCall={onStartCall}
        isReplayRunning={isReplayRunning}
        onStartReplay={onStartReplay}
      />

      {/* Pipeline Strip */}
      <PipelineStrip stages={pipelineStages} />

      {/* Dual Voice Transcript View */}
      <TranscriptView entries={transcripts} />

      {/* Auth State Panel */}
      <AuthState
        authLevel={authState.authLevel}
        pinVerified={authState.pinVerified}
        voiceScore={authState.voiceScore}
        isLocked={authState.isLocked}
        failedAttempts={authState.failedAttempts}
      />

      {/* Core Banking Transaction Ledger */}
      <Ledger transactions={transactions} />
    </div>
  )
}
