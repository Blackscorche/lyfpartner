/**
 * Lyfpatner Multilingual Intelligence Catalog
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
    greeting: 'Sannu! Barka da zuwa Lyfpatner. Don Allah fadi lambar sirrinka.',
    greetingTranslation: 'Hello! Welcome to Lyfpatner. Please speak your 4-digit PIN.',
    quickPhrases: [
      {
        id: 'pin',
        label: 'Speak PIN: 1-2-3-4',
        text: 'Lambar sirri na daya biyu uku hudu',
        translation: 'My PIN is 1-2-3-4',
        type: 'auth'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'Ina son duba kudi na a asusu',
        translation: 'I want to check my account balance',
        type: 'inquiry'
      },
      {
        id: 'transfer',
        label: 'Transfer ₦5,000 to Musa',
        text: 'Tura Naira dubu biyar zuwa ga Musa Bello',
        translation: 'Send 5,000 Naira to Musa Bello',
        type: 'transfer'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_ha_01', caller_id: '+2348000000001', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'Sannu! Barka da zuwa Lyfpatner. Don Allah fadi lambar sirrinka.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 3200, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'Daya biyu uku hudu (1234)', confidence: 0.98, latencyMs: 220 } },
      { timeMs: 3900, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.96, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'An tabbatar da lambar sirri. Yaya zan iya taimaka muku yau?', stage: 'TTS', latencyMs: 160 } },
      { timeMs: 7000, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'Ina son duba kudi na a asusu', confidence: 0.97, latencyMs: 210 } },
      { timeMs: 7800, type: 'tool.call', data: { tool: 'check_balance', result: { balance_naira: 250000 } } },
      { timeMs: 8800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'Kudin ku a asusun banki Naira dubu dari biyu da hamsin (₦250,000.00) ne.', stage: 'TTS', latencyMs: 190 } },
      { timeMs: 11500, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'Tura Naira dubu biyar zuwa ga Musa Bello', confidence: 0.96, latencyMs: 230 } },
      { timeMs: 12500, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Musa Bello', bank: 'First Bank', amount_naira: 5000 } } },
      { timeMs: 13800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'Kuna son tura Naira 5,000 ga Musa Bello a First Bank. In tura?', stage: 'TTS', latencyMs: 170 } },
      { timeMs: 16000, type: 'asr.final', data: { speaker: 'caller', language: 'ha', text: 'I mana, tura shi yanzu', confidence: 0.99, latencyMs: 180 } },
      { timeMs: 16800, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-8831', recipient: 'Musa Bello', bank: 'First Bank', amount_naira: 5000, status: 'SETTLED' } },
      { timeMs: 17600, type: 'agent.reply', data: { speaker: 'assistant', language: 'ha', text: 'An tura Naira 5,000 ga Musa Bello cikin nasara. An aiko muku da sakon SMS na biyan kudi.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 20500, type: 'call.ended', data: { duration_seconds: 21, turn_count: 5, outcome: 'completed', sms_receipt: 'Lyfpatner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-8831. Bal: NGN 244,990.00' } }
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
    greeting: 'Bawo ni! E kaabo si Lyfpatner. E jowo so nomba asiri yin.',
    greetingTranslation: 'Hello! Welcome to Lyfpatner. Please state your secret PIN.',
    quickPhrases: [
      {
        id: 'pin',
        label: 'Speak PIN: 1-2-3-4',
        text: 'Nomba asiri mi ni okan meji meta merin',
        translation: 'My PIN is 1-2-3-4',
        type: 'auth'
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
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_yo_02', caller_id: '+2348000000002', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'Bawo ni! E kaabo si Lyfpatner. E jowo so nomba asiri yin.', stage: 'TTS', latencyMs: 175 } },
      { timeMs: 3200, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Okan meji meta merin (1234)', confidence: 0.98, latencyMs: 220 } },
      { timeMs: 3900, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.95, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'A ti fowo si nomba asiri yin. Bawo ni a se le ran yin lowo loni?', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 7000, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Elo lo ku ninu akaunti mi?', confidence: 0.97, latencyMs: 200 } },
      { timeMs: 7800, type: 'tool.call', data: { tool: 'check_balance', result: { balance_naira: 180000 } } },
      { timeMs: 8800, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'Iye owo to ku ninu akaunti yin je egberun lona ogosan Naira (₦180,000.00).', stage: 'TTS', latencyMs: 185 } },
      { timeMs: 11500, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Mo fe san owo ina NEPA egberun mefa', confidence: 0.96, latencyMs: 220 } },
      { timeMs: 12500, type: 'tool.call', data: { tool: 'pay_bill', result: { biller: 'IKEDC Electricity', amount_naira: 6000 } } },
      { timeMs: 13800, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'Se ki n san egberun mefa Naira fun ina IKEDC sori mita yin?', stage: 'TTS', latencyMs: 170 } },
      { timeMs: 16000, type: 'asr.final', data: { speaker: 'caller', language: 'yo', text: 'Beeni, san owo ina na', confidence: 0.99, latencyMs: 180 } },
      { timeMs: 16800, type: 'transfer.confirmed', data: { reference: 'BILL-20261114-4902', recipient: 'IKEDC Ikeja Electric', bank: 'Utility Payment', amount_naira: 6000, status: 'SETTLED' } },
      { timeMs: 17600, type: 'agent.reply', data: { speaker: 'assistant', language: 'yo', text: 'A ti san owo ina NEPA egberun mefa Naira laseyori. E o gba SMS re nisisiyi.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 20500, type: 'call.ended', data: { duration_seconds: 21, turn_count: 5, outcome: 'completed', sms_receipt: 'Lyfpatner Bill Paid: NGN 6,000.00 to IKEDC. Token: 4920-1849-2910-4821. Bal: NGN 173,990.00' } }
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
    greeting: 'Nnọọ! Nnọọ na Lyfpatner. Biko kwuo nọmba nzuzo gi.',
    greetingTranslation: 'Welcome! Welcome to Lyfpatner. Please speak your secret PIN.',
    quickPhrases: [
      {
        id: 'pin',
        label: 'Speak PIN: 1-2-3-4',
        text: 'Nọmba nzuzo m bu otu abuo ato ano',
        translation: 'My PIN is 1-2-3-4',
        type: 'auth'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'Ego ole fọdụrụ na akaụntụ m?',
        translation: 'How much money is left in my account?',
        type: 'inquiry'
      },
      {
        id: 'transfer',
        label: 'Send ₦10,000 to Chinedu',
        text: 'Achọrọ m iziga puku naira iri nye Chinedu',
        translation: 'I want to send 10,000 Naira to Chinedu',
        type: 'transfer'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_ig_03', caller_id: '+2348000000003', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Nnọọ! Nnọọ na Lyfpatner. Biko kwuo nọmba nzuzo gi.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 3200, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Otu abuo ato ano (1234)', confidence: 0.98, latencyMs: 220 } },
      { timeMs: 3900, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.97, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'A kwadoro nọmba nzuzo gi. Kedu ka m ga-esi nyere gi aka taa?', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 7000, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Ego ole fọdụrụ na akaụntụ m?', confidence: 0.97, latencyMs: 210 } },
      { timeMs: 7800, type: 'tool.call', data: { tool: 'check_balance', result: { balance_naira: 320000 } } },
      { timeMs: 8800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Ego fọdụrụ na akaụntụ gi bu puku naira narị atọ na iri abụọ (₦320,000.00).', stage: 'TTS', latencyMs: 190 } },
      { timeMs: 11500, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Achọrọ m iziga puku naira iri nye Chinedu Obi', confidence: 0.96, latencyMs: 230 } },
      { timeMs: 12500, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Chinedu Obi', bank: 'Access Bank', amount_naira: 10000 } } },
      { timeMs: 13800, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Ị chọrọ iziga ₦10,000 nye Chinedu Obi na Access Bank. M ziga ya?', stage: 'TTS', latencyMs: 175 } },
      { timeMs: 16000, type: 'asr.final', data: { speaker: 'caller', language: 'ig', text: 'Ee, ziga ya ugbua', confidence: 0.99, latencyMs: 180 } },
      { timeMs: 16800, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-9912', recipient: 'Chinedu Obi', bank: 'Access Bank', amount_naira: 10000, status: 'SETTLED' } },
      { timeMs: 17600, type: 'agent.reply', data: { speaker: 'assistant', language: 'ig', text: 'Ezila ₦10,000 nye Chinedu Obi nke ọma. Anyị ezigala ozi SMS nnabata.', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 20500, type: 'call.ended', data: { duration_seconds: 21, turn_count: 5, outcome: 'completed', sms_receipt: 'Lyfpatner Debit: NGN 10,000.00 to Chinedu Obi. Ref: NIP-20261114-9912. Bal: NGN 309,990.00' } }
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
    greeting: 'Welcome to Lyfpatner voice banking. Please speak your 4-digit PIN.',
    greetingTranslation: 'Welcome to Lyfpatner voice banking. Please speak your 4-digit PIN.',
    quickPhrases: [
      {
        id: 'pin',
        label: 'Speak PIN: 1-2-3-4',
        text: 'My PIN is one two three four',
        translation: 'PIN authorization 1234',
        type: 'auth'
      },
      {
        id: 'bal',
        label: 'Check Balance',
        text: 'How much dey inside my account balance?',
        translation: 'Account balance inquiry',
        type: 'inquiry'
      },
      {
        id: 'transfer',
        label: 'Transfer ₦5,000 to Musa',
        text: 'Send 5000 naira to Musa Bello right now',
        translation: 'Instant NIP bank transfer',
        type: 'transfer'
      }
    ],
    replayEvents: [
      { timeMs: 0, type: 'call.started', data: { session_id: 'sess_en_04', caller_id: '+2348000000004', channel: 'telephony' } },
      { timeMs: 1000, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'Welcome to Lyfpatner voice banking. Please speak your 4-digit PIN.', stage: 'TTS', latencyMs: 170 } },
      { timeMs: 3200, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'One two three four (1234)', confidence: 0.99, latencyMs: 210 } },
      { timeMs: 3900, type: 'auth.update', data: { pin_verified: true, voice_match_score: 0.98, auth_level: 'full', status: 'UNLOCKED' } },
      { timeMs: 4800, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'PIN verified successfully. How can I help you today?', stage: 'TTS', latencyMs: 155 } },
      { timeMs: 7000, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'How much dey inside my account balance?', confidence: 0.98, latencyMs: 195 } },
      { timeMs: 7800, type: 'tool.call', data: { tool: 'check_balance', result: { balance_naira: 410000 } } },
      { timeMs: 8800, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'Your account balance is Four Hundred and Ten Thousand Naira (₦410,000.00).', stage: 'TTS', latencyMs: 180 } },
      { timeMs: 11500, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'Send 5000 naira to Musa Bello right now', confidence: 0.97, latencyMs: 220 } },
      { timeMs: 12500, type: 'tool.call', data: { tool: 'quote_transfer', result: { beneficiary_name: 'Musa Bello', bank: 'First Bank', amount_naira: 5000 } } },
      { timeMs: 13800, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: 'You are transferring ₦5,000 to Musa Bello at First Bank. Should I confirm?', stage: 'TTS', latencyMs: 165 } },
      { timeMs: 16000, type: 'asr.final', data: { speaker: 'caller', language: 'en', text: 'Yes, confirm the transfer', confidence: 0.99, latencyMs: 175 } },
      { timeMs: 16800, type: 'transfer.confirmed', data: { reference: 'NIP-20261114-7740', recipient: 'Musa Bello', bank: 'First Bank', amount_naira: 5000, status: 'SETTLED' } },
      { timeMs: 17600, type: 'agent.reply', data: { speaker: 'assistant', language: 'en', text: '₦5,000 has been transferred to Musa Bello successfully. SMS receipt sent.', stage: 'TTS', latencyMs: 175 } },
      { timeMs: 20500, type: 'call.ended', data: { duration_seconds: 21, turn_count: 5, outcome: 'completed', sms_receipt: 'Lyfpatner Debit: NGN 5,000.00 to Musa Bello. Ref: NIP-20261114-7740. Bal: NGN 404,990.00' } }
    ]
  }
}
