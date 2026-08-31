import React from 'react'
import { cn } from '@/utils/cn'

interface StatusIndicatorProps {
  status: string
  label: string
  sublabel?: string
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  sublabel,
}) => {
  const s = status.toLowerCase()

  const colorMap: Record<string, { bg: string; dot: string; text: string; border: string }> = {
    healthy: {
      bg: 'bg-emerald-50/70',
      dot: 'bg-emerald-500 ring-emerald-200',
      text: 'text-emerald-800',
      border: 'border-emerald-200',
    },
    watch: {
      bg: 'bg-amber-50/70',
      dot: 'bg-amber-500 ring-amber-200',
      text: 'text-amber-800',
      border: 'border-amber-200',
    },
    warning: {
      bg: 'bg-orange-50/70',
      dot: 'bg-orange-500 ring-orange-200',
      text: 'text-orange-800',
      border: 'border-orange-200',
    },
    critical: {
      bg: 'bg-rose-50/70',
      dot: 'bg-rose-500 ring-rose-200',
      text: 'text-rose-800',
      border: 'border-rose-200',
    },
    softening: {
      bg: 'bg-amber-50/70',
      dot: 'bg-amber-500 ring-amber-200',
      text: 'text-amber-800',
      border: 'border-amber-200',
    },
  }

  const currentTheme = colorMap[s] || {
    bg: 'bg-slate-50',
    dot: 'bg-slate-400 ring-slate-200',
    text: 'text-slate-700',
    border: 'border-slate-200',
  }

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 p-3 rounded-lg border transition-all',
        currentTheme.bg,
        currentTheme.border
      )}
    >
      <div className="flex items-center gap-2.5">
        <span className={cn('h-2 w-2 rounded-full shrink-0 ring-2', currentTheme.dot)} />
        <div>
          <div className="text-xs font-semibold text-slate-900 tracking-tight">{label}</div>
          {sublabel && <div className="text-[11px] text-slate-500">{sublabel}</div>}
        </div>
      </div>
      <span
        className={cn(
          'text-xs font-medium px-2 py-0.5 rounded bg-white/80 border',
          currentTheme.text,
          currentTheme.border
        )}
      >
        {status}
      </span>
    </div>
  )
}
