/**
 * Web Audio API Engine for Lyfpatner:
 * - Accurate Dual-Tone Multi-Frequency (DTMF) synthesis
 * - Telecom Ringback tone (440Hz + 480Hz modulated cadence)
 * - Microphone & audio stream AnalyserNode for the real-time waveform
 */

let audioCtx = null

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    audioCtx = new AudioContextClass()
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
  return audioCtx
}

const DTMF_FREQS = {
  '1': [697, 1209],
  '2': [697, 1336],
  '3': [697, 1477],
  '4': [770, 1209],
  '5': [770, 1336],
  '6': [770, 1477],
  '7': [852, 1209],
  '8': [852, 1336],
  '9': [852, 1477],
  '*': [941, 1209],
  '0': [941, 1336],
  '#': [941, 1477]
}

export function playDTMF(digit, duration = 0.15) {
  const ctx = getAudioContext()
  const freqs = DTMF_FREQS[digit]
  if (!freqs) return

  const osc1 = ctx.createOscillator()
  const osc2 = ctx.createOscillator()
  const gain = ctx.createGain()

  osc1.type = 'sine'
  osc2.type = 'sine'
  osc1.frequency.value = freqs[0]
  osc2.frequency.value = freqs[1]

  const now = ctx.currentTime
  gain.gain.setValueAtTime(0.12, now)
  gain.gain.exponentialRampToValueAtTime(0.001, now + duration)

  osc1.connect(gain)
  osc2.connect(gain)
  gain.connect(ctx.destination)

  osc1.start(now)
  osc2.start(now)
  osc1.stop(now + duration)
  osc2.stop(now + duration)
}

let ringbackInterval = null
let currentRingbackSources = null

export function startRingback() {
  stopRingback()
  const ctx = getAudioContext()

  function playCadenceBurst() {
    const now = ctx.currentTime
    const osc1 = ctx.createOscillator()
    const osc2 = ctx.createOscillator()
    const gain = ctx.createGain()

    osc1.type = 'sine'
    osc2.type = 'sine'
    osc1.frequency.value = 440
    osc2.frequency.value = 480

    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(0.08, now + 0.05)
    gain.gain.setValueAtTime(0.08, now + 1.8)
    gain.gain.linearRampToValueAtTime(0, now + 2.0)

    osc1.connect(gain)
    osc2.connect(gain)
    gain.connect(ctx.destination)

    osc1.start(now)
    osc2.start(now)
    osc1.stop(now + 2.0)
    osc2.stop(now + 2.0)

    currentRingbackSources = { osc1, osc2, gain }
  }

  playCadenceBurst()
  ringbackInterval = setInterval(playCadenceBurst, 4000)
}

export function stopRingback() {
  if (ringbackInterval) {
    clearInterval(ringbackInterval)
    ringbackInterval = null
  }
  if (currentRingbackSources) {
    try {
      currentRingbackSources.gain.gain.setValueAtTime(0, audioCtx.currentTime)
      currentRingbackSources.osc1.stop()
      currentRingbackSources.osc2.stop()
    } catch (e) {
      // already stopped
    }
    currentRingbackSources = null
  }
}

/**
 * Creates an AnalyserNode for live mic or audio element playback
 */
export function createAnalyser() {
  const ctx = getAudioContext()
  const analyser = ctx.createAnalyser()
  analyser.fftSize = 64
  analyser.smoothingTimeConstant = 0.8
  return analyser
}

/**
 * Call connection chime
 */
export function playCallConnectSound() {
  try {
    const ctx = getAudioContext()
    const now = ctx.currentTime
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(440, now)
    osc.frequency.setValueAtTime(880, now + 0.1)
    gain.gain.setValueAtTime(0.09, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(now)
    osc.stop(now + 0.35)
  } catch (e) {
    console.warn('Audio chime error:', e)
  }
}

/**
 * Call disconnect chime
 */
export function playCallEndSound() {
  try {
    const ctx = getAudioContext()
    const now = ctx.currentTime
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(480, now)
    osc.frequency.setValueAtTime(320, now + 0.12)
    gain.gain.setValueAtTime(0.09, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(now)
    osc.stop(now + 0.3)
  } catch (e) {
    console.warn('Audio chime error:', e)
  }
}

/**
 * Web Speech API Text-to-Speech Engine
 * Speaks caller replies out loud so the phone emulator isn't silent!
 */
export function speakText(text, lang = 'en', onStart, onEnd) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return
  try {
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    if (lang === 'ha') utterance.lang = 'ha-NG'
    else if (lang === 'yo') utterance.lang = 'yo-NG'
    else if (lang === 'ig') utterance.lang = 'ig-NG'
    else utterance.lang = 'en-NG'

    utterance.rate = 1.0
    utterance.pitch = 1.05

    if (onStart) utterance.onstart = onStart
    if (onEnd) utterance.onend = onEnd
    utterance.onerror = () => { if (onEnd) onEnd() }

    window.speechSynthesis.speak(utterance)
  } catch (e) {
    console.warn('Speech synthesis error:', e)
    if (onEnd) onEnd()
  }
}

export function stopSpeaking() {
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel()
    } catch (e) {}
  }
}

/**
 * Decode and play a base64-encoded WAV/audio buffer through AudioContext.
 * This BYPASSES the browser autoplay policy because AudioContext.resume()
 * is called, and decodeAudioData works with any user-gesture-unlocked context.
 * Returns a Promise that resolves when playback finishes (or rejects on error).
 */
export function playWavBase64(base64String, onStart, onEnd) {
  return new Promise((resolve, reject) => {
    try {
      const ctx = getAudioContext()

      // Convert base64 → ArrayBuffer
      const binaryString = atob(base64String)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      const arrayBuffer = bytes.buffer

      ctx.decodeAudioData(
        arrayBuffer,
        (audioBuffer) => {
          const source = ctx.createBufferSource()
          source.buffer = audioBuffer
          source.connect(ctx.destination)
          if (onStart) onStart()
          source.onended = () => {
            if (onEnd) onEnd()
            resolve()
          }
          source.start(0)
        },
        (err) => {
          console.warn('decodeAudioData error, falling back to <Audio>:', err)
          reject(err)
        }
      )
    } catch (e) {
      console.warn('playWavBase64 error:', e)
      reject(e)
    }
  })
}
