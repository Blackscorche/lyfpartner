# Lyfpartner: Voice-First Inclusive Banking Hotline (POC)

Lyfpartner is a phone and web voice assistant that empowers disabled and low-literacy users in Nigeria to bank hands-free by speaking **Hausa, Igbo, Yoruba, or Nigerian English**.

Built for hackathons and production pilots, it operates end-to-end on a mock core banking platform with vendor interfaces for Africa's Talking, Twilio, Hugging Face N-ATLAS ASR models, Spitch TTS, and Gemini.

---

## Architecture Overview

```
                      +------------------------------------------+
                      |         Caller Channels                  |
                      |  - Web Call (Browser Mic / WebSocket)    |
                      |  - Africa's Talking Voice (IVR / XML)    |
                      |  - Twilio Voice (TwiML / Streams)        |
                      +---------------------+--------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------------+
|                                GATEWAY SERVICE (:8000)                                   |
|   /v1/voice/turn  -  /ws/web-call  -  /telephony/at/voice  -  /telephony/twilio/voice   |
+----+---------------------+--------------------+--------------------+--------------------+
     |                     |                    |                    |
     v                     v                    v                    v
+-----------+        +-----------+        +-----------+        +-----------+
|    ASR    |        |   Agent   |        |    TTS    |        |   Auth    |
|  (:8001)  |        |  (:8002)  |        |  (:8003)  |        |  (:8004)  |
| N-ATLAS / |        | LLM Tools |        | Spitch /  |        | Argon2 /  |
|   Mock    |        |  Dialogue |        | PCM Synt  |        | Voiceprint|
+-----------+        +-----+-----+        +-----------+        +-----------+
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
     +------------+ +------------+ +------------+
     | Mock Bank  | |    KYC     | |  Support   |
     |  (:8005)   | |  (:8006)   | |  (:8007)   |
     | Accounts / | | BVN / NIN  | | Tickets /  |
     | Transfers  | | Face Match | | Escalation |
     +------------+ +------------+ +------------+
            |              |              |
            +--------------+--------------+
                           |
                           v
            +----------------------------+
            | Admin & Audit Log (:8008)  |
            | Notifications SMS (:8009)  |
            +----------------------------+
```

---

## Key Features & Global Rules Enforced

1. **Inclusive Native Language Support:**
   - Hausa (`ha`), Igbo (`ig`), Yoruba (`yo`), and Nigerian English (`en-ng`).
2. **Strict Financial Precision:**
   - Money stored and computed exclusively in **integer kobo** (NGN currency). Zero float rounding issues.
3. **Two-Step Transfer Protection:**
   - Transfers require a `quote` step returning a secure `confirmation_token` that expires in 120 seconds, followed by spoken confirmation before execution.
4. **Voice Channel Guardrails:**
   - Configurable transfer limits: 50,000 NGN per transaction; 100,000 NGN daily maximum.
   - Voice transfers restricted to saved beneficiaries only unless verified via trusted caregiver SMS OTP.
5. **Security & Biometrics:**
   - Argon2-hashed spoken PINs.
   - Account lockout after 3 consecutive wrong PIN attempts with caregiver OTP recovery.
   - Speaker embedding voiceprints.
6. **Data Privacy & Tamper-Evident Auditing:**
   - Sensitive data (PINs, BVNs, NINs) is automatically masked from logs.
   - Raw audio deleted immediately after transcription unless `STORE_AUDIO=true`.
   - Every sensitive event writes an immutable audit record.
7. **Swappable Adapters (Zero-Key Dev Ready):**
   - High-fidelity mock providers allow testing every user journey offline without external vendor keys.

---

## 5 Seed Demo Accounts

| Name | Language | Phone | Account No. | Opening Balance | PIN |
|---|---|---|---|---|---|
| **Aminu Kano** | Hausa (`ha`) | `+2348000000001` | `0123456789` | 250,000 NGN | `1234` |
| **Ngozi Eze** | Igbo (`ig`) | `+2348000000002` | `0123456788` | 80,000 NGN | `5678` |
| **Babatunde Adeyemi** | Yoruba (`yo`) | `+2348000000003` | `0123456787` | 15,000 NGN | `4321` |
| **Emeka Johnson** | Nigerian English (`en-ng`) | `+2348000000004` | `0123456786` | 500,000 NGN | `9999` |
| **Hadiza Aliyu** | Hausa (`ha`) | `+2348000000005` | `0123456785` | 2,500 NGN | `1122` |

---

## Quickstart

### 1. Running with Docker Compose
```bash
cp .env.example .env
docker compose up --build
```
- Web UI & Unified API: `http://localhost:8000` (or `http://localhost:3000`)
- OpenAPI Interactive Docs: `http://localhost:8000/docs`

### 2. Local Python Development
```bash
# 1. Setup virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Build frontend (optional: pre-built dist served automatically)
cd web && npm install && npm run build && cd ..

# 3. Run unified server
python run.py
```
Open `http://localhost:8000` in your browser.

---

## Running the Automated Test Suite

All 7 required hackathon demo scenarios and service unit tests run in pytest:

```bash
source .venv/bin/activate
pytest -v
```

### Covered Demo Scenarios
- `test_scenario_1_language_selection_hausa`: Session creation, language setting to Hausa, greeting in Hausa.
- `test_scenario_2_spoken_pin_and_balance_check`: Spoken PIN elevation and balance inquiry read back clearly.
- `test_scenario_3_two_step_transfer_and_sms`: Two-step transfer quote, confirmation, execution, and SMS receipt.
- `test_scenario_4_pay_electricity_bill_yoruba_igbo`: Utility bill payment in Yoruba and Igbo.
- `test_scenario_5_angry_caller_escalation`: Distress detection, human escalation, ticket creation, and transcript archiving.
- `test_scenario_6_wrong_pin_three_times_and_caregiver_unlock`: 3-attempt PIN lockout, caregiver OTP delivery, and unlock.
- `test_scenario_7_new_user_spoken_onboarding_with_bvn`: Voice onboarding with mock BVN verification and account provisioning.
