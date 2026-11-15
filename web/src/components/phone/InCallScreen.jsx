import React, { useState } from 'react'
import Waveform from './Waveform'
import CaptionStrip from './CaptionStrip'
import { playDTMF } from '../../utils/audio'
import { MicIcon, PhoneIcon } from '../common/Icons'

export default function InCallScreen({
  callDuration = 0,
  captionText = '',
  captionLang = 'ha',
  isAssistantSpeaking = false,
  isListening = false,
  isMuted = false,
  quickPhrases = [],
  onEndCall,
  onSendDTMF,
  onSendTurn,
  onToggleMic
}) {
  const [isSpeaker, setIsSpeaker] = useState(true)
  const [showKeypad, setShowKeypad] = useState(false)
  const [typedDigits, setTypedDigits] = useState('')

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`
  }

  const handleKeypadDigit = (digit) => {
    playDTMF(digit)
    const nextDigits = typedDigits + digit
    setTypedDigits(nextDigits)
    if (nextDigits.length === 4) {
      if (onSendDTMF) {
        onSendDTMF(nextDigits)
      }
      setTimeout(() => {
        setTypedDigits('')
        setShowKeypad(false)
      }, 600)
    } else if (onSendDTMF) {
      onSendDTMF(digit)
    }
  }

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '24px 18px 24px',
      background: 'radial-gradient(circle at 50% 25%, #1c2738 0%, #05070c 80%)',
      color: '#FFFFFF',
      position: 'relative',
      height: '100%',
      boxSizing: 'border-box'
    }}>
      {/* Top Caller Header */}
      <div style={{ textAlign: 'center', marginTop: 12 }}>
        <h2 style={{
          fontSize: 26,
          fontWeight: 400,
          letterSpacing: -0.5,
          margin: 0,
          fontFamily: 'var(--font-sans)'
        }}>
          Lyfpartner
        </h2>
        <span style={{ fontSize: 13, color: '#8E8E93', display: 'block', marginTop: 2 }}>
          333 &bull; Toll-Free
        </span>
        <span style={{
          fontSize: 13.5,
          fontWeight: 600,
          fontFamily: 'var(--font-mono)',
          color: '#34C759',
          display: 'block',
          marginTop: 3
        }}>
          {formatTimer(callDuration)}
        </span>

        {/* Privacy Notice Pill */}
        <div style={{
          margin: '6px auto 0',
          padding: '3px 10px',
          background: 'rgba(255, 255, 255, 0.08)',
          borderRadius: '9999px',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 5,
          border: '1px solid rgba(255, 255, 255, 0.14)'
        }}>
          <span style={{ fontSize: 10 }}>🔒</span>
          <span style={{ fontSize: 9.5, color: '#D1D5DB', fontFamily: 'var(--font-mono)' }}>
            Ensure privacy &bull; Keypad or voice PIN
          </span>
        </div>
      </div>

      {/* Center: Live Waveform Visualizer */}
      <div style={{ margin: '8px 0' }}>
        <Waveform isActive={true} isSpeaking={isAssistantSpeaking || isListening} />
      </div>

      {/* iOS Live Captions Strip */}
      <CaptionStrip
        text={captionText}
        language={captionLang}
        isAssistant={isAssistantSpeaking}
      />

      {/* Conversational Action Prompts (Talk to Assistant) */}
      {!showKeypad && onSendTurn && (
        <div style={{
          margin: '6px 0 10px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 5,
          justifyContent: 'center',
          maxWidth: 290
        }}>
          {/* Quick confirmation chips if assistant is awaiting confirmation */}
          {(captionText.toLowerCase().includes('in tura') ||
            captionText.toLowerCase().includes('proceed') ||
            captionText.toLowerCase().includes('confirm') ||
            captionText.toLowerCase().includes('se kin tesiwaju') ||
            captionText.toLowerCase().includes('m ga-eziga ya')) ? (
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={() => onSendTurn(captionLang === 'ha' ? 'I mana, tura shi yanzu' : captionLang === 'yo' ? 'Beeni, tesiwaju' : captionLang === 'ig' ? 'Ee, ziga ya ugbua' : 'Yes, proceed with transfer')}
                style={{
                  padding: '5px 12px',
                  borderRadius: 9999,
                  background: 'rgba(52, 199, 89, 0.3)',
                  border: '1px solid #34C759',
                  color: '#FFFFFF',
                  fontSize: 11,
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer'
                }}
              >
                ✅ Yes, Confirm
              </button>
              <button
                onClick={() => onSendTurn(captionLang === 'ha' ? 'A\'a, soke shi' : captionLang === 'yo' ? 'Rara, fagile e' : captionLang === 'ig' ? 'Mba, kagbuo ya' : 'No, cancel')}
                style={{
                  padding: '5px 12px',
                  borderRadius: 9999,
                  background: 'rgba(255, 59, 48, 0.3)',
                  border: '1px solid #FF3B30',
                  color: '#FFFFFF',
                  fontSize: 11,
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer'
                }}
              >
                ❌ Cancel
              </button>
            </div>
          ) : (
            quickPhrases && quickPhrases.map((phrase) => (
              <button
                key={phrase.id}
                onClick={() => {
                  if (phrase.type === 'auth') {
                    setShowKeypad(true)
                  }
                  onSendTurn(phrase.text)
                }}
                style={{
                  padding: '4px 9px',
                  borderRadius: 9999,
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.16)',
                  color: '#FFFFFF',
                  fontSize: 10.5,
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(52, 199, 89, 0.22)' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)' }}
                title={phrase.translation || phrase.text}
              >
                <span style={{ fontSize: 9 }}>
                  {phrase.type === 'transfer' ? '💸' : phrase.type === 'inquiry' ? '💳' : phrase.type === 'bill' ? '💡' : '🔒'}
                </span>
                <span>{phrase.label}</span>
              </button>
            ))
          )}
        </div>
      )}

      {/* In-Call Keypad Overlay (if opened) */}
      {showKeypad ? (
        <div style={{
          position: 'absolute',
          top: 90,
          left: 14,
          right: 14,
          bottom: 90,
          background: 'rgba(20, 20, 22, 0.98)',
          backdropFilter: 'blur(30px)',
          borderRadius: 24,
          padding: '16px 14px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          zIndex: 40,
          border: '1px solid rgba(255, 255, 255, 0.12)'
        }}>
          <div style={{ textAlign: 'center', height: 28 }}>
            <span style={{ fontSize: 11, color: '#34C759', fontFamily: 'var(--font-mono)', fontWeight: 700, display: 'block', marginBottom: 2 }}>
              4-DIGIT PIN (KEYPAD OR VOICE)
            </span>
            <span style={{ fontSize: 20, fontFamily: 'var(--font-mono)', letterSpacing: 4, color: '#FFFFFF' }}>
              {typedDigits ? typedDigits.replace(/./g, '• ') : '_ _ _ _'}
            </span>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '10px 12px',
            maxWidth: 220,
            margin: '0 auto'
          }}>
            {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map(digit => (
              <button
                key={digit}
                onClick={() => handleKeypadDigit(digit)}
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  background: '#2C2C2E',
                  color: '#FFFFFF',
                  fontSize: 20,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                {digit}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowKeypad(false)}
            style={{
              padding: '8px',
              fontSize: 13.5,
              color: '#0A84FF',
              fontWeight: 600,
              textAlign: 'center',
              background: 'none',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            Hide Keypad
          </button>
        </div>
      ) : (
        /* Genuine iPhone In-Call 6-Button Grid */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '14px 12px',
          maxWidth: 250,
          margin: '0 auto'
        }}>
          {/* Mute Button */}
          <button
            onClick={onToggleMic}
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: isMuted ? '#FFFFFF' : '#2C2C2E',
              color: isMuted ? '#000000' : '#FFFFFF',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto',
              cursor: 'pointer',
              border: 'none',
              transition: 'all 0.15s ease'
            }}
            title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          >
            <MicIcon size={20} color={isMuted ? '#000000' : '#FFFFFF'} />
            <span style={{ fontSize: 9, marginTop: 2 }}>{isMuted ? 'unmute' : 'mute'}</span>
          </button>

          {/* Keypad */}
          <button
            onClick={() => setShowKeypad(!showKeypad)}
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#2C2C2E',
              color: '#FFFFFF',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="5" cy="5" r="2" />
              <circle cx="12" cy="5" r="2" />
              <circle cx="19" cy="5" r="2" />
              <circle cx="5" cy="12" r="2" />
              <circle cx="12" cy="12" r="2" />
              <circle cx="19" cy="12" r="2" />
              <circle cx="5" cy="19" r="2" />
              <circle cx="12" cy="19" r="2" />
              <circle cx="19" cy="19" r="2" />
            </svg>
            <span style={{ fontSize: 9, marginTop: 2 }}>keypad</span>
          </button>

          {/* Speaker */}
          <button
            onClick={() => setIsSpeaker(!isSpeaker)}
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: isSpeaker ? '#FFFFFF' : '#2C2C2E',
              color: isSpeaker ? '#000000' : '#FFFFFF',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            </svg>
            <span style={{ fontSize: 9, marginTop: 2 }}>speaker</span>
          </button>

          {/* Add Call */}
          <button
            disabled
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#2C2C2E',
              color: '#636366',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: 0.5,
              margin: '0 auto',
              border: 'none'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span style={{ fontSize: 9, marginTop: 2 }}>add call</span>
          </button>

          {/* FaceTime */}
          <button
            disabled
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#2C2C2E',
              color: '#636366',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: 0.5,
              margin: '0 auto',
              border: 'none'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
            </svg>
            <span style={{ fontSize: 9, marginTop: 2 }}>FaceTime</span>
          </button>

          {/* Contacts */}
          <button
            disabled
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#2C2C2E',
              color: '#636366',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: 0.5,
              margin: '0 auto',
              border: 'none'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <span style={{ fontSize: 9, marginTop: 2 }}>contacts</span>
          </button>
        </div>
      )}

      {/* Red End Call Handset */}
      <div style={{ textAlign: 'center', marginTop: 12 }}>
        <button
          onClick={onEndCall}
          style={{
            width: 60,
            height: 60,
            borderRadius: '50%',
            background: '#FF3B30',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(255, 59, 48, 0.45)',
            transition: 'transform 0.1s'
          }}
          onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.95)' }}
          onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)' }}
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="#FFFFFF" style={{ transform: 'rotate(135deg)' }}>
            <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24c1.12.37 2.33.57 3.58.57a1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1c0 1.25.2 2.46.57 3.58a1 1 0 01-.24 1.01l-2.21 2.2z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
