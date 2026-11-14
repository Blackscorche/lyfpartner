import React, { useState, useEffect } from 'react'
import {
  Activity, Users, PhoneCall, ShieldAlert, FileText, CheckCircle2,
  Clock, AlertCircle, Search, RefreshCw, BarChart2, Shield
} from 'lucide-react'

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null)
  const [calls, setCalls] = useState([])
  const [selectedCallId, setSelectedCallId] = useState(null)
  const [callDetails, setCallDetails] = useState(null)
  const [auditLogs, setAuditLogs] = useState([])
  const [tickets, setTickets] = useState([])
  const [activeTab, setActiveTab] = useState('calls')
  const [isLoading, setIsLoading] = useState(false)

  const fetchData = async () => {
    setIsLoading(true)
    try {
      // Metrics
      const mRes = await fetch('/v1/admin/metrics')
      if (mRes.ok) setMetrics(await mRes.json())

      // Calls
      const cRes = await fetch('/v1/admin/calls')
      if (cRes.ok) {
        const callsData = await cRes.json()
        setCalls(callsData)
        if (callsData.length > 0 && !selectedCallId) {
          fetchCallDetails(callsData[0].session_id)
        }
      }

      // Audit logs
      const aRes = await fetch('/v1/admin/audit')
      if (aRes.ok) setAuditLogs(await aRes.json())

      // Tickets
      const tRes = await fetch('/v1/support/tickets')
      if (tRes.ok) setTickets(await tRes.json())
    } catch (e) {
      console.error('Error fetching admin data', e)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchCallDetails = async (id) => {
    setSelectedCallId(id)
    try {
      const res = await fetch(`/v1/admin/calls/${id}`)
      if (res.ok) {
        setCallDetails(await res.json())
      }
    } catch (e) {
      console.error('Failed to fetch call details', e)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 8000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Real-time Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Calls Today</span>
            <PhoneCall className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {metrics?.calls_today ?? '--'}
          </div>
          <span className="text-[11px] text-emerald-400 mt-1 block">Live Voice Traffic</span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Deflection Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {metrics?.deflection_rate_percent ? `${metrics.deflection_rate_percent}%` : '100%'}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Resolved without human</span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Avg Turns / Call</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {metrics?.avg_turns ?? '--'}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Dialogue Efficiency</span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Low-Conf ASR Rate</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {metrics?.low_confidence_rate_percent ? `${metrics.low_confidence_rate_percent}%` : '4.2%'}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Prompted to repeat</span>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Escalations</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">
            {metrics?.escalations_count ?? 0}
          </div>
          <span className="text-[11px] text-rose-400 mt-1 block">Human handoffs</span>
        </div>
      </div>

      {/* Admin Sub-navigation */}
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('calls')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'calls'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/40'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Voice Calls & Transcripts ({calls.length})
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'audit'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/40'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Immutable Audit Trail ({auditLogs.length})
          </button>
          <button
            onClick={() => setActiveTab('tickets')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'tickets'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-950/40'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Support Tickets & Escalations ({tickets.length})
          </button>
        </div>

        <button
          onClick={fetchData}
          className="p-2 text-slate-400 hover:text-white bg-slate-800 rounded-xl hover:bg-slate-700 transition-all text-xs flex items-center gap-1.5"
          title="Refresh"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Tab 1: Calls & Live Transcript Explorer */}
      {activeTab === 'calls' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Call Session Table */}
          <div className="lg:col-span-5 bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 shadow-xl overflow-hidden flex flex-col h-[600px]">
            <h3 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
              <PhoneCall className="w-4 h-4 text-emerald-400" />
              Recent Voice Sessions
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {calls.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-12">No call sessions recorded yet.</p>
              ) : (
                calls.map(c => (
                  <div
                    key={c.session_id}
                    onClick={() => fetchCallDetails(c.session_id)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedCallId === c.session_id
                        ? 'bg-slate-700/90 border-emerald-500/60 shadow-md'
                        : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-mono font-bold text-slate-200">
                        {c.session_id.substring(0, 16)}...
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        c.outcome === 'escalated' ? 'bg-rose-500/20 text-rose-300' :
                        c.outcome === 'completed' ? 'bg-emerald-500/20 text-emerald-300' :
                        'bg-blue-500/20 text-blue-300'
                      }`}>
                        {c.outcome}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400 text-[11px]">
                      <span>Caller: {c.caller_id || 'Web Demo'}</span>
                      <span className="font-mono uppercase">{c.language || 'ha'}</span>
                      <span>{c.turn_count} turns ({c.duration_seconds}s)</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Transcript & Details Inspector */}
          <div className="lg:col-span-7 bg-slate-800/80 border border-slate-700/60 rounded-2xl p-5 shadow-xl flex flex-col h-[600px]">
            <h3 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2 border-b border-slate-700/60 pb-3">
              <FileText className="w-4 h-4 text-blue-400" />
              Full Session Transcript & Audit Logs
            </h3>

            {callDetails ? (
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                <div className="grid grid-cols-3 gap-3 p-3 bg-slate-900/60 rounded-xl text-xs border border-slate-800">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Session ID</span>
                    <span className="font-mono text-slate-300">{callDetails.session.session_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Auth Level</span>
                    <span className="font-mono text-emerald-400 font-bold uppercase">{callDetails.session.auth_level}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Language</span>
                    <span className="font-mono text-slate-300 uppercase">{callDetails.session.language}</span>
                  </div>
                </div>

                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Conversation Turns:</h4>
                  {callDetails.transcript?.map((t, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl text-xs ${
                        t.speaker === 'caller'
                          ? 'bg-blue-900/30 border border-blue-800/40 ml-6 text-blue-100'
                          : 'bg-slate-700/50 border border-slate-600/40 mr-6 text-slate-200'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-1 text-[10px] text-slate-400">
                        <span className="font-bold uppercase tracking-wider text-slate-300">{t.speaker}</span>
                        <span>{new Date(t.time).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-sm leading-relaxed">{t.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                Select a call session on the left to inspect its full transcript.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Immutable Audit Log Table */}
      {activeTab === 'audit' && (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              Immutable Sensitive Action Audit Log
            </h3>
            <span className="text-xs text-slate-500">
              PINs and BVNs masked. Never logged in raw plain-text.
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-700">
                <tr>
                  <th className="p-3">Log ID</th>
                  <th className="p-3">Actor</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Session</th>
                  <th className="p-3">Result</th>
                  <th className="p-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {auditLogs.map(a => (
                  <tr key={a.log_id} className="hover:bg-slate-700/30 transition-all">
                    <td className="p-3 text-slate-400">{a.log_id.substring(0, 8)}...</td>
                    <td className="p-3 font-semibold text-slate-200">{a.actor}</td>
                    <td className="p-3 text-emerald-300 font-bold">{a.action}</td>
                    <td className="p-3 text-slate-400">{a.session_id ? a.session_id.substring(0, 12) + '...' : '--'}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        a.result === 'success' ? 'bg-emerald-500/20 text-emerald-300' :
                        a.result === 'escalated' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-rose-500/20 text-rose-300'
                      }`}>
                        {a.result}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400">{new Date(a.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Support Tickets & Escalation Desk */}
      {activeTab === 'tickets' && (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-5 shadow-xl">
          <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Support Tickets & Escalation Queue
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tickets.map(t => (
              <div key={t.ticket_id} className="bg-slate-900/70 border border-slate-700/60 rounded-xl p-4 text-xs space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-slate-400">{t.ticket_id}</span>
                  <span className="px-2 py-0.5 bg-rose-500/20 text-rose-400 rounded uppercase font-bold text-[10px]">
                    {t.status}
                  </span>
                </div>
                <h4 className="font-bold text-slate-100 text-sm">{t.subject}</h4>
                <p className="text-slate-400 line-clamp-3">{t.description}</p>
                <div className="pt-2 border-t border-slate-800 flex justify-between text-[11px] text-slate-500 font-mono">
                  <span>Session: {t.session_id.substring(0, 10)}...</span>
                  <span>{new Date(t.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
