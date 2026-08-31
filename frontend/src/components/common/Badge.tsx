import React from 'react'
import { cn } from '@/utils/cn'

export type BadgeVariant =
  | 'healthy'
  | 'watch'
  | 'warning'
  | 'critical'
  | 'neutral'
  | 'brand'
  | 'settled'
  | 'in-transit'
  | 'pending'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant | string
  size?: 'sm' | 'md'
  dot?: boolean
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  className,
  ...props
}) => {
  // Normalize string variants
  const normalizedVariant = (() => {
    const v = String(variant).toLowerCase()
    if (v === 'healthy' || v === 'current' || v === 'settled' || v === 'captured' || v === 'enterprise') return 'healthy'
    if (v === 'watch' || v === 'due soon' || v === 'in transit' || v === 'tier-1' || v === 'medium') return 'watch'
    if (v === 'warning' || v === 'aging' || v === 'overdue' || v === 'high') return 'warning'
    if (v === 'critical' || v === 'severely overdue' || v === 'failed' || v === 'declining') return 'critical'
    if (v === 'brand') return 'brand'
    return 'neutral'
  })()

  const variantStyles: Record<BadgeVariant, string> = {
    healthy: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    watch: 'bg-amber-50 text-amber-700 border-amber-200/80',
    warning: 'bg-orange-50 text-orange-700 border-orange-200/80',
    critical: 'bg-rose-50 text-rose-700 border-rose-200/80',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    brand: 'bg-brand-50 text-brand-700 border-brand-200',
    settled: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    'in-transit': 'bg-sky-50 text-sky-700 border-sky-200/80',
    pending: 'bg-slate-100 text-slate-600 border-slate-200',
  }

  const dotColors: Record<BadgeVariant, string> = {
    healthy: 'bg-emerald-500',
    watch: 'bg-amber-500',
    warning: 'bg-orange-500',
    critical: 'bg-rose-500',
    neutral: 'bg-slate-400',
    brand: 'bg-brand-500',
    settled: 'bg-emerald-500',
    'in-transit': 'bg-sky-500',
    pending: 'bg-slate-400',
  }

  const sizeStyles = {
    sm: 'px-1.5 py-0.5 text-[11px] font-medium leading-none',
    md: 'px-2 py-1 text-xs font-medium leading-none',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border tracking-tight',
        variantStyles[normalizedVariant as BadgeVariant] || variantStyles.neutral,
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            'h-1.5 w-1.5 rounded-full shrink-0',
            dotColors[normalizedVariant as BadgeVariant] || dotColors.neutral
          )}
        />
      )}
      <span>{children}</span>
    </span>
  )
}
