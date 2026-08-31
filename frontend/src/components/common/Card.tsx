import React from 'react'
import { cn } from '@/utils/cn'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'subtle' | 'warning' | 'critical' | 'highlight'
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'md',
  className,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-white border-slate-200/90 text-slate-900 shadow-fintech-card',
    subtle: 'bg-slate-50/60 border-slate-200 text-slate-900',
    warning: 'bg-amber-50/40 border-amber-200/80 text-slate-900',
    critical: 'bg-rose-50/40 border-rose-200/80 text-slate-900',
    highlight: 'bg-white border-brand-300 ring-1 ring-brand-100 shadow-fintech-card',
  }

  const paddingStyles = {
    none: 'p-0',
    sm: 'p-3.5',
    md: 'p-5',
    lg: 'p-6',
  }

  return (
    <div
      className={cn(
        'rounded-lg border transition-all duration-150',
        variantStyles[variant],
        paddingStyles[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div className={cn('flex items-center justify-between gap-3 mb-4', className)} {...props}>
    {children}
  </div>
)

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className,
  ...props
}) => (
  <h3 className={cn('text-sm font-semibold text-slate-900 tracking-tight', className)} {...props}>
    {children}
  </h3>
)

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className,
  ...props
}) => (
  <p className={cn('text-xs text-slate-500 mt-0.5 leading-relaxed', className)} {...props}>
    {children}
  </p>
)
