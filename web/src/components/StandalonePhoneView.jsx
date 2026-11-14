import React, { useState, useEffect, useRef } from 'react'
import PhoneFrame from './phone/PhoneFrame'
import LockScreen from './phone/LockScreen'
import Dialer from './phone/Dialer'
import InCallScreen from './phone/InCallScreen'
import NotificationBanner from './phone/NotificationBanner'
import MessagesView from './phone/MessagesView'
import FeaturePhone from './phone/FeaturePhone'
import {
  startRingback,
  stopRingback,
  playDTMF,
  speakText,
  stopSpeaking,
  playCallConnectSound,
  playCallEndSound,
  playWavBase64
} from '../utils/audio'
import { LANGUAGES } from '../data/languages'
import { PhoneIcon } from './common/Icons'

export default function StandalonePhoneView({ selectedLanguage = 'ha', onSelectLanguage }) {
  const [deviceType, setDeviceType] = useState('iphone')
  const [phoneState, setPhoneState] = useState('dialer')
  const [callDuration, setCallDuration] = useState(0)
  const [captionText, setCaptionText] = useState('')
  const [captionLang, setCaptionLang] = useState(selectedLanguage)
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false)
  const [isListeningMic, setIsListeningMic] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [smsReceiptText, setSmsReceiptText] = useState('')
  const [activeSessionId, setActiveSessionId] = useState(null)

  const callTimerRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const sessionIdRef = useRef(null)
  const isAssistantSpeakingRef = useRef(false)
  const isMutedRef = useRef(false)
  const phoneStateRef = useRef('dialer')
  const audioContextRef = useRef(null)
  const animFrameRef = useRef(null)
  const speechTrackerRef = useRef({
    isSpeaking: false,
    silenceStartTime: 0,
    speechStartTime: 0,
    chunks: []
  })

  // Sync refs
  useEffect(() => { sessionIdRef.current = activeSessionId }, [activeSessionId])
  useEffect(() => { isAssistantSpeakingRef.current = isAssistantSpeaking }, [isAssistantSpeaking])
  useEffect(() => { isMutedRef.current = isMuted }, [isMuted])
  useEffect(() => { phoneStateRef.current = phoneState }, [phoneState])

  useEffect(() => {
    if (selectedLanguage) setCaptionLang(selectedLanguage)
  }, [selectedLanguage])

  // Call duration timer
  useEffect(() => {
    if (phoneState === 'incall') {
      setCallDuration(0)
      callTimerRef.current = setInterval(() => setCallDuration(p => p + 1), 1000)
    } else {
      clearInterval(callTimerRef.current)
    }
    return () => clearInterval(callTimerRef.current)
  }, [phoneState])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRingback()
      stopSpeaking()
      clearInterval(callTimerRef.current)
      stopContinuousAudio()
    }
  }, [])

  const langData = LANGUAGES[captionLang] || LANGUAGES.ha
  const apiLang = captionLang === 'en' ? 'en-ng' : captionLang

  const playReply = async (replyText, replyAudioBase64) => {
    setIsAssistantSpeaking(true)
    isAssistantSpeakingRef.current = true
    if (replyAudioBase64) {
      try {
        await playWavBase64(replyAudioBase64, null, () => {
          setIsAssistantSpeaking(false)
          isAssistantSpeakingRef.current = false
        })
        return
      } catch (e) {
        console.warn('AudioContext playback failed, trying Web Speech:', e)
      }
    }
    speakText(replyText, captionLang, null, () => {
      setIsAssistantSpeaking(false)
      isAssistantSpeakingRef.current = false
    })
  }

  const executeTextTurn = async (text) => {
    if (!text?.trim()) return
    setCaptionText(text)
    setIsAssistantSpeaking(false)
    isAssistantSpeakingRef.current = false

    const sid = sessionIdRef.current
    if (!sid) return

    try {
      const res = await fetch('/v1/voice/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, text_input: text })
      })
      if (res.ok) {
        const data = await res.json()
        setCaptionText(data.reply_text)
        await playReply(data.reply_text, data.reply_audio_base64)
      }
    } catch (e) {
      console.warn('Voice turn error:', e)
    }
  }

  // ─── Continuous Hands-Free VAD (Voice Activity Detection) ───
  const startContinuousAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      const audioCtx = new AudioCtx()
      audioContextRef.current = audioCtx

      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 512
      source.connect(analyser)

      // MediaRecorder to capture audio segments
      const mimeType = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4'
      ].find(t => MediaRecorder.isTypeSupported(t)) || ''

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {})
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data)
        }
      }

      recorder.start(100) // 100ms time slices
      setIsListeningMic(true)

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)

      let noiseFloor = 18
      const tracker = speechTrackerRef.current
      tracker.isSpeaking = false
      tracker.silenceStartTime = 0
      tracker.speechStartTime = 0

      const checkVolume = () => {
        if (phoneStateRef.current !== 'incall') {
          return
        }

        analyser.getByteFrequencyData(dataArray)
        let sum = 0
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i]
        const average = sum / bufferLength

        const now = Date.now()

        // If assistant is speaking or call is muted, don't record user speech
        if (isAssistantSpeakingRef.current || isMutedRef.current) {
          audioChunksRef.current = [] // clear echo buffer
          noiseFloor = Math.max(15, average * 0.5)
          animFrameRef.current = requestAnimationFrame(checkVolume)
          return
        }

        const voiceThreshold = Math.max(26, noiseFloor * 1.55)

        if (average > voiceThreshold) {
          // Voice detected!
          if (!tracker.isSpeaking) {
            tracker.isSpeaking = true
            tracker.speechStartTime = now
            tracker.silenceStartTime = 0
          } else {
            tracker.silenceStartTime = 0
          }
        } else {
          // Voice quiet
          noiseFloor = noiseFloor * 0.95 + average * 0.05
          if (tracker.isSpeaking) {
            if (tracker.silenceStartTime === 0) {
              tracker.silenceStartTime = now
            } else if (now - tracker.silenceStartTime > 950) {
              // 950ms of silence after speaking -> user finished talking!
              const speechDuration = tracker.silenceStartTime - tracker.speechStartTime
              tracker.isSpeaking = false
              tracker.silenceStartTime = 0

              if (speechDuration >= 350) {
                // Meaningful speech segment! Process it
                sendSpokenSegment(mimeType)
              } else {
                audioChunksRef.current = []
              }
            }
          } else {
            // Keep buffer small while waiting
            if (audioChunksRef.current.length > 25) {
              audioChunksRef.current = audioChunksRef.current.slice(-15)
            }
          }
        }

        animFrameRef.current = requestAnimationFrame(checkVolume)
      }

      animFrameRef.current = requestAnimationFrame(checkVolume)
    } catch (e) {
      console.warn('Microphone stream error:', e)
      setCaptionText('Please allow microphone access to talk.')
    }
  }

  const sendSpokenSegment = async (mimeType) => {
    const chunks = [...audioChunksRef.current]
    audioChunksRef.current = []
    if (chunks.length === 0) return

    const blob = new Blob(chunks, { type: mimeType || 'audio/webm' })
    if (blob.size < 600) return

    try {
      const formData = new FormData()
      formData.append('audio', blob, 'turn.webm')
      formData.append('session_id', sessionIdRef.current || '')

      const res = await fetch('/v1/voice/turn_audio', {
        method: 'POST',
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        if (data.user_text) {
          setCaptionText(data.user_text)
        }
        setTimeout(async () => {
          setCaptionText(data.reply_text)
          await playReply(data.reply_text, data.reply_audio_base64)
        }, 200)
      }
    } catch (e) {
      console.warn('Turn error:', e)
    }
  }

  const stopContinuousAudio = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = null
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch (e) {}
    }
    if (audioContextRef.current) {
      try { audioContextRef.current.close() } catch (e) {}
      audioContextRef.current = null
    }
    setIsListeningMic(false)
  }

  // ─── Call Controls ───
  const handleStartCall = async (shortCode = '333') => {
    stopRingback()
    stopSpeaking()
    setPhoneState('ringing')
    phoneStateRef.current = 'ringing'
    startRingback()

    try {
      const res = await fetch('/v1/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'web',
          caller_id: langData.caller.phone,
          language: apiLang
        })
      })
      if (res.ok) {
        const sData = await res.json()
        setActiveSessionId(sData.session_id)
        sessionIdRef.current = sData.session_id
      }
    } catch (e) {
      console.warn('Session create error:', e)
    }

    setTimeout(async () => {
      stopRingback()
      playCallConnectSound()
      setPhoneState('incall')
      phoneStateRef.current = 'incall'
      const greeting = langData.greeting
      setCaptionText(greeting)

      // Start hands-free automatic listening
      startContinuousAudio()

      // Fetch and play greeting TTS via AudioContext
      try {
        const ttsRes = await fetch('/v1/tts/speak', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: greeting, language: apiLang })
        })
        if (ttsRes.ok) {
          const arrayBuffer = await ttsRes.arrayBuffer()
          const bytes = new Uint8Array(arrayBuffer)
          let binary = ''
          for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
          const b64 = btoa(binary)
          await playWavBase64(b64, () => {
            setIsAssistantSpeaking(true)
            isAssistantSpeakingRef.current = true
          }, () => {
            setIsAssistantSpeaking(false)
            isAssistantSpeakingRef.current = false
          })
          return
        }
      } catch (e) {
        console.warn('Greeting TTS error:', e)
      }

      speakText(greeting, captionLang, () => {
        setIsAssistantSpeaking(true)
        isAssistantSpeakingRef.current = true
      }, () => {
        setIsAssistantSpeaking(false)
        isAssistantSpeakingRef.current = false
      })
    }, 2000)
  }

  const handleEndCall = () => {
    stopRingback()
    stopSpeaking()
    stopContinuousAudio()
    playCallEndSound()
    setPhoneState('ended')
    phoneStateRef.current = 'ended'
    setIsAssistantSpeaking(false)
    isAssistantSpeakingRef.current = false
    if (!smsReceiptText) {
      setSmsReceiptText(`Lyfpartner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8831. Bal: ${langData.caller.balanceFormatted}`)
    }
  }

  const handleSendDTMF = async (digit) => {
    playDTMF(digit)
    await executeTextTurn(digit)
  }

  const handleToggleMute = () => {
    setIsMuted(prev => !prev)
  }

  return (
    <div style={{
      width: '100%',
      maxWidth: 680,
      margin: '0 auto',
      padding: 'clamp(10px, 3vw, 24px) clamp(10px, 3vw, 20px) 40px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 16,
      boxSizing: 'border-box'
    }}>
      {/* Device & Language Controls */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        maxWidth: 350,
        flexWrap: 'wrap',
        gap: 8
      }}>
        {/* Device Switcher */}
        <div style={{
          display: 'flex',
          gap: 3,
          background: 'var(--bg-white)',
          padding: '3px 5px',
          borderRadius: 'var(--radius-full)',
          border: '1.5px solid var(--color-border)'
        }}>
          <button
            onClick={() => setDeviceType('iphone')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              background: deviceType === 'iphone' ? 'var(--color-ink)' : 'transparent',
              color: deviceType === 'iphone' ? '#FFFFFF' : 'var(--color-ink-secondary)',
              transition: 'all 0.15s ease'
            }}
          >
            Smartphone
          </button>
          <button
            onClick={() => setDeviceType('feature')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              background: deviceType === 'feature' ? 'var(--color-ink)' : 'transparent',
              color: deviceType === 'feature' ? '#FFFFFF' : 'var(--color-ink-secondary)',
              transition: 'all 0.15s ease'
            }}
          >
            Feature Phone
          </button>
        </div>

        {/* Language Switcher */}
        <div style={{
          display: 'flex',
          gap: 2,
          background: 'var(--bg-white)',
          padding: '3px 5px',
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
              onClick={() => {
                setCaptionLang(l.id)
                if (onSelectLanguage) onSelectLanguage(l.id)
              }}
              style={{
                padding: '4px 8px',
                borderRadius: 'var(--radius-full)',
                fontSize: 10,
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                background: captionLang === l.id ? 'var(--color-ink)' : 'transparent',
                color: captionLang === l.id ? '#FFFFFF' : 'var(--color-ink-secondary)',
                transition: 'all 0.15s ease'
              }}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      {/* Phone Simulator Frame */}
      {deviceType === 'iphone' ? (
        <PhoneFrame inCall={phoneState === 'incall' || phoneState === 'ringing'}>
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
                <h2 style={{ fontSize: 26, fontWeight: 400, margin: '0 0 4px', fontFamily: 'var(--font-sans)' }}>Lyfpartner</h2>
                <p style={{ fontSize: 14, color: '#8E8E93', margin: 0 }}>calling 333...</p>
              </div>

              <div style={{
                width: 70, height: 70, borderRadius: '50%',
                background: 'rgba(52, 199, 89, 0.15)',
                border: '2px solid #34C759',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                animation: 'pulseGlow 1.5s infinite'
              }}>
                <PhoneIcon size={28} color="#34C759" />
              </div>

              <button
                onClick={handleEndCall}
                style={{
                  width: 56, height: 56, borderRadius: '50%',
                  background: '#FF3B30',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <div style={{ transform: 'rotate(135deg)' }}>
                  <PhoneIcon size={24} color="#FFFFFF" />
                </div>
              </button>
            </div>
          )}

          {phoneState === 'incall' && (
            <InCallScreen
              callDuration={callDuration}
              captionText={captionText}
              captionLang={captionLang}
              isAssistantSpeaking={isAssistantSpeaking}
              isListening={isListeningMic && !isAssistantSpeaking}
              isMuted={isMuted}
              onEndCall={handleEndCall}
              onSendDTMF={handleSendDTMF}
              onToggleMic={handleToggleMute}
            />
          )}

          {phoneState === 'ended' && (
            <div style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'space-between',
              padding: '30px 20px', background: '#000000', color: '#FFFFFF'
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
                    width: '100%', padding: '11px', borderRadius: 'var(--radius-md)',
                    background: 'rgba(255,255,255,0.14)', color: '#FFFFFF',
                    fontSize: 12.5, fontWeight: 700,
                    border: '1px solid rgba(255,255,255,0.2)', cursor: 'pointer'
                  }}
                >
                  View SMS Receipt &rarr;
                </button>
                <button
                  onClick={() => setPhoneState('dialer')}
                  style={{
                    width: '100%', padding: '11px', borderRadius: 'var(--radius-md)',
                    background: '#1C1C1E', color: '#8E8E93',
                    fontSize: 12.5, fontWeight: 700, cursor: 'pointer'
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
  )
}
