import React, { useState, useEffect, useRef } from 'react'
import {
  Mic, MicOff, PhoneCall, PhoneOff, Volume2, Globe, Shield, RefreshCw,
  Send, User, Bot, AlertTriangle, CheckCircle, Zap
} from 'lucide-react'

const LANGUAGES = [
  { code: 'ha', name: 'Hausa', greeting: 'Sannu barka da zuwa' },
  { code: 'ig', name: 'Igbo', greeting: 'Ndewo nnoo' },
  { code: 'yo', name: 'Yoruba', greeting: 'Bawo e kaabo' },
  { code: 'en-ng', name: 'Nigerian English', greeting: 'Welcome to Lyfpartner' }
]

const DEMO_SCENARIOS = [
  { label: '1. Select Hausa', lang: 'ha', text: 'Sannu Hausa' },
  { label: '2. Spoken PIN (1234)', lang: 'ha', text: '1234' },
  { label: '3. Check Balance', lang: 'ha', text: 'Ina son duba kudi na' },
  { label: '4. Send 5,000 NGN to Musa', lang: 'en-ng', text: 'Send 5,000 naira to Musa' },
  { label: '5. Confirm "Yes"', lang: 'en-ng', text: 'Yes proceed' },
  { label: '6. Pay NEPA Electricity (Yoruba)', lang: 'yo', text: 'Mo fe san owo ina electricity' },
  { label: '7. Angry Caller / Escalate', lang: 'en-ng', text: 'I am angry, I want to speak to a person right now!' }
]

export default function CallDemo() {
  const [inCall, setInCall] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [selectedLang, setSelectedLang] = useState('ha')
  const [authLevel, setAuthLevel] = useState('none')
  const [transcripts, setTranscripts] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)

  const audioRef = useRef(null)
  const transcriptEndRef = useRef(null)

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcripts])

  const startCall = async () => {
    try {
      setIsProcessing(true)
      const res = await fetch('/v1/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'web',
          caller_id: '+2348000000001',
          language: selectedLang
        })
      })
      const data = await res.json()
      setSessionId(data.session_id)
      setAuthLevel(data.auth_level || 'none')
      setInCall(true)

      // Initial greeting turn
      await sendTurn(data.session_id, `Hello in ${selectedLang}`)
    } catch (e) {
      console.error('Failed to start call', e)
    } finally {
      setIsProcessing(false)
    }
  }

  const endCall = async () => {
    if (sessionId) {
      try {
        await fetch(`/v1/sessions/${sessionId}/end`, { method: 'POST' })
      } catch (e) {
        console.error('Error ending session', e)
      }
    }
    setInCall(false)
    setSessionId(null)
    setPendingAction(null)
    setAuthLevel('none')
    if (audioRef.current) {
      audioRef.current.pause()
    }
  }

  const handleLanguageChange = async (langCode) => {
    setSelectedLang(langCode)
    if (sessionId) {
      try {
        await fetch(`/v1/sessions/${sessionId}/language`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ language: langCode })
        })
      } catch (e) {
        console.error('Failed to update language', e)
      }
    }
  }

  const sendTurn = async (activeSessionId, text) => {
    const sId = activeSessionId || sessionId
    if (!sId || !text.trim()) return

    const userText = text.trim()
    setInputMessage('')
    setIsProcessing(true)

    // Add user message to UI
    setTranscripts(prev => [...prev, { speaker: 'caller', text: userText, time: new Date() }])

    try {
      const res = await fetch('/v1/voice/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sId,
          text_input: userText
        })
      })

      const data = await res.json()
      setAuthLevel(data.auth_level || 'none')
      setPendingAction(data.pending_action)

      // Add assistant response
      setTranscripts(prev => [
        ...prev,
        {
          speaker: 'assistant',
          text: data.reply_text,
          time: new Date(),
          intent: data.intent
        }
      ])

      // Play audio if returned
      if (data.reply_audio_base64) {
        playBase64Audio(data.reply_audio_base64)
      }
    } catch (e) {
      console.error('Turn error', e)
      setTranscripts(prev => [
        ...prev,
        { speaker: 'assistant', text: 'Connection issue. Please try again.', time: new Date() }
      ])
    } finally {
      setIsProcessing(false)
    }
  }

  const playBase64Audio = (b64) => {
    try {
      setIsPlayingAudio(true)
      const audioUrl = `data:audio/wav;base64,${b64}`
      if (!audioRef.current) {
        audioRef.current = new Audio(audioUrl)
      } else {
        audioRef.current.src = audioUrl
      }
      audioRef.current.onended = () => setIsPlayingAudio(false)
      audioRef.current.play().catch(e => {
        console.warn('Auto-play prevented:', e)
        setIsPlayingAudio(false)
      })
    } catch (e) {
      console.error('Audio play error', e)
      setIsPlayingAudio(false)
    }
  }

  // Simulated browser mic toggle
  const toggleMic = () => {
    if (!inCall) return
    setIsRecording(!isRecording)
    if (!isRecording) {
      // Simulate listening and then sending
      setTimeout(() => {
        setIsRecording(false)
        sendTurn(sessionId, "What is my balance?")
      }, 2500)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
      {/* Left/Middle Column: Voice Hotline Call Experience */}
      <div className="lg:col-span-2 bg-slate-800/80 rounded-2xl border border-slate-700/60 p-6 flex flex-col h-[750px] shadow-2xl backdrop-blur-md">
        {/* Call Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className={`w-3.5 h-3.5 rounded-full ${inCall ? 'bg-emerald-500 animate-pulse' : 'bg-slate-500'}`} />
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Lyfpartner Voice Hotline
                <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full font-mono">
                  +234 (0) 800-LYF-BANK
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Inclusive voice assistant: Hausa, Igbo, Yoruba, Nigerian English
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`text-xs px-2.5 py-1 rounded-md font-medium border flex items-center gap-1.5 ${
              authLevel === 'full' ? 'bg-purple-500/20 border-purple-500/40 text-purple-300' :
              authLevel === 'basic' ? 'bg-blue-500/20 border-blue-500/40 text-blue-300' :
              'bg-slate-700/50 border-slate-600 text-slate-400'
            }`}>
              <Shield className="w-3.5 h-3.5" />
              Auth: {authLevel.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Language Selector Bar */}
        <div className="py-3 px-1 flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/50 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 font-medium">
            <Globe className="w-3.5 h-3.5" />
            Language:
          </div>
          <div className="flex gap-1.5">
            {LANGUAGES.map(lang => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  selectedLang === lang.code
                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/30 font-semibold'
                    : 'bg-slate-700/70 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {lang.name}
              </button>
            ))}
          </div>
        </div>

        {/* Active Audio Waveform Indicator */}
        <div className="h-12 bg-slate-900/60 rounded-xl my-3 flex items-center justify-center px-4 border border-slate-800">
          {isPlayingAudio ? (
            <div className="flex items-center gap-1.5">
              <Volume2 className="w-4 h-4 text-emerald-400 animate-bounce" />
              <div className="flex items-center">
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
              </div>
              <span className="text-xs text-emerald-400 font-medium ml-2">Speaking response...</span>
            </div>
          ) : isRecording ? (
            <div className="flex items-center gap-2 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
              <span className="text-xs font-semibold">Listening to spoken audio...</span>
            </div>
          ) : (
            <span className="text-xs text-slate-500">
              {inCall ? 'Hotline connected. Speak into mic or use demo triggers below.' : 'Call hotline to begin voice banking.'}
            </span>
          )}
        </div>

        {/* Live Conversation Transcript */}
        <div className="flex-1 overflow-y-auto space-y-3 p-2 pr-3">
          {transcripts.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 p-6">
              <PhoneCall className="w-12 h-12 text-slate-600 mb-3 stroke-[1.5]" />
              <p className="font-semibold text-slate-400">Ready for Live Voice Call</p>
              <p className="text-xs max-w-sm mt-1">
                Click "Start Call" to open a live session. Disabled and low-literacy users can bank entirely hands-free in their native language.
              </p>
            </div>
          ) : (
            transcripts.map((t, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${t.speaker === 'caller' ? 'justify-end' : 'justify-start'}`}
              >
                {t.speaker === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-md ${
                    t.speaker === 'caller'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-slate-700/90 text-slate-100 rounded-bl-none border border-slate-600/50'
                  }`}
                >
                  <p className="leading-relaxed">{t.text}</p>
                  {t.intent && (
                    <span className="inline-block mt-2 text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-900/50 text-slate-300">
                      Intent: {t.intent}
                    </span>
                  )}
                </div>
                {t.speaker === 'caller' && (
                  <div className="w-8 h-8 rounded-full bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-blue-300 shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={transcriptEndRef} />
        </div>

        {/* Pending Confirmation Alert Banner */}
        {pendingAction && (
          <div className="bg-amber-500/15 border border-amber-500/30 rounded-xl p-3 my-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-300 text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong>Confirmation Required:</strong> Send {pendingAction.amount_naira} NGN to {pendingAction.beneficiary_name}?
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => sendTurn(sessionId, "Yes")}
                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold"
              >
                Yes
              </button>
              <button
                onClick={() => sendTurn(sessionId, "No")}
                className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-xs"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Call Controls & Message Input */}
        <div className="pt-3 border-t border-slate-700/60 flex items-center gap-3">
          {!inCall ? (
            <button
              onClick={startCall}
              disabled={isProcessing}
              className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/40 transition-all text-sm"
            >
              <PhoneCall className="w-4 h-4" />
              Start Live Web Call
            </button>
          ) : (
            <>
              <button
                onClick={toggleMic}
                className={`p-3 rounded-xl border flex items-center justify-center transition-all ${
                  isRecording
                    ? 'bg-rose-600 border-rose-500 text-white animate-pulse'
                    : 'bg-slate-700/80 border-slate-600 hover:bg-slate-700 text-slate-200'
                }`}
                title="Microphone (Simulated Speech Input)"
              >
                {isRecording ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
              </button>

              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  sendTurn(sessionId, inputMessage)
                }}
                className="flex-1 flex gap-2"
              >
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Speak into mic or type your turn here..."
                  className="flex-1 bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="submit"
                  disabled={isProcessing || !inputMessage.trim()}
                  className="px-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white rounded-xl flex items-center justify-center transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>

              <button
                onClick={endCall}
                className="p-3 bg-rose-600 hover:bg-rose-500 text-white rounded-xl flex items-center justify-center transition-all shadow-md shadow-rose-950/40"
                title="Hang up"
              >
                <PhoneOff className="w-5 h-5" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Right Column: Interactive Demo Scenarios & Caller Info */}
      <div className="space-y-6">
        {/* Quick Demo Script Panel */}
        <div className="bg-slate-800/80 rounded-2xl border border-slate-700/60 p-5 shadow-xl backdrop-blur-md">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-amber-400" />
            POC Demo Test Scenarios
          </h3>
          <p className="text-xs text-slate-400 mb-3">
            Click any step below to simulate caller voice input across all 7 evaluated hackathon journeys:
          </p>

          <div className="space-y-2">
            {DEMO_SCENARIOS.map((sc, i) => (
              <button
                key={i}
                onClick={async () => {
                  if (!inCall) await startCall()
                  setSelectedLang(sc.lang)
                  sendTurn(sessionId, sc.text)
                }}
                className="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-700/50 border border-slate-800 hover:border-slate-600 transition-all text-xs flex items-center justify-between group"
              >
                <div>
                  <span className="font-semibold text-slate-200 group-hover:text-emerald-400 block">
                    {sc.label}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    "{sc.text}"
                  </span>
                </div>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {sc.lang}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Current Demo Customer Profile Card */}
        <div className="bg-slate-800/80 rounded-2xl border border-slate-700/60 p-5 shadow-xl backdrop-blur-md text-xs">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 mb-3">
            <User className="w-4 h-4 text-blue-400" />
            Active Test Account
          </h3>
          <div className="space-y-2.5">
            <div className="flex justify-between py-1 border-b border-slate-700/40">
              <span className="text-slate-400">Customer Name:</span>
              <span className="font-semibold text-slate-200">Aminu Bello Kano</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-700/40">
              <span className="text-slate-400">Phone Number:</span>
              <span className="font-mono text-slate-200">+234 800 000 0001</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-700/40">
              <span className="text-slate-400">Account Number:</span>
              <span className="font-mono text-slate-200">0123456789</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-700/40">
              <span className="text-slate-400">Opening Balance:</span>
              <span className="font-bold text-emerald-400">250,000 NGN</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Spoken PIN:</span>
              <span className="font-mono text-slate-300">1234 (Argon2 Hashed)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
