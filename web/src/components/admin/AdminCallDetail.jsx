import React, { useState, useEffect } from 'react'
import { SearchIcon, UserIcon, BotIcon } from '../common/Icons'

export default function AdminCallDetail({ sessionId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('transcript') // 'transcript' | 'audit' | 'tech'

  useEffect(() => {
    if (!sessionId) return
    const fetchDetail = async () => {
      try {
        setLoading(true)
        setError(null)
        const res = await fetch(`/v1/admin/calls/${sessionId}`)
        if (res.ok) {
          setData(await res.json())
        } else {
          throw new Error('Could not load call details')
        }
      } catch (e) {
        console.error(e)
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchDetail()
  }, [sessionId])

  if (!sessionId) {
    return (
      <div style={{
        background: 'var(--bg-white)',
        border: '1.5px solid var(--color-border)',
        borderRadius: 'var(--radius-xl)',
        padding: 40,
        textAlign: 'center',
        color: 'var(--color-ink-tertiary)',
        fontSize: 13,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: 'var(--shadow-card)'
      }}>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: '50%',
          background: 'var(--bg-paper-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-ink-tertiary)',
          marginBottom: 12
        }}>
          <SearchIcon size={20} />
        </div>
        <p style={{ margin: 0, fontWeight: 700, color: 'var(--color-ink-secondary)' }}>
          Session Inspector
        </p>
        <p style={{ margin: '4px 0 0', fontSize: 12 }}>
          Select a call record from the left table to inspect its turns and sensitive audit trail.
        </p>
      </div>
    )
  }

  const isEscalated = data?.session?.outcome === 'escalated'

  return (
    <div style={{
      background: 'var(--bg-white)',
      border: '1.5px solid var(--color-border)',
      borderRadius: 'var(--radius-xl)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      boxShadow: 'var(--shadow-card)'
    }}>
      {/* Detail Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--color-border)',
        background: 'var(--bg-paper-surface)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <span style={{ fontSize: 13, fontWeight: 800, color: 'var(--color-ink)' }}>
            Session Intelligence Inspector
          </span>
          <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--color-ink-tertiary)', display: 'block', marginTop: 2 }}>
            {sessionId}
          </span>
        </div>

        {data?.session && (
          <span style={{
            fontSize: 10,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            background: isEscalated ? 'var(--color-accent-clay-subtle)' : 'var(--color-accent-green-subtle)',
            color: isEscalated ? 'var(--color-accent-clay)' : 'var(--color-accent-green)',
            border: `1.5px solid ${isEscalated ? 'var(--color-accent-clay-border)' : 'var(--color-accent-green-border)'}`
          }}>
            STATUS: {(data.session.outcome || 'completed').toUpperCase()}
          </span>
        )}
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--color-border)',
        background: 'var(--bg-white)',
        padding: '0 20px',
        gap: 6
      }}>
        {[
          { id: 'transcript', label: 'Audio Transcript' },
          { id: 'audit', label: `Audit Log (${data?.audit_logs?.length || 0})` },
          { id: 'tech', label: 'Security Context' }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{
              padding: '12px 14px',
              fontSize: 11.5,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              borderBottom: activeTab === t.id ? '2.5px solid var(--color-ink)' : '2.5px solid transparent',
              color: activeTab === t.id ? 'var(--color-ink)' : 'var(--color-ink-tertiary)',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Detail Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 14, maxHeight: 460 }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-ink-secondary)', fontSize: 12 }}>
            Loading session intelligence...
          </div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-accent-clay)', fontSize: 12 }}>
            {error}
          </div>
        ) : data ? (
          <>
            {/* Meta Row */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 10,
              padding: '12px 14px',
              background: 'var(--bg-paper-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border-subtle)',
              fontSize: 11,
              fontFamily: 'var(--font-mono)'
            }}>
              <div>
                <span style={{ color: 'var(--color-ink-tertiary)', display: 'block', fontSize: 9.5, fontWeight: 700 }}>CALLER PHONE</span>
                <span style={{ fontWeight: 800, color: 'var(--color-ink)', marginTop: 2, display: 'block' }}>{data.session.caller_id || '--'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--color-ink-tertiary)', display: 'block', fontSize: 9.5, fontWeight: 700 }}>AUTH LEVEL</span>
                <span style={{ fontWeight: 800, color: 'var(--color-accent-green)', marginTop: 2, display: 'block' }}>{(data.session.auth_level || 'none').toUpperCase()}</span>
              </div>
              <div>
                <span style={{ color: 'var(--color-ink-tertiary)', display: 'block', fontSize: 9.5, fontWeight: 700 }}>TOTAL TURNS</span>
                <span style={{ fontWeight: 800, color: 'var(--color-ink)', marginTop: 2, display: 'block' }}>{data.session.turn_count || 0}</span>
              </div>
            </div>

            {/* Tab: Transcript */}
            {activeTab === 'transcript' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                {data.transcript && data.transcript.length > 0 ? (
                  data.transcript.map((t, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '12px 14px',
                        borderRadius: 'var(--radius-md)',
                        background: t.speaker === 'caller' ? 'var(--bg-paper-surface)' : 'var(--color-accent-green-subtle)',
                        border: `1.5px solid ${t.speaker === 'caller' ? 'var(--color-border-subtle)' : 'var(--color-accent-green-border)'}`,
                        lineHeight: 1.45,
                        animation: 'slideInUp 0.25s ease'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{
                          fontWeight: 800,
                          fontSize: 10,
                          color: t.speaker === 'caller' ? 'var(--color-ink)' : 'var(--color-accent-green)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4
                        }}>
                          {t.speaker === 'caller' ? <UserIcon size={11} color="var(--color-ink)" /> : <BotIcon size={11} color="var(--color-accent-green)" />}
                          <span>{t.speaker === 'caller' ? 'CALLER' : 'LYFPARTNER ASSISTANT'}</span>
                        </span>
                        <span style={{ fontSize: 10, color: 'var(--color-ink-tertiary)' }}>
                          {new Date(t.time).toLocaleTimeString('en-GB')}
                        </span>
                      </div>
                      <p style={{ margin: 0, color: 'var(--color-ink)', fontFamily: 'var(--font-sans)', fontSize: 12.5 }}>
                        {t.text}
                      </p>
                    </div>
                  ))
                ) : (
                  <p style={{ color: 'var(--color-ink-tertiary)', fontStyle: 'italic', fontSize: 12, padding: 20, textAlign: 'center' }}>
                    No recorded transcript turns for this session.
                  </p>
                )}
              </div>
            )}

            {/* Tab: Audit Log */}
            {activeTab === 'audit' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                {data.audit_logs && data.audit_logs.length > 0 ? (
                  data.audit_logs.map((a, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border-subtle)',
                        background: 'var(--bg-paper-surface)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 800, color: 'var(--color-ink)' }}>{a.action}</span>
                        <span style={{ color: 'var(--color-ink-tertiary)', marginLeft: 8 }}>
                          {new Date(a.time).toLocaleTimeString('en-GB')}
                        </span>
                      </div>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 9.5,
                        fontWeight: 800,
                        background: a.result === 'success' ? 'var(--color-accent-green-subtle)' : 'var(--color-accent-clay-subtle)',
                        color: a.result === 'success' ? 'var(--color-accent-green)' : 'var(--color-accent-clay)'
                      }}>
                        {a.result.toUpperCase()}
                      </span>
                    </div>
                  ))
                ) : (
                  <p style={{ color: 'var(--color-ink-tertiary)', fontStyle: 'italic', fontSize: 12, padding: 20, textAlign: 'center' }}>
                    No sensitive audit events recorded.
                  </p>
                )}
              </div>
            )}

            {/* Tab: Technical Metadata */}
            {activeTab === 'tech' && (
              <div style={{
                background: 'var(--bg-paper-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                fontFamily: 'var(--font-mono)',
                fontSize: 11
              }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'var(--color-ink)' }}>
                  {JSON.stringify(data.session, null, 2)}
                </pre>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  )
}
