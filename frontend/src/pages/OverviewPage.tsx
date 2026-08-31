import React from 'react'
import {
  Wallet,
  Receipt,
  FileSpreadsheet,
  Boxes,
  Clock,
  Flame,
  Percent,
  TrendingDown,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/common/Card'
import { StatCard } from '@/components/common/StatCard'
import { Badge } from '@/components/common/Badge'
import { StatusIndicator } from '@/components/common/StatusIndicator'
import { LoadingState } from '@/components/common/LoadingState'
import { ErrorState } from '@/components/common/ErrorState'
import { CashflowTimelineChart } from '@/components/charts/CashflowTimelineChart'
import { useBusinessState } from '@/hooks/useMerchant'
import { useSnapshots } from '@/hooks/useSnapshots'
import { useNavigate } from 'react-router-dom'

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: state, isLoading: stateLoading, error: stateError, refetch } = useBusinessState()
  const { data: snapshots, isLoading: snapshotsLoading } = useSnapshots()

  if (stateLoading || snapshotsLoading) {
    return <LoadingState message="Calculating real-time economic state and liquidity outlook..." />
  }

  if (stateError || !state) {
    return (
      <ErrorState
        title="Failed to load merchant overview"
        message="Could not retrieve the current liquidity state. Please verify backend service connectivity."
        onRetry={() => refetch()}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Top 8 KPI Grid */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Cash Available"
          value={state.cash.formatted_value}
          subtitle={state.cash.label}
          status={state.cash.status}
          trend={state.cash.trend}
          trendPct={state.cash.trend_pct}
          benchmark={state.cash.benchmark}
          icon={<Wallet className="w-4 h-4" />}
          onClick={() => navigate('/business-state')}
        />
        <StatCard
          title="Receivables Book"
          value={state.receivables.formatted_value}
          subtitle={state.receivables.label}
          status={state.receivables.status}
          trend={state.receivables.trend}
          trendPct={state.receivables.trend_pct}
          benchmark={state.receivables.benchmark}
          icon={<Receipt className="w-4 h-4" />}
          onClick={() => navigate('/receivables')}
        />
        <StatCard
          title="Accounts Payable"
          value={state.payables.formatted_value}
          subtitle={state.payables.label}
          status={state.payables.status}
          trend={state.payables.trend}
          trendPct={state.payables.trend_pct}
          benchmark={state.payables.benchmark}
          icon={<FileSpreadsheet className="w-4 h-4" />}
          onClick={() => navigate('/business-state')}
        />
        <StatCard
          title="Inventory Valuation"
          value={state.inventory_value.formatted_value}
          subtitle={state.inventory_value.label}
          status={state.inventory_value.status}
          trend={state.inventory_value.trend}
          trendPct={state.inventory_value.trend_pct}
          benchmark={state.inventory_value.benchmark}
          icon={<Boxes className="w-4 h-4" />}
          onClick={() => navigate('/inventory')}
        />
        <StatCard
          title="Aging Inventory"
          value={state.aging_inventory.formatted_value}
          subtitle={state.aging_inventory.label}
          status={state.aging_inventory.status}
          trend={state.aging_inventory.trend}
          trendPct={state.aging_inventory.trend_pct}
          benchmark={state.aging_inventory.benchmark}
          icon={<Clock className="w-4 h-4" />}
          onClick={() => navigate('/inventory')}
        />
        <StatCard
          title="Cash Runway"
          value={state.cash_runway.formatted_value}
          subtitle={state.cash_runway.label}
          status={state.cash_runway.status}
          trend={state.cash_runway.trend}
          trendPct={state.cash_runway.trend_pct}
          benchmark={state.cash_runway.benchmark}
          icon={<Flame className="w-4 h-4" />}
          onClick={() => navigate('/business-state')}
        />
        <StatCard
          title="Gross Margin"
          value={state.gross_margin.formatted_value}
          subtitle={state.gross_margin.label}
          status={state.gross_margin.status}
          trend={state.gross_margin.trend}
          trendPct={state.gross_margin.trend_pct}
          benchmark={state.gross_margin.benchmark}
          icon={<Percent className="w-4 h-4" />}
          onClick={() => navigate('/business-state')}
        />
        <StatCard
          title="Demand Trend"
          value={state.demand_trend.formatted_value}
          subtitle={state.demand_trend.label}
          status={state.demand_trend.status}
          trend={state.demand_trend.trend}
          trendPct={state.demand_trend.trend_pct}
          benchmark={state.demand_trend.benchmark}
          icon={<TrendingDown className="w-4 h-4" />}
          onClick={() => navigate('/business-state')}
        />
      </section>

      {/* Main Grid: Business State Panel & Liquidity Outlook */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Business State & Cashflow Timeline */}
        <div className="lg:col-span-8 space-y-6">
          <Card>
            <CardHeader className="border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <CardTitle>Business State</CardTitle>
                  <Badge variant={state.liquidity_status} size="sm" dot>
                    {state.liquidity_status}
                  </Badge>
                </div>
                <CardDescription>
                  Live operational dimensions and 30-day cash balance velocity
                </CardDescription>
              </div>
              <button
                onClick={() => navigate('/business-state')}
                className="text-xs text-brand-600 hover:text-brand-700 font-semibold inline-flex items-center gap-1 shrink-0"
              >
                Full Scorecard <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </CardHeader>

            {/* 5 Dimension Status Strips */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 mb-5">
              <StatusIndicator
                status={state.cash_runway.status}
                label="Liquidity"
                sublabel={`${state.cash_runway.value}d Runway`}
              />
              <StatusIndicator
                status={state.aging_inventory.status}
                label="Inventory"
                sublabel={`${state.aging_inventory.status}`}
              />
              <StatusIndicator
                status={state.demand_trend.status}
                label="Demand"
                sublabel={state.demand_trend.formatted_value}
              />
              <StatusIndicator
                status={state.receivables.status}
                label="Collections"
                sublabel="DSO 42d"
              />
              <StatusIndicator
                status={state.fulfillment_capacity.status}
                label="Fulfillment"
                sublabel={state.fulfillment_capacity.formatted_value}
              />
            </div>

            {/* Cash Balance 30-Day Timeline Chart */}
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2 px-1">
                <span>Cash Balance Trajectory (30 Days)</span>
                <span className="text-[11px] text-slate-400 font-normal">
                  • Event markers denote major settlements &amp; dues
                </span>
              </div>
              <CashflowTimelineChart data={snapshots?.data || []} height={260} />
            </div>
          </Card>
        </div>

        {/* Right Column (4 cols): Liquidity Outlook & Pressure Drivers */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="border-amber-200/90 bg-amber-50/20">
            <CardHeader className="border-b border-amber-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-amber-100 text-amber-700 rounded">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <CardTitle className="text-amber-950">Liquidity Outlook</CardTitle>
                  <CardDescription className="text-amber-700">
                    Deterministic stress analysis
                  </CardDescription>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-amber-900 tabular-nums">
                  {state.liquidity_stress_score}
                  <span className="text-xs text-amber-600 font-normal">/100</span>
                </div>
                <div className="text-[10px] font-semibold uppercase text-amber-600 tracking-wider">
                  Stress Index
                </div>
              </div>
            </CardHeader>

            {/* Headline Message */}
            <div className="mt-4 p-3 rounded-md bg-amber-100/70 border border-amber-200/80">
              <div className="text-xs font-bold text-amber-950 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                {state.liquidity_outlook_headline}
              </div>
              <p className="text-xs text-amber-900 mt-1 leading-relaxed">
                {state.liquidity_outlook_summary}
              </p>
            </div>

            {/* Primary Drivers List */}
            <div className="mt-4 space-y-2.5">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Primary Pressure Drivers
              </div>
              {state.drivers.map((driver) => (
                <div
                  key={driver.id}
                  className="p-3 bg-white rounded-md border border-slate-200/90 text-xs shadow-xs space-y-1"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-900 truncate">
                      {driver.title}
                    </span>
                    <Badge variant={driver.severity} size="sm">
                      {driver.category}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-snug">
                    {driver.description}
                  </p>
                </div>
              ))}
            </div>

            {/* Working Capital Footnote */}
            <div className="mt-4 pt-3 border-t border-amber-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">Net Working Capital:</span>
              <span className="font-bold text-slate-900 tabular-nums">
                {state.working_capital_formatted}
              </span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
