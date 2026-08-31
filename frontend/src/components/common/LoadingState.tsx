import React from 'react'
import { Card } from './Card'

interface LoadingStateProps {
  rows?: number
  message?: string
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  rows = 4,
  message = 'Loading economic intelligence...',
}) => {
  return (
    <div className="w-full space-y-4 animate-pulse">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: rows }).map((_, i) => (
          <Card key={i} className="h-28 bg-slate-100/70 border-slate-200" padding="md">
            <div className="h-3 w-20 bg-slate-200 rounded mb-3" />
            <div className="h-6 w-32 bg-slate-200 rounded mb-2" />
            <div className="h-3 w-24 bg-slate-200 rounded" />
          </Card>
        ))}
      </div>
      <Card className="h-64 bg-slate-100/70 border-slate-200 flex flex-col items-center justify-center text-slate-400 gap-3">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-medium text-slate-500">{message}</span>
      </Card>
    </div>
  )
}
