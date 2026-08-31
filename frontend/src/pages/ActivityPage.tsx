import React, { useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Receipt,
  Boxes,
  Wallet,
  ArrowLeftRight,
  TrendingDown,
  Clock,
  Filter,
} from 'lucide-react'
import { Card } from '@/components/common/Card'
import { StatCard } from '@/components/common/StatCard'
import { Badge } from '@/components/common/Badge'
import { LoadingState } from '@/components/common/LoadingState'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { useActivity } from '@/hooks/useActivity'
import { formatDate } from '@/utils/formatters'

export const ActivityPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL')

  const { data, isLoading, error, refetch } = useActivity({
    category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
    severity: selectedSeverity !== 'ALL' ? selectedSeverity : undefined,
  })

  if (isLoading) {
    return <LoadingState message="Loading live operational activity feed..." />
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Failed to load activity log"
        message="Could not retrieve the event audit trail."
        onRetry={() => refetch()}
      />
    )
  }

  const { summary, events } = data

  const getEventIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'liquidity':
        return <Wallet className="w-4 h-4 text-sky-600" />
      case 'receivables':
        return <Receipt className="w-4 h-4 text-emerald-600" />
      case 'inventory':
        return <Boxes className="w-4 h-4 text-amber-600" />
      case 'payables':
        return <Clock className="w-4 h-4 text-rose-600" />
      case 'transactions':
        return <ArrowLeftRight className="w-4 h-4 text-indigo-600" />
      case 'demand':
        return <TrendingDown className="w-4 h-4 text-orange-600" />
      default:
        return <Activity className="w-4 h-4 text-slate-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Activity Metric Summary */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          title="Total Events Logged"
          value={summary.total_events}
          subtitle="System audit feed"
          status="Healthy"
          icon={<Activity className="w-4 h-4" />}
        />
        <StatCard
          title="High / Critical Alerts"
          value={summary.high_count + summary.critical_count}
          subtitle="Require operational review"
          status={summary.high_count + summary.critical_count > 0 ? 'Warning' : 'Healthy'}
          icon={<AlertTriangle className="w-4 h-4" />}
        />
        <StatCard
          title="Active Categories"
          value={summary.categories.length}
          subtitle="Tracked operational areas"
          status="Healthy"
          icon={<Filter className="w-4 h-4" />}
        />
        <StatCard
          title="Realtime Ingestion"
          value="Online"
          subtitle="20s automatic polling"
          status="Healthy"
          icon={<Clock className="w-4 h-4" />}
        />
      </section>

      {/* Filter & Timeline Container */}
      <Card padding="none">
        {/* Filter Bar */}
        <div className="p-4 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Category:</span>
            {['ALL', 'Liquidity', 'Receivables', 'Inventory', 'Payables', 'Transactions', 'Demand'].map(
              (cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    selectedCategory === cat
                      ? 'bg-brand-600 text-white shadow-xs'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {cat}
                </button>
              )
            )}
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Severity:</span>
            {['ALL', 'Critical', 'High', 'Medium', 'Info'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  selectedSeverity === sev
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-600 hover:bg-slate-200/60'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* Chronological Timeline */}
        {events.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No activity events found"
              description="There are no events matching your active filters."
              action={
                <button
                  onClick={() => {
                    setSelectedCategory('ALL')
                    setSelectedSeverity('ALL')
                  }}
                  className="px-3 py-1.5 bg-white border border-slate-300 rounded text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Clear Filters
                </button>
              }
            />
          </div>
        ) : (
          <div className="p-6 space-y-4">
            {events.map((event, index) => (
              <div key={event.id} className="relative flex items-start gap-4 group">
                {/* Timeline vertical bar */}
                {index < events.length - 1 && (
                  <div className="absolute left-4 top-8 -bottom-4 w-0.5 bg-slate-200 group-hover:bg-slate-300 transition-colors" />
                )}

                {/* Event Icon Bubble */}
                <div className="relative z-10 h-8 w-8 rounded-full bg-white border-2 border-slate-200 flex items-center justify-center shadow-xs group-hover:border-brand-500 transition-colors shrink-0">
                  {getEventIcon(event.category)}
                </div>

                {/* Event Content Card */}
                <div className="flex-1 bg-white border border-slate-200 rounded-lg p-4 shadow-fintech-card group-hover:border-slate-300 transition-colors space-y-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">{event.title}</span>
                      <Badge variant={event.category} size="sm">
                        {event.category}
                      </Badge>
                      <Badge variant={event.severity} size="sm" dot>
                        {event.severity}
                      </Badge>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {formatDate(event.created_at, 'full')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{event.description}</p>

                  {/* Optional JSON metadata pill list */}
                  {event.parsed_metadata && Object.keys(event.parsed_metadata).length > 0 && (
                    <div className="pt-2 mt-1 border-t border-slate-100 flex flex-wrap gap-2 text-[11px] font-mono text-slate-500">
                      {Object.entries(event.parsed_metadata).map(([k, v]) => (
                        <span
                          key={k}
                          className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-700"
                        >
                          <span className="text-slate-400">{k}:</span> {String(v)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
