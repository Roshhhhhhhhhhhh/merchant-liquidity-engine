import React from 'react'
import { Card } from './Card'
import { Badge } from './Badge'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/utils/cn'

export interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  status?: string
  statusLabel?: string
  trend?: 'Up' | 'Down' | 'Stable'
  trendPct?: number
  benchmark?: string
  icon?: React.ReactNode
  className?: string
  compact?: boolean
  onClick?: () => void
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  status,
  statusLabel,
  trend,
  trendPct,
  benchmark,
  icon,
  className,
  compact = false,
  onClick,
}) => {
  return (
    <Card
      padding={compact ? 'sm' : 'md'}
      className={cn(
        'relative overflow-hidden group hover:border-slate-300 transition-colors',
        onClick && 'cursor-pointer hover:shadow-fintech-hover',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-medium text-slate-500 tracking-tight uppercase">
          {title}
        </span>
        {status && (
          <Badge variant={status} size="sm" dot>
            {statusLabel || status}
          </Badge>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-3">
        <div className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight tabular-nums font-sans">
          {value}
        </div>
        {icon && (
          <div className="text-slate-400 p-1.5 bg-slate-50 rounded border border-slate-100 shrink-0">
            {icon}
          </div>
        )}
      </div>

      {(subtitle || trend || benchmark) && (
        <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 gap-2">
          {subtitle && <span className="truncate">{subtitle}</span>}

          <div className="flex items-center gap-1.5 shrink-0 ml-auto font-medium">
            {trend === 'Up' && (
              <span className="inline-flex items-center gap-0.5 text-emerald-600">
                <TrendingUp className="w-3 h-3" />
                {trendPct !== undefined && `${trendPct > 0 ? '+' : ''}${trendPct}%`}
              </span>
            )}
            {trend === 'Down' && (
              <span className="inline-flex items-center gap-0.5 text-rose-600">
                <TrendingDown className="w-3 h-3" />
                {trendPct !== undefined && `${trendPct}%`}
              </span>
            )}
            {trend === 'Stable' && (
              <span className="inline-flex items-center gap-0.5 text-slate-400">
                <Minus className="w-3 h-3" />
                Stable
              </span>
            )}
            {benchmark && !trend && (
              <span className="text-slate-400 font-normal">{benchmark}</span>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}
