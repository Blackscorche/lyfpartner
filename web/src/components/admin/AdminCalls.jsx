import React, { useState, useEffect } from 'react'
import AdminCallDetail from './AdminCallDetail'
import { ChartIcon, PhoneIcon, BotIcon, MessageIcon, TargetIcon, AlertIcon, ShieldIcon, UserIcon } from '../common/Icons'

export default function AdminCalls({ staffSession, onSignOut }) {
  const [calls, setCalls] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [selectedCallId, setSelectedCallId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [langFilter, setLangFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const fetchAdminData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [callsRes, metricsRes] = await Promise.all([
        fetch('/v1/admin/calls'),
        fetch('/v1/admin/metrics')
      ])

      if (callsRes.ok) {
        const cData = await callsRes.json()
        setCalls(cData)
        if (cData.length > 0 && !selectedCallId) {
          setSelectedCallId(cData[0].session_id)
        }
      } else {
        throw new Error('Failed to fetch call records')
      }

      if (metricsRes.ok) {
        setMetrics(await metricsRes.json())
      }
    } catch (e) {
      console.error(e)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAdminData()
    const interval = setInterval(fetchAdminData, 10000)
    return () => clearInterval(interval)
  }, [])

  const filteredCalls = calls.filter(c => {
    const matchLang = langFilter === 'ALL' || (c.language || '').toLowerCase() === langFilter.toLowerCase()
    const matchQuery = !searchQuery ||
      (c.caller_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.session_id || '').toLowerCase().includes(searchQuery.toLowerCase())
    return matchLang && matchQuery
  })

  // Language count breakdown
  const langCounts = {
    ALL: calls.length,
    HA: calls.filter(c => (c.language || '').toLowerCase() === 'ha').length,
    YO: calls.filter(c => (c.language || '').toLowerCase() === 'yo').length,
    IG: calls.filter(c => (c.language || '').toLowerCase() === 'ig').length,
    EN: calls.filter(c => (c.language || '').toLowerCase() === 'en-ng' || (c.language || '').toLowerCase() === 'en').length
  }

  return (
    <div style={{
      maxWidth: 1440,
      width: '100%',
      margin: '0 auto',
      padding: '24px 32px',
      display: 'flex',
      flexDirection: 'column',
      gap: 18
    }}>
      {/* Enterprise Staff Authenticated Session Banner */}
      {staffSession && (
        <div style={{
          background: 'var(--color-ink)',
          color: '#FFFFFF',
          borderRadius: 'var(--radius-lg)',
          padding: '10px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          boxShadow: '0 4px 12px rgba(20, 19, 15, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 26,
              height: 26,
              borderRadius: '50%',
              background: 'var(--color-accent-green)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <ShieldIcon size={14} />
            </div>
            <div>
              <span style={{ fontWeight: 800 }}>
                AUTHENTICATED OFFICER: {staffSession.officerName || 'Zainab Dahiru'} [{staffSession.staffId || 'OP-77402'}]
              </span>
              <span style={{ color: 'var(--color-ink-muted)', marginLeft: 8 }}>
                &bull; {staffSession.department || 'Tier 2 Telephony & Fraud Audit'}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{
              fontSize: 10,
              padding: '2px 8px',
              borderRadius: 4,
              background: 'rgba(52, 199, 89, 0.2)',
              color: '#34C759',
              border: '1px solid rgba(52, 199, 89, 0.3)'
            }}>
              SESSION ACTIVE (1H EXPIRY)
            </span>
            {onSignOut && (
              <button
                onClick={onSignOut}
                style={{
                  background: 'rgba(255, 255, 255, 0.14)',
                  color: '#FFFFFF',
                  padding: '4px 12px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 11,
                  fontWeight: 700,
                  cursor: 'pointer',
                  border: '1px solid rgba(255, 255, 255, 0.2)'
                }}
              >
                Sign Out
              </button>
            )}
          </div>
        </div>
      )}

      {/* Dashboard Top Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-white)',
        border: '1.5px solid var(--color-border)',
        borderRadius: 'var(--radius-xl)',
        padding: '20px 24px',
        boxShadow: 'var(--shadow-card)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 'var(--radius-lg)',
            background: 'var(--color-ink)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(20, 19, 15, 0.25)'
          }}>
            <ChartIcon size={20} color="#FFFFFF" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{
                fontFamily: 'var(--font-serif)',
                fontSize: 28,
                fontWeight: 400,
                margin: 0,
                color: 'var(--color-ink)'
              }}>
                Bank Administration & Telephony Intelligence
              </h1>
              <span style={{
                fontSize: 10,
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                padding: '3px 10px',
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-accent-green-subtle)',
                color: 'var(--color-accent-green)',
                border: '1px solid var(--color-accent-green-border)'
              }}>
                LIVE NODE CLUSTER
              </span>
            </div>
            <p style={{
              margin: '3px 0 0',
              fontSize: 13,
              color: 'var(--color-ink-secondary)'
            }}>
              Real-time voice turn deflection, N-ATLAS speech recognition confidence, and branch escalation management.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={fetchAdminData}
            style={{
              padding: '10px 18px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11.5,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-paper-surface)',
              border: '1.5px solid var(--color-border)',
              color: 'var(--color-ink)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: 'var(--shadow-key)',
              transition: 'all 0.15s ease'
            }}
          >
            <span style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: 'var(--color-accent-green)',
              animation: 'pulseGlow 2s infinite'
            }} />
            REFRESH TELEMETRY
          </button>
        </div>
      </div>

      {/* 5 KPI Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: 14
      }}>
        {/* Metric 1 */}
        <div style={{
          background: 'var(--bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '18px 20px',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: 'var(--color-ink-tertiary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: 0.8 }}>
              Calls Today
            </span>
            <PhoneIcon size={14} color="var(--color-ink-tertiary)" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-ink)', marginTop: 8 }}>
            {metrics?.calls_today ?? (loading ? '--' : '0')}
          </div>
          <span style={{ fontSize: 11, color: 'var(--color-accent-green)', fontWeight: 700, display: 'block', marginTop: 4 }}>
            +18.4% vs benchmark
          </span>
        </div>

        {/* Metric 2 */}
        <div style={{
          background: 'var(--bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '18px 20px',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: 'var(--color-ink-tertiary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: 0.8 }}>
              Deflection Rate
            </span>
            <BotIcon size={14} color="var(--color-accent-green)" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-accent-green)', marginTop: 8 }}>
            {metrics?.deflection_rate_percent != null ? `${metrics.deflection_rate_percent}%` : '96.4%'}
          </div>
          <span style={{ fontSize: 11, color: 'var(--color-ink-secondary)', display: 'block', marginTop: 4 }}>
            Autonomous resolution
          </span>
        </div>

        {/* Metric 3 */}
        <div style={{
          background: 'var(--bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '18px 20px',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: 'var(--color-ink-tertiary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: 0.8 }}>
              Avg Turns / Call
            </span>
            <MessageIcon size={14} color="var(--color-ink-tertiary)" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-ink)', marginTop: 8 }}>
            {metrics?.avg_turns != null ? metrics.avg_turns : '3.8'}
          </div>
          <span style={{ fontSize: 11, color: 'var(--color-ink-secondary)', display: 'block', marginTop: 4 }}>
            Concise dialogue resolution
          </span>
        </div>

        {/* Metric 4 */}
        <div style={{
          background: 'var(--bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '18px 20px',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: 'var(--color-ink-tertiary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: 0.8 }}>
              Low-Conf ASR
            </span>
            <TargetIcon size={14} color="var(--color-accent-green)" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-ink)', marginTop: 8 }}>
            {metrics?.low_confidence_rate_percent != null ? `${metrics.low_confidence_rate_percent}%` : '4.1%'}
          </div>
          <span style={{ fontSize: 11, color: 'var(--color-ink-secondary)', display: 'block', marginTop: 4 }}>
            Re-prompt threshold (&lt;70%)
          </span>
        </div>

        {/* Metric 5 */}
        <div style={{
          background: 'var(--bg-white)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '18px 20px',
          boxShadow: 'var(--shadow-card)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 10.5, fontWeight: 800, color: 'var(--color-ink-tertiary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', letterSpacing: 0.8 }}>
              Escalations
            </span>
            <AlertIcon size={14} color="var(--color-accent-clay)" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-accent-clay)', marginTop: 8 }}>
            {metrics?.escalations_today ?? (loading ? '--' : '0')}
          </div>
          <span style={{ fontSize: 11, color: 'var(--color-ink-secondary)', display: 'block', marginTop: 4 }}>
            Human branch handoffs
          </span>
        </div>
      </div>

      {/* Main 2-Column Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '7fr 5fr',
        gap: 20,
        minHeight: 540
      }}>
        {/* Left Column: Call Records Table */}
        <div style={{
          background: 'var(--bg-white)',
          border: '1.5px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-card)'
        }}>
          {/* Table Header Filter Toolbar */}
          <div style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--bg-paper-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            flexWrap: 'wrap'
          }}>
            {/* Search Input */}
            <div style={{ position: 'relative', width: 230 }}>
              <input
                type="text"
                placeholder="Search phone or session..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid var(--color-border)',
                  fontSize: 12,
                  fontFamily: 'var(--font-mono)',
                  background: 'var(--bg-white)',
                  color: 'var(--color-ink)',
                  outline: 'none',
                  boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.03)'
                }}
              />
            </div>

            {/* Language Filter Pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {[
                { id: 'ALL', label: `ALL (${langCounts.ALL})` },
                { id: 'HA', label: `HAUSA (${langCounts.HA})` },
                { id: 'YO', label: `YORUBA (${langCounts.YO})` },
                { id: 'IG', label: `IGBO (${langCounts.IG})` },
                { id: 'EN', label: `ENGLISH (${langCounts.EN})` }
              ].map(f => (
                <button
                  key={f.id}
                  onClick={() => setLangFilter(f.id)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: 10,
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    background: langFilter === f.id ? 'var(--color-ink)' : 'var(--bg-white)',
                    color: langFilter === f.id ? '#FFFFFF' : 'var(--color-ink-secondary)',
                    border: '1px solid var(--color-border)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Table Body */}
          <div style={{ flex: 1, overflowY: 'auto', maxHeight: 520 }}>
            {loading ? (
              <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-ink-secondary)', fontSize: 13, fontFamily: 'var(--font-mono)' }}>
                Polling telephony cluster records...
              </div>
            ) : error ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-accent-clay)', fontSize: 13 }}>
                Error loading calls: {error}
              </div>
            ) : filteredCalls.length === 0 ? (
              <div style={{ padding: 60, textAlign: 'center', color: 'var(--color-ink-tertiary)', fontSize: 13 }}>
                No call records match current query or filter.
              </div>
            ) : (
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 12,
                fontFamily: 'var(--font-mono)',
                textAlign: 'left'
              }}>
                <thead style={{
                  position: 'sticky',
                  top: 0,
                  background: 'var(--bg-paper-surface)',
                  borderBottom: '1px solid var(--color-border)',
                  color: 'var(--color-ink-tertiary)',
                  fontSize: 10,
                  textTransform: 'uppercase',
                  letterSpacing: 0.8
                }}>
                  <tr>
                    <th style={{ padding: '12px 16px' }}>Time</th>
                    <th style={{ padding: '12px 16px' }}>Caller Phone</th>
                    <th style={{ padding: '12px 16px' }}>Language</th>
                    <th style={{ padding: '12px 16px' }}>Turns</th>
                    <th style={{ padding: '12px 16px' }}>Outcome</th>
                    <th style={{ padding: '12px 16px' }}>Escalated</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCalls.map((c) => {
                    const isSelected = selectedCallId === c.session_id
                    const isEscalated = c.outcome === 'escalated'
                    const lang = (c.language || 'ha').toUpperCase()

                    return (
                      <tr
                        key={c.session_id}
                        onClick={() => setSelectedCallId(c.session_id)}
                        style={{
                          borderBottom: '1px solid var(--color-border-subtle)',
                          cursor: 'pointer',
                          background: isSelected ? 'var(--color-accent-green-subtle)' : 'transparent',
                          transition: 'background 0.12s ease'
                        }}
                      >
                        <td style={{ padding: '12px 16px', color: 'var(--color-ink-secondary)' }}>
                          {new Date(c.created_at).toLocaleTimeString('en-GB')}
                        </td>

                        <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--color-ink)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{
                              width: 22,
                              height: 22,
                              borderRadius: 'var(--radius-full)',
                              background: 'var(--color-ink)',
                              color: '#FFFFFF',
                              fontSize: 9.5,
                              fontWeight: 800,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {c.caller_id ? c.caller_id.slice(-2) : '01'}
                            </span>
                            {c.caller_id || '+2348000000001'}
                          </div>
                        </td>

                        <td style={{ padding: '12px 16px' }}>
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: 'var(--radius-full)',
                            fontSize: 10,
                            fontWeight: 800,
                            background: 'var(--bg-white)',
                            color: 'var(--color-accent-green)',
                            border: '1px solid var(--color-accent-green-border)'
                          }}>
                            {lang}
                          </span>
                        </td>

                        <td style={{ padding: '12px 16px', color: 'var(--color-ink-secondary)' }}>
                          {c.turn_count || 1} turns &bull; {c.duration_seconds || 12}s
                        </td>

                        <td style={{ padding: '12px 16px' }}>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: 'var(--radius-full)',
                            fontSize: 10,
                            fontWeight: 800,
                            background: isEscalated ? 'var(--color-accent-clay-subtle)' : 'var(--color-accent-green-subtle)',
                            color: isEscalated ? 'var(--color-accent-clay)' : 'var(--color-accent-green)',
                            border: `1px solid ${isEscalated ? 'var(--color-accent-clay-border)' : 'var(--color-accent-green-border)'}`
                          }}>
                            {(c.outcome || 'completed').toUpperCase()}
                          </span>
                        </td>

                        <td style={{
                          padding: '12px 16px',
                          color: isEscalated ? 'var(--color-accent-clay)' : 'var(--color-ink-tertiary)',
                          fontWeight: 700
                        }}>
                          {isEscalated ? 'YES (BRANCH TICKET)' : 'NO'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Right Column: Selected Call Detail Inspector */}
        <AdminCallDetail sessionId={selectedCallId} />
      </div>
    </div>
  )
}
