import type { Factor } from './types'

const shortDate = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

const longDate = new Intl.DateTimeFormat('en-GB', {
  weekday: 'short',
  day: '2-digit',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
})

const timestampFormatter = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'UTC',
  timeZoneName: 'short',
})

export function formatDate(iso: string, style: 'short' | 'long' = 'short'): string {
  const date = new Date(`${iso}T00:00:00Z`)
  return (style === 'long' ? longDate : shortDate).format(date)
}

export function formatTimestamp(iso: string): string {
  return timestampFormatter.format(new Date(iso))
}

export function formatPercent(value: number, digits = 0): string {
  const percent = value * 100
  if (percent === 0) return '0%'
  if (percent < 0.1) return '<0.1%'
  return `${percent.toFixed(percent < 10 ? Math.max(digits, 1) : digits)}%`
}

export function formatSigned(value: number, digits = 0): string {
  if (value === 0) return '0'
  return `${value > 0 ? '+' : ''}${value.toFixed(digits)}`
}

export function formatFactorValue(factor: Factor): string {
  if (factor.unit === 'grid') return `P${factor.value}`
  const digits = factor.unit === 's/lap' ? 2 : 1
  const sign = factor.value > 0 ? '+' : ''
  return `${sign}${factor.value.toFixed(digits)} ${factor.unit}`
}
