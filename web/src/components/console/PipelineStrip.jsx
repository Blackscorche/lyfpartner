import React from 'react'
import { MicIcon, BrainIcon, ZapIcon, ShieldIcon, BankIcon, SpeakerIcon } from '../common/Icons'

export default function PipelineStrip({ stages = {} }) {
  const STAGE_DEFS = [
    { key: 'mic', name: 'Mic In', sub: 'WebAudio', icon: MicIcon, defaultLatency: 12 },
    { key: 'asr', name: 'N-ATLAS ASR', sub: 'Whisper NG', icon: BrainIcon, defaultLatency: 240 },
    { key: 'intent', name: 'Agent NLU', sub: 'Intent & Tools', icon: ZapIcon, defaultLatency: 65 },
    { key: 'auth', name: 'Voice Auth', sub: 'Argon2 / Vector', icon: ShieldIcon, defaultLatency: 35 },
    { key: 'bank', name: 'Core Bank', sub: 'NIP Sandbox', icon: BankIcon, defaultLatency: 52 },
    { key: 'tts', name: 'Spitch TTS', sub: 'Native Voice', icon: SpeakerIcon, defaultLatency: 180 }
  ]

  return (
    <div style={{
      background: 'var(--bg-white)',
      border: '1.5px solid var(--color-border)',
      borderRadius: 'var(--radius-xl)',
      padding: '16px 20px',
      boxShadow: 'var(--shadow-card)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Top Header with Live Flow Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 26,
            height: 26,
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-accent-green-subtle)',
            border: '1px solid var(--color-accent-green-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-accent-green)'
          }}>
            <ZapIcon size={14} />
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
              Neural Pipeline Execution
            </span>
            <span style={{ fontSize: 10.5, color: 'var(--color-ink-tertiary)', display: 'block', fontFamily: 'var(--font-mono)' }}>
              Sub-second asynchronous streaming orchestration
            </span>
          </div>
        </div>

        {/* Live Animative Pulse Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--color-accent-green-subtle)',
          padding: '4px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--color-accent-green-border)'
        }}>
          <span style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--color-accent-green)',
            animation: 'pulseGlow 2s infinite'
          }} />
          <span style={{
            fontSize: 10,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-accent-green)'
          }}>
            TELEMETRY LIVE
          </span>
        </div>
      </div>

      {/* 6 Stage Rounded Cards with Connection Flow */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(6, 1fr)',
        gap: 10,
        position: 'relative'
      }}>
        {STAGE_DEFS.map((s, idx) => {
          const stageState = stages[s.key] || { active: false, latencyMs: s.defaultLatency, status: 'IDLE' }
          const isActive = stageState.active
          const isDone = stageState.status === 'OK' || stageState.status === 'DONE'
          const IconComp = s.icon

          return (
            <div
              key={s.key}
              style={{
                background: isActive
                  ? 'var(--color-accent-green-subtle)'
                  : isDone
                  ? 'var(--bg-paper-surface)'
                  : 'var(--bg-white)',
                border: `1.5px solid ${isActive ? 'var(--color-accent-green)' : isDone ? 'var(--color-accent-green-border)' : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-md)',
                padding: '12px 10px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minHeight: 88,
                position: 'relative',
                transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
                transform: isActive ? 'translateY(-2px)' : 'none',
                boxShadow: isActive
                  ? '0 8px 20px rgba(14, 90, 60, 0.2), 0 0 0 1px var(--color-accent-green)'
                  : '0 2px 6px rgba(0,0,0,0.02)'
              }}
            >
              {/* Header Row */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{
                  fontSize: 10,
                  fontWeight: 800,
                  color: isActive ? 'var(--color-accent-green)' : 'var(--color-ink-tertiary)',
                  fontFamily: 'var(--font-mono)'
                }}>
                  0{idx + 1}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  {isActive && (
                    <div style={{ display: 'flex', gap: 1.5, alignItems: 'flex-end', height: 10 }}>
                      <span style={{ width: 1.5, height: 6, background: 'var(--color-accent-green)', borderRadius: 1, animation: 'liveWaveDance 0.6s infinite alternate' }} />
                      <span style={{ width: 1.5, height: 10, background: 'var(--color-accent-green)', borderRadius: 1, animation: 'liveWaveDance 0.6s infinite alternate 0.2s' }} />
                      <span style={{ width: 1.5, height: 4, background: 'var(--color-accent-green)', borderRadius: 1, animation: 'liveWaveDance 0.6s infinite alternate 0.4s' }} />
                    </div>
                  )}
                  <span style={{
                    width: 7,
                    height: 7,
                    borderRadius: '50%',
                    background: isActive
                      ? 'var(--color-accent-green)'
                      : isDone
                      ? 'var(--color-accent-green)'
                      : 'var(--color-border-strong)',
                    boxShadow: isActive ? '0 0 8px var(--color-accent-green)' : 'none'
                  }} />
                </div>
              </div>

              {/* Title & Sub */}
              <div style={{ margin: '6px 0 4px' }}>
                <div style={{
                  fontSize: 12,
                  fontWeight: 800,
                  color: 'var(--color-ink)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5
                }}>
                  <IconComp size={12} color={isActive ? 'var(--color-accent-green)' : 'var(--color-ink-secondary)'} />
                  <span>{s.name}</span>
                </div>
                <div style={{
                  fontSize: 10,
                  color: 'var(--color-ink-tertiary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {s.sub}
                </div>
              </div>

              {/* Latency Pill */}
              <div style={{
                fontSize: 10.5,
                fontFamily: 'var(--font-mono)',
                color: isActive ? 'var(--color-accent-green)' : 'var(--color-ink-secondary)',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: isActive ? '#FFFFFF' : 'var(--bg-white)',
                padding: '3px 6px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--color-border-subtle)'
              }}>
                <span>{stageState.latencyMs}ms</span>
                <span style={{
                  fontSize: 8,
                  fontWeight: 800,
                  color: isActive ? 'var(--color-accent-green)' : 'var(--color-ink-muted)'
                }}>
                  {isActive ? 'EXEC' : isDone ? 'DONE' : 'IDLE'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
