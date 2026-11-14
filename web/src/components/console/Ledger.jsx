import React from 'react'
import { BankIcon } from '../common/Icons'

export default function Ledger({ transactions = [] }) {
  return (
    <div style={{
      background: 'var(--bg-white)',
      border: '1.5px solid var(--color-border)',
      borderRadius: 'var(--radius-xl)',
      padding: '16px 20px',
      boxShadow: 'var(--shadow-card)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28,
            height: 28,
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-accent-green-subtle)',
            border: '1px solid var(--color-accent-green-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-accent-green)'
          }}>
            <BankIcon size={14} />
          </div>

          <div>
            <span style={{
              fontSize: 12,
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: 1,
              color: 'var(--color-ink)',
              fontFamily: 'var(--font-mono)'
            }}>
              Core Banking Settlement Ledger
            </span>
            <span style={{ fontSize: 10.5, color: 'var(--color-ink-tertiary)', display: 'block', fontFamily: 'var(--font-mono)' }}>
              NIBSS / NIP Instant Payment Switch Sandbox &bull; ISO 20022
            </span>
          </div>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--color-accent-green-subtle)',
          padding: '4px 12px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--color-accent-green-border)'
        }}>
          <span style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: 'var(--color-accent-green)',
            animation: 'pulseGlow 2.5s infinite'
          }} />
          <span style={{
            fontSize: 10,
            fontWeight: 800,
            fontFamily: 'var(--font-mono)',
            color: 'var(--color-accent-green)'
          }}>
            INSTANT CLEARING
          </span>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-subtle)' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          textAlign: 'left'
        }}>
          <thead>
            <tr style={{
              background: 'var(--bg-paper-surface)',
              borderBottom: '1px solid var(--color-border)',
              color: 'var(--color-ink-tertiary)',
              fontSize: 10,
              textTransform: 'uppercase',
              letterSpacing: 0.8
            }}>
              <th style={{ padding: '10px 14px' }}>Transaction Ref</th>
              <th style={{ padding: '10px 14px' }}>Beneficiary Account</th>
              <th style={{ padding: '10px 14px' }}>Bank</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Amount (NGN)</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Settlement</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={5} style={{
                  padding: '24px 14px',
                  textAlign: 'center',
                  color: 'var(--color-ink-tertiary)',
                  fontStyle: 'italic',
                  fontSize: 12
                }}>
                  No money-moving transactions in this session yet. Spoken quotes and debits record and animate here instantly.
                </td>
              </tr>
            ) : (
              transactions.map((tx, idx) => {
                const amount = (tx.amount_naira || (tx.amount_kobo ? tx.amount_kobo / 100 : 5000)).toLocaleString('en-NG', { minimumFractionDigits: 2 })
                const ref = tx.reference || `NIP-20261114-${1000 + idx}`
                const recip = tx.recipient || tx.beneficiary_name || 'Musa Bello'
                const bank = tx.bank || 'First Bank of Nigeria'
                const status = tx.status || 'SETTLED'

                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid var(--color-border-subtle)',
                      background: 'var(--bg-white)',
                      animation: 'slideInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
                    }}
                  >
                    <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--color-ink)' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: 'var(--bg-subtle)',
                        border: '1px solid var(--color-border-subtle)',
                        fontSize: 11
                      }}>
                        {ref}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--color-ink)', fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{
                          width: 24,
                          height: 24,
                          borderRadius: 'var(--radius-full)',
                          background: 'var(--color-accent-green)',
                          color: '#FFFFFF',
                          fontSize: 10,
                          fontWeight: 800,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          {recip.charAt(0)}
                        </span>
                        <span style={{ fontSize: 13, fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                          {recip}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--color-ink-secondary)' }}>
                      {bank}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 800, color: 'var(--color-accent-green)', fontSize: 13.5 }}>
                      ₦{amount}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '4px 10px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 10,
                        fontWeight: 800,
                        background: 'var(--color-accent-green-subtle)',
                        color: 'var(--color-accent-green)',
                        border: '1.5px solid var(--color-accent-green-border)'
                      }}>
                        <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--color-accent-green)' }} />
                        {status}
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
