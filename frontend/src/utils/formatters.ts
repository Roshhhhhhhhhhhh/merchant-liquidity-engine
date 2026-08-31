/**
 * Utility formatters for Indian Rupee currency, percentages, numbers, and dates.
 */

export function formatINR(
  amount: number | string | null | undefined,
  options: { compact?: boolean } = { compact: true }
): string {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return '₹0.00'
  }

  const num = Number(amount)
  const sign = num < 0 ? '-' : ''
  const abs = Math.abs(num)

  if (options.compact) {
    if (abs >= 10000000) {
      return `${sign}₹${(abs / 10000000).toFixed(2)}Cr`
    } else if (abs >= 100000) {
      return `${sign}₹${(abs / 100000).toFixed(2)}L`
    } else if (abs >= 1000) {
      return `${sign}₹${(abs / 1000).toFixed(1)}k`
    } else {
      return `${sign}₹${abs.toFixed(2)}`
    }
  }

  // Exact Indian numbering format (e.g. ₹4,85,000.00)
  const fixed = abs.toFixed(2)
  const [intPart, decPart] = fixed.split('.')

  let formattedInt = ''
  if (intPart.length <= 3) {
    formattedInt = intPart
  } else {
    const last3 = intPart.substring(intPart.length - 3)
    let other = intPart.substring(0, intPart.length - 3)
    const groups: string[] = []
    while (other.length > 2) {
      groups.unshift(other.substring(other.length - 2))
      other = other.substring(0, other.length - 2)
    }
    if (other.length > 0) {
      groups.unshift(other)
    }
    groups.push(last3)
    formattedInt = groups.join(',')
  }

  return `${sign}₹${formattedInt}.${decPart}`
}

export function formatPct(
  val: number | string | null | undefined,
  options: { includeSign?: boolean; decimals?: number } = { includeSign: false, decimals: 1 }
): string {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return '0.0%'
  }

  const num = Number(val)
  const sign = options.includeSign && num > 0 ? '+' : ''
  const dec = options.decimals !== undefined ? options.decimals : 1

  return `${sign}${num.toFixed(dec)}%`
}

export function formatDate(
  dateVal: string | Date | null | undefined,
  format: 'short' | 'medium' | 'full' = 'medium'
): string {
  if (!dateVal) return '-'

  const d = typeof dateVal === 'string' ? new Date(dateVal) : dateVal
  if (isNaN(d.getTime())) return '-'

  if (format === 'short') {
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  } else if (format === 'medium') {
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  } else {
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
}

export function formatNumber(val: number | string | null | undefined): string {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return '0'
  }
  return Number(val).toLocaleString('en-IN')
}

export function formatDays(days: number | string | null | undefined): string {
  if (days === null || days === undefined || isNaN(Number(days))) {
    return '0 Days'
  }
  const n = Number(days)
  return n === 1 ? '1 Day' : `${n} Days`
}
