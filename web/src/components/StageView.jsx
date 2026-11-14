import React, { useState, useEffect, useRef } from 'react'
import PhoneFrame from './phone/PhoneFrame'
import LockScreen from './phone/LockScreen'
import Dialer from './phone/Dialer'
import InCallScreen from './phone/InCallScreen'
import NotificationBanner from './phone/NotificationBanner'
import MessagesView from './phone/MessagesView'
import FeaturePhone from './phone/FeaturePhone'
import ConsolePanel from './console/ConsolePanel'
import {
  startRingback,
  stopRingback,
  playDTMF,
  speakText,
  stopSpeaking,
  playCallConnectSound,
  playCallEndSound
} from '../utils/audio'
import { LANGUAGES } from '../data/languages'

export default function StageView({
  isPresenterMode = false,
  selectedLanguage = 'ha',
  onSelectLanguage
}) {
  // Device simulation states
  const [deviceType, setDeviceType] = useState('iphone') // 'iphone' | 'feature'
  const [phoneState, setPhoneState] = useState('lock') // 'lock' | 'dialer' | 'ringing' | 'incall' | 'ended' | 'messages'
  const [callDuration, setCallDuration] = useState(0)
  const [captionText, setCaptionText] = useState('')
  const [captionLang, setCaptionLang] = useState(selectedLanguage)
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false)
  const [smsReceiptText, setSmsReceiptText] = useState('')
  const [activeSessionId, setActiveSessionId] = useState(null)

  // Console / Bank Operations states
  const [pipelineStages, setPipelineStages] = useState({})
  const [transcripts, setTranscripts] = useState([])
  const [authState, setAuthState] = useState({
    authLevel: 'none',
    pinVerified: false,
    voiceScore: 0.0,
    isLocked: false,
    failedAttempts: 0
  })
  const [transactions, setTransactions] = useState([])
  const [isRealCallMode, setIsRealCallMode] = useState(false)
  const [isReplayRunning, setIsReplayRunning] = useState(false)

  const callTimerRef = useRef(null)
  const replayTimersRef = useRef([])

  // Keep captionLang in sync with selectedLanguage from parent
  useEffect(() => {
    if (selectedLanguage) {
      setCaptionLang(selectedLanguage)
    }
  }, [selectedLanguage])

  // Global Keyboard Shortcuts (F = Fullscreen, Space = Start/End Call)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

      if (e.code === 'Space') {
        e.preventDefault()
        if (phoneState === 'incall' || phoneState === 'ringing') {
          handleEndCall()
        } else {
          handleStartCall('333')
        }
      } else if (e.key === 'f' || e.key === 'F') {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {})
        } else {
          document.exitFullscreen().catch(() => {})
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [phoneState])

  // Call duration timer
  useEffect(() => {
    if (phoneState === 'incall') {
      setCallDuration(0)
      callTimerRef.current = setInterval(() => {
        setCallDuration(prev => prev + 1)
      }, 1000)
    } else {
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current)
        callTimerRef.current = null
      }
    }
    return () => {
      if (callTimerRef.current) clearInterval(callTimerRef.current)
    }
  }, [phoneState])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRingback()
      replayTimersRef.current.forEach(t => clearTimeout(t))
    }
  }, [])

  // Start Call Sequence (Dial 333 -> Ringing -> In-Call)
  const handleStartCall = async (shortCode = '333') => {
    stopRingback()
    setPhoneState('ringing')
    startRingback()

    const langData = LANGUAGES[captionLang] || LANGUAGES.ha

    // Create session in backend
    try {
      const res = await fetch('/v1/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'web',
          caller_id: langData.caller.phone,
          language: captionLang || 'ha'
        })
      })
      if (res.ok) {
        const sData = await res.json()
        setActiveSessionId(sData.session_id)
      }
    } catch (e) {
      console.warn('Backend session fallback:', e)
    }

    // Ringing audio cadence for 2.2s, then answer
    setTimeout(() => {
      stopRingback()
      playCallConnectSound()
      setPhoneState('incall')
      setPipelineStages({
        mic: { active: true, latencyMs: 12, status: 'OK' },
        asr: { active: false, latencyMs: 240, status: 'IDLE' },
        intent: { active: false, latencyMs: 65, status: 'IDLE' },
        auth: { active: false, latencyMs: 35, status: 'IDLE' },
        bank: { active: false, latencyMs: 52, status: 'IDLE' },
        tts: { active: true, latencyMs: 180, status: 'OK' }
      })

      // Language-specific greeting
      const greeting = langData.greeting
      setCaptionText(greeting)
      setIsAssistantSpeaking(true)
      speakText(
        greeting,
        captionLang,
        () => setIsAssistantSpeaking(true),
        () => setIsAssistantSpeaking(false)
      )
      setTranscripts([
        {
          speaker: 'assistant',
          language: captionLang,
          text: greeting,
          timestamp: new Date().toLocaleTimeString('en-GB'),
          confidence: 0.99
        }
      ])
    }, 2200)
  }

  // End Call
  const handleEndCall = () => {
    stopRingback()
    stopSpeaking()
    playCallEndSound()
    setPhoneState('ended')
    setIsAssistantSpeaking(false)
    if (activeSessionId) {
      fetch(`/v1/sessions/${activeSessionId}/end`, { method: 'POST' }).catch(() => {})
    }

    // Default receipt if none generated yet
    if (!smsReceiptText) {
      const langData = LANGUAGES[captionLang] || LANGUAGES.ha
      setSmsReceiptText(`Lyfpatner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8831. Bal: ${langData.caller.balanceFormatted}`)
    }
  }

  // Simulate speaking a phrase in the active language
  const handleSimulatePhrase = async (phrase) => {
    // If not in call, connect call first
    if (phoneState !== 'incall') {
      await handleStartCall('333')
      // wait for call to connect
      setTimeout(() => executeSpokenTurn(phrase), 2400)
    } else {
      executeSpokenTurn(phrase)
    }
  }

  const executeSpokenTurn = async (phrase) => {
    const lang = captionLang || 'ha'

    // Update pipeline to ASR processing
    setPipelineStages({
      mic: { active: true, latencyMs: 14, status: 'OK' },
      asr: { active: true, latencyMs: 220, status: 'ACTIVE' },
      intent: { active: false, latencyMs: 65, status: 'IDLE' },
      auth: { active: false, latencyMs: 35, status: 'IDLE' },
      bank: { active: false, latencyMs: 52, status: 'IDLE' },
      tts: { active: false, latencyMs: 180, status: 'IDLE' }
    })

    // Add caller utterance to transcript
    setTranscripts(prev => [
      ...prev,
      {
        speaker: 'caller',
        language: lang,
        text: phrase.text,
        confidence: 0.98,
        timestamp: new Date().toLocaleTimeString('en-GB')
      }
    ])
    setCaptionText(phrase.text)
    setIsAssistantSpeaking(false)

    // Call backend /v1/voice/turn or simulate intelligent reply
    try {
      const res = await fetch('/v1/voice/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId || 'sess_sim_01',
          text_input: phrase.text
        })
      })

      if (res.ok) {
        const turnData = await res.json()
        handleTurnResponse(phrase, turnData.reply_text, turnData)
        return
      }
    } catch (e) {
      console.warn('Backend turn fallback:', e)
    }

    // Local fallback response if backend turn returned error
    let fallbackReply = ''
    if (phrase.type === 'auth') {
      setAuthState({
        authLevel: 'full',
        pinVerified: true,
        voiceScore: 0.97,
        isLocked: false,
        failedAttempts: 0
      })
      fallbackReply = lang === 'ha'
        ? 'An tabbatar da lambar sirri. Yaya zan iya taimaka muku?'
        : lang === 'yo'
        ? 'A ti fowo si nomba asiri yin. Bawo ni a se le ran yin lowo?'
        : lang === 'ig'
        ? 'A kwadoro nọmba nzuzo gi. Kedu ka m ga-esi nyere gi aka?'
        : 'PIN verified successfully. How can I help you today?'
    } else if (phrase.type === 'inquiry') {
      fallbackReply = lang === 'ha'
        ? 'Kudin ku a asusun banki Naira dubu dari biyu da hamsin (₦250,000.00) ne.'
        : lang === 'yo'
        ? 'Iye owo to ku ninu akaunti yin je egberun lona ogosan Naira (₦180,000.00).'
        : lang === 'ig'
        ? 'Ego fọdụrụ na akaụntụ gi bu puku naira narị atọ na iri abụọ (₦320,000.00).'
        : 'Your account balance is Four Hundred and Ten Thousand Naira (₦410,000.00).'
    } else {
      // Transfer or bill
      setTransactions(prev => [
        {
          reference: `NIP-${Date.now().toString().slice(-8)}`,
          recipient: phrase.type === 'bill' ? 'IKEDC Electric' : 'Musa Bello',
          bank: phrase.type === 'bill' ? 'Utility Payment' : 'First Bank',
          amount_naira: phrase.type === 'bill' ? 6000 : 5000,
          status: 'SETTLED'
        },
        ...prev
      ])
      fallbackReply = lang === 'ha'
        ? 'An tura Naira 5,000 ga Musa Bello cikin nasara. An aiko muku da sakon SMS.'
        : lang === 'yo'
        ? 'A ti san owo ina NEPA egberun mefa Naira laseyori. E o gba SMS nisisiyi.'
        : lang === 'ig'
        ? 'Ezila ₦10,000 nye Chinedu Obi nke ọma. Anyị ezigala ozi SMS.'
        : '₦5,000 has been transferred to Musa Bello successfully. SMS receipt sent.'
    }

    handleTurnResponse(phrase, fallbackReply, {})
  }

  const handleTurnResponse = (phrase, replyText, data) => {
    // Pipeline finishes
    setPipelineStages({
      mic: { active: true, latencyMs: 12, status: 'OK' },
      asr: { active: false, latencyMs: 220, status: 'OK' },
      intent: { active: false, latencyMs: 55, status: 'OK' },
      auth: { active: false, latencyMs: 35, status: 'OK' },
      bank: { active: false, latencyMs: 48, status: 'OK' },
      tts: { active: true, latencyMs: 175, status: 'OK' }
    })

    setTimeout(() => {
      setCaptionText(replyText)
      setIsAssistantSpeaking(true)
      setTranscripts(prev => [
        ...prev,
        {
          speaker: 'assistant',
          language: captionLang,
          text: replyText,
          confidence: 0.99,
          timestamp: new Date().toLocaleTimeString('en-GB')
        }
      ])

      // If phrase was auth, unlock
      if (phrase.type === 'auth') {
        setAuthState({
          authLevel: 'full',
          pinVerified: true,
          voiceScore: 0.96,
          isLocked: false,
          failedAttempts: 0
        })
      }

      setTimeout(() => setIsAssistantSpeaking(false), 3000)
    }, 400)
  }

  // DTMF Keypad in-call handler
  const handleSendDTMF = async (digit) => {
    playDTMF(digit)
    if (!activeSessionId) return
    try {
      const res = await fetch('/v1/voice/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          text_input: digit
        })
      })
      if (res.ok) {
        const turnData = await res.json()
        setCaptionText(turnData.reply_text)
        setIsAssistantSpeaking(true)
        setTimeout(() => setIsAssistantSpeaking(false), 2500)
      }
    } catch (e) {
      console.error(e)
    }
  }

  // Multi-Language Scripted Replay Engine
  const handleStartReplay = () => {
    replayTimersRef.current.forEach(t => clearTimeout(t))
    replayTimersRef.current = []
    stopRingback()

    setIsReplayRunning(true)
    handleResetSession()
    setPhoneState('ringing')
    startRingback()

    const langData = LANGUAGES[captionLang] || LANGUAGES.ha
    const events = langData.replayEvents || []

    events.forEach(event => {
      const timer = setTimeout(() => {
        handleReplayEvent(event)
      }, event.timeMs)
      replayTimersRef.current.push(timer)
    })
  }

  const handleReplayEvent = (event) => {
    const { type, data } = event

    switch (type) {
      case 'call.started':
        stopRingback()
        setPhoneState('incall')
        setPipelineStages({
          mic: { active: true, latencyMs: 12, status: 'OK' },
          asr: { active: false, latencyMs: 240, status: 'IDLE' },
          intent: { active: false, latencyMs: 65, status: 'IDLE' },
          auth: { active: false, latencyMs: 35, status: 'IDLE' },
          bank: { active: false, latencyMs: 52, status: 'IDLE' },
          tts: { active: false, latencyMs: 180, status: 'IDLE' }
        })
        break

      case 'asr.final':
        setCaptionText(data.text)
        setCaptionLang(data.language)
        setIsAssistantSpeaking(false)
        setTranscripts(prev => [
          ...prev,
          {
            speaker: 'caller',
            language: data.language,
            text: data.text,
            confidence: data.confidence,
            timestamp: new Date().toLocaleTimeString('en-GB')
          }
        ])
        setPipelineStages(prev => ({
          ...prev,
          asr: { active: false, latencyMs: data.latencyMs, status: 'OK' },
          intent: { active: true, latencyMs: 45, status: 'ACTIVE' }
        }))
        break

      case 'auth.update':
        setAuthState({
          authLevel: data.auth_level,
          pinVerified: data.pin_verified,
          voiceScore: data.voice_match_score,
          isLocked: data.status === 'LOCKED',
          failedAttempts: 0
        })
        setPipelineStages(prev => ({
          ...prev,
          auth: { active: false, latencyMs: 35, status: 'OK' }
        }))
        break

      case 'tool.call':
        setPipelineStages(prev => ({
          ...prev,
          intent: { active: false, latencyMs: 55, status: 'OK' },
          bank: { active: true, latencyMs: 48, status: 'ACTIVE' }
        }))
        break

      case 'transfer.confirmed':
        setTransactions(prev => [
          {
            reference: data.reference,
            recipient: data.recipient,
            bank: data.bank,
            amount_naira: data.amount_naira,
            status: data.status
          },
          ...prev
        ])
        setPipelineStages(prev => ({
          ...prev,
          bank: { active: false, latencyMs: 48, status: 'OK' }
        }))
        break

      case 'agent.reply':
        setCaptionText(data.text)
        setCaptionLang(data.language)
        setIsAssistantSpeaking(true)
        setTranscripts(prev => [
          ...prev,
          {
            speaker: 'assistant',
            language: data.language,
            text: data.text,
            confidence: 0.99,
            timestamp: new Date().toLocaleTimeString('en-GB')
          }
        ])
        setPipelineStages(prev => ({
          ...prev,
          tts: { active: true, latencyMs: data.latencyMs, status: 'OK' }
        }))
        setTimeout(() => setIsAssistantSpeaking(false), 2600)
        break

      case 'call.ended':
        setSmsReceiptText(data.sms_receipt)
        setPhoneState('ended')
        setIsAssistantSpeaking(false)
        setIsReplayRunning(false)
        break

      default:
        break
    }
  }

  // Reset Session
  const handleResetSession = () => {
    replayTimersRef.current.forEach(t => clearTimeout(t))
    replayTimersRef.current = []
    stopRingback()
    setPhoneState('lock')
    setCallDuration(0)
    setCaptionText('')
    setIsAssistantSpeaking(false)
    setSmsReceiptText('')
    setTranscripts([])
    setPipelineStages({})
    setAuthState({
      authLevel: 'none',
      pinVerified: false,
      voiceScore: 0.0,
      isLocked: false,
      failedAttempts: 0
    })
    setTransactions([])
    setIsReplayRunning(false)
  }

  return (
    <div style={{
      maxWidth: 1600,
      margin: '0 auto',
      padding: isPresenterMode ? '16px 24px' : '16px 28px',
      display: 'grid',
      gridTemplateColumns: '4.8fr 7.2fr',
      gap: 28,
      alignItems: 'start',
      minHeight: 'calc(100vh - 90px)'
    }}>
      {/* Left Column: Device Simulator (Hero Sticky) */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        position: 'sticky',
        top: 16
      }}>
        {/* Device Switcher Toggle */}
        <div style={{
          display: 'flex',
          gap: 6,
          background: 'var(--bg-white)',
          padding: '4px 6px',
          borderRadius: 'var(--radius-full)',
          border: '1.5px solid var(--color-border)',
          marginBottom: 14,
          boxShadow: 'var(--shadow-key)'
        }}>
          <button
            onClick={() => setDeviceType('iphone')}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-full)',
              fontSize: 12,
              fontWeight: 800,
              background: deviceType === 'iphone' ? 'var(--color-ink)' : 'transparent',
              color: deviceType === 'iphone' ? '#FFFFFF' : 'var(--color-ink-secondary)',
              transition: 'all 0.15s ease'
            }}
          >
            iPhone 16 Pro
          </button>
          <button
            onClick={() => setDeviceType('feature')}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-full)',
              fontSize: 12,
              fontWeight: 800,
              background: deviceType === 'feature' ? 'var(--color-ink)' : 'transparent',
              color: deviceType === 'feature' ? '#FFFFFF' : 'var(--color-ink-secondary)',
              transition: 'all 0.15s ease'
            }}
          >
            Feature Phone (Keypad)
          </button>
        </div>

        {/* Selected Phone Device Frame */}
        {deviceType === 'iphone' ? (
          <PhoneFrame inCall={phoneState === 'incall' || phoneState === 'ringing'}>
            {/* Screen State Machine */}
            {phoneState === 'lock' && (
              <LockScreen onUnlock={() => setPhoneState('dialer')} />
            )}

            {phoneState === 'dialer' && (
              <Dialer onCall={(num) => handleStartCall(num)} />
            )}

            {phoneState === 'ringing' && (
              <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '30px 20px',
                background: '#000000',
                color: '#FFFFFF'
              }}>
                <div style={{ textAlign: 'center', marginTop: 24 }}>
                  <h2 style={{ fontSize: 26, fontWeight: 400, margin: '0 0 4px', fontFamily: 'var(--font-sans)' }}>Lyfpatner</h2>
                  <p style={{ fontSize: 14, color: '#8E8E93', margin: 0 }}>calling 333 (toll-free)...</p>
                </div>

                <div style={{
                  width: 70,
                  height: 70,
                  borderRadius: '50%',
                  background: 'rgba(52, 199, 89, 0.15)',
                  border: '2px solid #34C759',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  animation: 'pulseGlow 1.5s infinite'
                }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="#34C759">
                    <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.46.57 3.58a1 1 0 01-.24 1.01l-2.21 2.2z" />
                  </svg>
                </div>

                <button
                  onClick={handleEndCall}
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: '50%',
                    background: '#FF3B30',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="#FFFFFF" style={{ transform: 'rotate(135deg)' }}>
                    <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.46.57 3.58a1 1 0 01-.24 1.01l-2.21 2.2z" />
                  </svg>
                </button>
              </div>
            )}

            {phoneState === 'incall' && (
              <InCallScreen
                callDuration={callDuration}
                captionText={captionText}
                captionLang={captionLang}
                isAssistantSpeaking={isAssistantSpeaking}
                onEndCall={handleEndCall}
                onSendDTMF={handleSendDTMF}
              />
            )}

            {phoneState === 'ended' && (
              <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '30px 20px',
                background: '#000000',
                color: '#FFFFFF',
                position: 'relative'
              }}>
                <NotificationBanner
                  message={smsReceiptText}
                  onOpen={() => setPhoneState('messages')}
                />

                <div style={{ textAlign: 'center', marginTop: 90 }}>
                  <h2 style={{ fontSize: 24, fontWeight: 400, margin: '0 0 4px', fontFamily: 'var(--font-sans)' }}>Call Ended</h2>
                  <p style={{ fontSize: 13, color: '#8E8E93', margin: 0 }}>Duration: {callDuration}s</p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%' }}>
                  <button
                    onClick={() => setPhoneState('messages')}
                    style={{
                      width: '100%',
                      padding: '11px',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(255, 255, 255, 0.14)',
                      color: '#FFFFFF',
                      fontSize: 12.5,
                      fontWeight: 700,
                      border: '1px solid rgba(255, 255, 255, 0.2)'
                    }}
                  >
                    View SMS Transaction Receipt &rarr;
                  </button>
                  <button
                    onClick={() => setPhoneState('dialer')}
                    style={{
                      width: '100%',
                      padding: '11px',
                      borderRadius: 'var(--radius-md)',
                      background: '#1C1C1E',
                      color: '#8E8E93',
                      fontSize: 12.5,
                      fontWeight: 700
                    }}
                  >
                    Return to Keypad
                  </button>
                </div>
              </div>
            )}

            {phoneState === 'messages' && (
              <MessagesView
                message={smsReceiptText}
                onBack={() => setPhoneState('dialer')}
              />
            )}
          </PhoneFrame>
        ) : (
          <FeaturePhone
            inCall={phoneState === 'incall'}
            callDuration={callDuration}
            captionText={captionText}
            onCall={() => handleStartCall('333')}
            onEndCall={handleEndCall}
          />
        )}
      </div>

      {/* Right Column: Bank Operations Console Panel (Fully Scrollable, Never Clipped) */}
      <div style={{
        overflowY: 'auto',
        maxHeight: 'calc(100vh - 100px)',
        paddingRight: 8,
        display: 'flex',
        flexDirection: 'column',
        gap: 14
      }}>
        <ConsolePanel
          pipelineStages={pipelineStages}
          transcripts={transcripts}
          authState={authState}
          transactions={transactions}
          isRealCallMode={isRealCallMode}
          onToggleRealCallMode={() => setIsRealCallMode(!isRealCallMode)}
          isReplayRunning={isReplayRunning}
          onStartReplay={handleStartReplay}
          onResetSession={handleResetSession}
          currentLang={captionLang}
          onSelectLang={(lang) => {
            setCaptionLang(lang)
            if (onSelectLanguage) onSelectLanguage(lang)
          }}
          onSimulatePhrase={handleSimulatePhrase}
          phoneState={phoneState}
          onStartCall={handleStartCall}
        />
      </div>
    </div>
  )
}
