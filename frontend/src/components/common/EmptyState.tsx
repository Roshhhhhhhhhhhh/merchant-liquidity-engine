import React from 'react'
import { Card } from './Card'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title?: string
  description?: string
  icon?: React.ReactNode
  action?: React.ReactNode
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There are no active records matching the current filter criteria.',
  icon,
  action,
}) => {
  return (
    <Card className="border-dashed border-slate-300 bg-slate-50/50 p-8 text-center flex flex-col items-center justify-center">
      <div className="p-3 bg-white border border-slate-200 text-slate-400 rounded-lg mb-3 shadow-sm">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h3 className="text-sm font-semibold text-slate-800 mb-1">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm mb-4">{description}</p>
      {action && <div>{action}</div>}
    </Card>
  )
}
