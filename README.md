# Lyfpartner — Voice-First Multilingual Autonomous Banking

> **Zenith Bank Zecathon 6.0 POC**  
> Empathetic, autonomous voice banking hotline built for 35M+ Nigerians living with visual impairments or low digital literacy.  
> Supports **Nigerian English, Hausa, Yoruba, and Igbo**.

---

## 🌟 The Problem & The Solution

- **The Problem:** 35+ million Nigerians are shut out of digital finance by complex mobile apps and confusing USSD menus with strict timeouts. Visually impaired or non-literate customers are forced to share PINs and phones with third parties, exposing them to massive fraud risks.
- **The Solution:** Lyfpartner replaces the screens with a zero-interface, toll-free phone number (`333`). Customers dial in, speak naturally in their own language or dialect, hear warm female conversational audio, and complete balance checks, transfers, and bill payments with spoken PIN security.

---

## 🚀 Live Demo & How to Use It

The project runs on `http://localhost:8000` with 3 completely separated views:

| View | URL | What It Does & How to Use It |
|---|---|---|
| **Customer Phone Hotline** | [`http://localhost:8000/`](http://localhost:8000/) | **Real Phone Simulator**: Dial `333`, talk hands-free without tapping any buttons. The AI assistant detects your speech, answers in a warm Nigerian female voice, and performs your commands. |
| **Live Stage Console** | [`http://localhost:8000/stage`](http://localhost:8000/stage) | **Hackathon Presentation View**: Dual-panel view showing the phone simulator side-by-side with live ASR/LLM telemetry, NIP transaction ledger, and step-by-step pipeline tracing. Press `P` for Stage Mode (projector scaling). |
| **Bank Admin Portal** | [`http://localhost:8000/admin`](http://localhost:8000/admin) | **Enterprise Portal**: Gated by staff auth (`Staff ID: OP-77402`, `Token: lyfpartner2026`). Inspect all completed voice sessions, audio transcripts, and fraud escalation queues. |

---

## 🎙️ Step-by-Step Walkthrough (Demo Scripts)

### Demo 1: Balance Inquiry (Zero Auth Friction)
1. Open [`http://localhost:8000/`](http://localhost:8000/)
2. Tap the green call button to dial **333**.
3. The assistant greets you: *"Welcome to Lyfpartner! How can I assist you today?"*
4. Speak normally: **"What is my account balance?"**
5. The assistant detects silence automatically, transcribes your speech via Groq Whisper, and replies: *"Your current account balance is 250,000 Naira."*

### Demo 2: Money Transfer with Voice PIN Elevation
1. While on the call, say: **"I want to transfer 5,000 Naira to Musa Bello."**
2. The assistant recognizes a Tier-2 sensitive financial action and prompts for authorization: *"Please say your 4-digit voice PIN."*
3. Speak your PIN clearly: **"1 2 3 4"** (or dial it on the in-call keypad).
4. The system validates the PBKDF2 hash, elevates the session, and asks for confirmation: *"PIN verified. Confirm transfer of 5,000 Naira to Musa Bello?"*
5. Say: **"Yes, proceed"** (or *"Oya"* / *"Eh"* / *"Go ahead"*).
6. The transfer executes on the NIP sandbox ledger, generates reference `NIP-20261114-XXXX`, and delivers an immediate SMS receipt notification to the phone.

### Demo 3: Multilingual Code-Switching
1. Select **HA** (Hausa), **YO** (Yoruba), or **IG** (Igbo) on the top bar.
2. Dial **333**.
3. **Hausa:** Say *"Ina son in duba ragowar kudi na"* → Assistant replies *"Ragowar asusunka shine 250,000 Naira."*
4. **Yoruba:** Say *"Mo fe san owo ina"* → Assistant prompts for electricity meter details.
5. **Igbo:** Say *"Echere m ego ole m nwere"* → Assistant speaks account balance in Igbo.

---

## 🛠️ Technology Stack & Architecture

- **Backend:** Python 3.11+, FastAPI (Gateway, KYC, Bank, Support, Unified Runner)
- **ASR (Speech-to-Text):** Groq Whisper Large v3 Turbo (`whisper-large-v3-turbo`) with real-time `ffmpeg` pipeline transcoding
- **LLM / Conversational Engine:** Groq API (`openai/gpt-oss-20b`) with deterministic banking security guards
- **TTS (Text-to-Speech):** Microsoft Edge Neural TTS (`en-NG-EzinneNeural` female Nigerian voice) encoded at native 24kHz PCM16 WAV + Google TTS for regional languages
- **Frontend:** React 19, Vite, Pure CSS iPhone/Feature Phone Simulators (zero external UI dependencies, zero emojis, full SVG icons)
- **Database & Ledger:** SQLite / SQLAlchemy async session with NIP ledger audit logs

---

## ⚡ Quickstart & Local Installation

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- `ffmpeg` (installed via `brew install ffmpeg` on macOS or `apt install ffmpeg` on Linux)

### 2. Setup Backend & Virtualenv
```bash
git clone https://github.com/Blackscorche/lyfpartner.git
cd lyfpartner

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install edge-tts gTTS scipy
```

### 3. Environment Configuration (`.env`)
Create a `.env` file in the root directory:
```ini
TTS_PROVIDER=natural
LLM_PROVIDER=groq
ASR_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

### 4. Build Frontend
```bash
cd web
npm install
npm run build
cd ..
```

### 5. Launch the Server
```bash
source .venv/bin/activate
python run.py
```
Open **`http://localhost:8000`** in Chrome, Edge, or Safari.

---

## 🧪 Running Automated Tests

Lyfpartner includes a comprehensive test suite validating all end-to-end user journeys:
```bash
source .venv/bin/activate
python -m pytest -v
```
**Test Results: 14/14 tests passing (100% green).**

---

## 📄 License & Team

Built with ❤️ for **Zenith Bank Zecathon 6.0** by the Lyfpartner Team.
Licensed under MIT.
