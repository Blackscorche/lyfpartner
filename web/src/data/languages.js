/**
 * Lyfpartner Multilingual Intelligence Catalog
 * Full scenario prompts and replay flows for Hausa, Yoruba, Igbo, and Nigerian English.
 */

export const LANGUAGES = {
  ha: {
    id: 'ha',
    code: 'HA',
    name: 'Hausa',
    region: 'Northern Nigeria (Kano, Kaduna, Sokoto)',
    caller: {
      name: 'Aminu Bello Kano',
      phone: '+2348000000001',
      balanceKobo: 25000000,
      balanceFormatted: '₦250,000.00'
    },
    greeting: 'Sannu! Barka da zuwa Lyfpartner. Yaya zan iya taimaka muku yau? Kuna iya duba kudi a asusu, tura kudi ga wani, ko biyan kudin wuta.',
    greetingTranslation: 'Welcome to Lyfpartner. How can I assist you today? You can check your account balance, transfer money, or pay electricity bills.',
    quickPhrases: [
      {
        id: 'transfer',
        label: 'Transfer ₦5,000 to Musa',
        text: 'Tura Naira dubu biyar zuwa ga Musa Bello',
        translation: 'Send 5,000 Naira to Musa Bello',
        type: 'transfer'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'Ina son duba kudi na a asusu',
        translation: 'I want to check my account balance',
        type: 'inquiry'
      },
      {
        id: 'bill',
        label: 'Pay Electricity',
        text: 'Ina son biyan kudin wuta',
        translation: 'I want to pay electricity bill',
        type: 'bill'
      },
      {
        id: 'pin',
        label: 'Keypad PIN: 1234',
        text: '1234',
        translation: 'Punch in PIN 1234',
        type: 'auth'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_ha_01', caller_id: '+2348000000001', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'Sannu! Barka da zuwa Lyfpartner. Yaya zan iya taimaka muku yau? Kuna iya duba kudi a asusu, tura kudi ga wani, ko biyan kudin wuta.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 3800, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'Tura Naira dubu biyar zuwa ga Musa Bello', confidence: 0.98, latencyMs: 220 } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'Kuna son tura Naira 5,000 ga Musa Bello. Don tsaronka, da fatan kana wuri mai natsuwa da sirri ba a cikin jama\'a ba. Za ka iya danna lambar sirrinka a kan keypad, ko kuma ka fadi ta a fili.', stage: 'TTS', latencyMs: 160 } },
      { timeMs: 7800, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'Daya biyu uku hudu (1234)', confidence: 0.99, latencyMs: 200 } },
      { timeMs: 8500, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.97, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 9200, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Musa Bello', bank: 'First Bank', amount_naira: 5000 } } },
      { timeMs: 10200, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'An tabbatar da lambar sirri! Kuna son tura Naira 5,000 ga Musa Bello a First Bank. In tura?', stage: 'TTS', latencyMs: 170 } },
      { timeMs: 12500, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'I mana, tura shi yanzu', confidence: 0.99, latencyMs: 180 } },
      { timeMs: 13300, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-8831', recipient: 'Musa Bello', bank: 'First Bank', amount_naira: 5000, status: 'SETTLED' } },
      { timeMs: 14200, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'An tura Naira 5,000 ga Musa Bello cikin nasara. An aiko muku da sakon SMS na biyan kudi.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 17200, type: 'call.ended', data: { duration_seconds: 18, turn_count: 4, outcome: 'completed', sms_receipt: 'Lyfpartner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8831. Bal: NGN 244,990.00' } }
    ]
  },

  yo: {
    id: 'yo',
    code: 'YO',
    name: 'Yoruba',
    region: 'Southwestern Nigeria (Lagos, Ibadan, Ogun)',
    caller: {
      name: 'Folake Adeyemi',
      phone: '+2348000000002',
      balanceKobo: 18000000,
      balanceFormatted: '₦180,000.00'
    },
    greeting: 'Bawo ni! E kaabo si Lyfpartner. Bawo ni a se le ran yin lowo loni? E le wo iye owo to ku ninu akaunti yin, gbe owo ranse, tabi san owo ina.',
    greetingTranslation: 'Welcome to Lyfpartner. How can we help you today? You can check your account balance, transfer money, or pay electricity bills.',
    quickPhrases: [
      {
        id: 'transfer',
        label: 'Transfer ₦5,000',
        text: 'Mo fe fi Naira egberun marun ranse si Musa Bello',
        translation: 'Send 5,000 Naira to Musa Bello',
        type: 'transfer'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'Elo lo ku ninu akaunti mi?',
        translation: 'How much money is left in my account?',
        type: 'inquiry'
      },
      {
        id: 'bill',
        label: 'Pay Electricity: ₦6,000',
        text: 'Mo fe san owo ina NEPA egberun mefa',
        translation: 'I want to pay 6,000 Naira electricity bill',
        type: 'bill'
      },
      {
        id: 'pin',
        label: 'Keypad PIN: 1234',
        text: '1234',
        translation: 'Punch in PIN 1234',
        type: 'auth'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_yo_02', caller_id: '+2348000000002', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'Bawo ni! E kaabo si Lyfpartner. Bawo ni a se le ran yin lowo loni? E le wo iye owo to ku ninu akaunti yin, gbe owo ranse, tabi san owo ina.', stage: 'TTS', latencyMs: 175 } },
      { timeMs: 3800, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Mo fe fi Naira egberun marun ranse si Musa Bello', confidence: 0.98, latencyMs: 220 } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'E fe fi Naira 5,000 ranse si Musa Bello. Fun aabo re, a lero pe o wa ni aye ikoko ti o ni aabo. Jowo te nomba asiri re lori keypad, tabi ki o so o jade.', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 7800, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Okan meji meta merin (1234)', confidence: 0.98, latencyMs: 200 } },
      { timeMs: 8500, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.96, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 9200, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Musa Bello', bank: 'First Bank', amount_naira: 5000 } } },
      { timeMs: 10200, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'A ti fowo si nomba asiri yin! Se e fe fi Naira 5,000 ranse si Musa Bello ni First Bank? Se kin tesiwaju?', stage: 'TTS', latencyMs: 170 } },
      { timeMs: 12500, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Beeni, gbe owo na ranse nisisiyi', confidence: 0.99, latencyMs: 180 } },
      { timeMs: 13300, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-8832', recipient: 'Musa Bello', bank: 'First Bank', amount_naira: 5000, status: 'SETTLED' } },
      { timeMs: 14200, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'A ti fi Naira 5,000 ranse si Musa Bello laseyori. A ti fi SMS ranse si foonu yin.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 17200, type: 'call.ended', data: { duration_seconds: 18, turn_count: 4, outcome: 'completed', sms_receipt: 'Lyfpartner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8832. Bal: NGN 174,990.00' } }
    ]
  },

  ig: {
    id: 'ig',
    code: 'IG',
    name: 'Igbo',
    region: 'Southeastern Nigeria (Enugu, Owerri, Onitsha)',
    caller: {
      name: 'Emeka Okonkwo',
      phone: '+2348000000003',
      balanceKobo: 32000000,
      balanceFormatted: '₦320,000.00'
    },
    greeting: 'Nnọọ! Nnọọ na Lyfpartner. Kedu ka m ga-esi nyere gi aka taa? I nwere ike ilele ego fọdụrụ na akaụntụ gi, zipu ego, ma obu kwuo ugwo oku eletrik.',
    greetingTranslation: 'Welcome to Lyfpartner. How can I help you today? You can check your account balance, send money, or pay electricity bills.',
    quickPhrases: [
      {
        id: 'transfer',
        label: 'Send ₦10,000 to Chinedu',
        text: 'Achọrọ m iziga puku naira iri nye Chinedu',
        translation: 'I want to send 10,000 Naira to Chinedu',
        type: 'transfer'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'Ego ole fọdụrụ na akaụntụ m?',
        translation: 'How much money is left in my account?',
        type: 'inquiry'
      },
      {
        id: 'bill',
        label: 'Pay Electricity',
        text: 'Achọrọ m ikwu ugwọ ọkụ eletrik',
        translation: 'I want to pay electricity bill',
        type: 'bill'
      },
      {
        id: 'pin',
        label: 'Keypad PIN: 1234',
        text: '1234',
        translation: 'Punch in PIN 1234',
        type: 'auth'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_ig_03', caller_id: '+2348000000003', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Nnọọ! Nnọọ na Lyfpartner. Kedu ka m ga-esi nyere gi aka taa? I nwere ike ilele ego fọdụrụ na akaụntụ gi, zipu ego, ma obu kwuo ugwo oku eletrik.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 3800, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Achọrọ m iziga puku naira iri nye Chinedu Obi', confidence: 0.98, latencyMs: 220 } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Ị chọrọ iziga ₦10,000 nye Chinedu Obi. Maka nchekwa gi, anyi nwere olileanya na ino n\'ebe zoro ezo nwere nchekwa. Biko pia nọmba nzuzo gi na keypad, ma obu kwuo ya n\'olu.', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 7800, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Otu abuo ato ano (1234)', confidence: 0.98, latencyMs: 200 } },
      { timeMs: 8500, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.97, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 9200, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Chinedu Obi', bank: 'Access Bank', amount_naira: 10000 } } },
      { timeMs: 10200, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'A kwadoro nọmba nzuzo gi! Ị chọrọ iziga ₦10,000 nye Chinedu Obi na Access Bank. M ziga ya?', stage: 'TTS', latencyMs: 175 } },
      { timeMs: 12500, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Ee, ziga ya ugbua', confidence: 0.99, latencyMs: 180 } },
      { timeMs: 13300, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-9912', recipient: 'Chinedu Obi', bank: 'Access Bank', amount_naira: 10000, status: 'SETTLED' } },
      { timeMs: 14200, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Ezila ₦10,000 nye Chinedu Obi nke ọma. Anyị ezigala ozi SMS nnabata.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 17200, type: 'call.ended', data: { duration_seconds: 18, turn_count: 4, outcome: 'completed', sms_receipt: 'Lyfpartner Debit: NGN 10,000.00 to Chinedu Obi. Ref: NIP-20261114-9912. Bal: NGN 309,990.00' } }
    ]
  },

  en: {
    id: 'en',
    code: 'EN',
    name: 'Nigerian English',
    region: 'National / Federal (Pidgin & Nigerian Accented English)',
    caller: {
      name: 'Chidi Williams',
      phone: '+2348000000004',
      balanceKobo: 41000000,
      balanceFormatted: '₦410,000.00'
    },
    greeting: 'Hello! Welcome to Lyfpartner Voice Banking. How can I assist you today? You can check your balance, transfer money to anyone, or pay electricity bills.',
    greetingTranslation: 'Hello! Welcome to Lyfpartner Voice Banking. How can I assist you today? You can check your balance, transfer money to anyone, or pay electricity bills.',
    quickPhrases: [
      {
        id: 'transfer',
        label: 'Transfer ₦5,000 to Musa',
        text: 'Send 5000 naira to Musa Bello right now',
        translation: 'Instant NIP bank transfer',
        type: 'transfer'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'How much dey inside my account balance?',
        translation: 'Account balance inquiry',
        type: 'inquiry'
      },
      {
        id: 'bill',
        label: 'Pay Electricity',
        text: 'I want to pay my IKEDC electricity bill',
        translation: 'Pay electricity utility bill',
        type: 'bill'
      },
      {
        id: 'pin',
        label: 'Keypad PIN: 1234',
        text: '1234',
        translation: 'Punch in PIN 1234',
        type: 'auth'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_en_04', caller_id: '+2348000000004', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'Hello! Welcome to Lyfpartner Voice Banking. How can I assist you today? You can check your balance, transfer money to anyone, or pay electricity bills.', stage: 'TTS', latencyMs: 170 } },
      { timeMs: 3800, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'Send 5000 naira to Musa Bello right now', confidence: 0.98, latencyMs: 210 } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'Alright! You want to send 5,000 Naira to Musa Bello. For your security, hope you are in a private space and have your privacy? Please punch in your 4-digit PIN on the keypad, or say it out loud.', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 7800, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'One two three four (1234)', confidence: 0.99, latencyMs: 200 } },
      { timeMs: 8500, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.98, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 9200, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Musa Bello', bank: 'First Bank', amount_naira: 5000 } } },
      { timeMs: 10200, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'PIN verified! You are transferring ₦5,000 to Musa Bello at First Bank. Should I confirm?', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 12500, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'Yes, confirm the transfer now', confidence: 0.99, latencyMs: 175 } },
      { timeMs: 13300, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-7740', recipient: 'Musa Bello', bank: 'First Bank', amount_naira: 5000, status: 'SETTLED' } },
      { timeMs: 14200, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: '₦5,000 has been transferred to Musa Bello successfully. SMS receipt sent.', stage: 'TTS', latencyMs: 175 } },
      { timeMs: 17200, type: 'call.ended', data: { duration_seconds: 18, turn_count: 4, outcome: 'completed', sms_receipt: 'Lyfpartner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-7740. Bal: NGN 404,990.00' } }
    ]
  }
}
