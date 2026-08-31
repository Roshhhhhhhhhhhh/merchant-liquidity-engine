import React, { useState } from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  Flame,
  Activity,
  ArrowRight,
  RefreshCw,
  Layers,
  BarChart3,
  AlertTriangle,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/common/Card'
import { StatCard } from '@/components/common/StatCard'
import { Badge } from '@/components/common/Badge'
import { LoadingState } from '@/components/common/LoadingState'
import { ErrorState } from '@/components/common/ErrorState'
import { EconomicHealthTimelineChart } from '@/components/charts/EconomicHealthTimelineChart'
import {
  useBusinessState,
  useStateDrivers,
  useStateDelta,
} from '@/hooks/useMerchant'
import { useSnapshots } from '@/hooks/useSnapshots'
import { formatDays } from '@/utils/formatters'

export const BusinessStatePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'drivers' | 'timeline' | 'delta'>('overview')
  const { data: state, isLoading: stateLoading, error: stateError, refetch } = useBusinessState()
  const { data: driversData } = useStateDrivers()
  const { data: deltaData } = useStateDelta(30)
  const { data: snapshots, isLoading: snapshotsLoading } = useSnapshots()

  if (stateLoading || snapshotsLoading) {
    return <LoadingState message="Aggregating 10-dimension Merchant Economic Twin..." />
  }

  if (stateError || !state) {
    return (
      <ErrorState
        title="Failed to load economic state"
        message="Could not retrieve the multi-dimensional economic model from backend."
        onRetry={() => refetch()}
      />
    )
  }

  const dimensions = [
    state.cash,
    state.receivables,
    state.payables,
    state.inventory_value,
    state.aging_inventory,
    state.gross_margin,
    state.demand_trend,
    state.customer_value,
    state.fulfillment_capacity,
    state.cash_runway,
  ]

  const driversList = driversData?.drivers || state.top_drivers || []

  // Dynamic state badge styling
  const stateColor =
    state.state === 'Strong'
      ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
      : state.state === 'Healthy'
      ? 'text-sky-700 bg-sky-50 border-sky-200'
      : state.state === 'Watch'
      ? 'text-amber-700 bg-amber-50 border-amber-200'
      : state.state === 'Stressed'
      ? 'text-amber-800 bg-amber-100 border-amber-300'
      : 'text-rose-800 bg-rose-100 border-rose-300'

  return (
    <div className="space-y-6">
      {/* 1. ECONOMIC STATE OVERVIEW HERO */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 text-white p-6 shadow-xl relative overflow-hidden">
        {/* Background decorative glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="flex h-2.5 w-2.5 rounded-full bg-sky-400 animate-pulse" />
                <span className="text-[11px] font-bold uppercase tracking-wider font-mono text-sky-400">
                  Merchant Economic Twin • Authoritative Engine
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                {state.merchant_name}
              </h1>
              <p className="text-xs text-slate-400 max-w-2xl">
                Deterministic real-time representation of merchant liquidity, working capital velocity, and structural health across 10 continuous economic dimensions.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => refetch()}
                className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Re-sync
              </button>
            </div>
          </div>

          {/* Core Economic Twin Indicators Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
            {/* Classification State */}
            <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700/80 flex items-center justify-between">
              <div>
                <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                  Business State
                </div>
                <div className="text-xl font-bold text-white font-mono mt-0.5">
                  {state.state.toUpperCase()}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {state.liquidity_status} equilibrium
                </div>
              </div>
              <div className={`px-2.5 py-1 rounded text-xs font-bold font-mono border ${stateColor}`}>
                {state.state}
              </div>
            </div>

            {/* Pressure Score */}
            <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700/80 flex items-center justify-between">
              <div>
                <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                  Economic Pressure Score
                </div>
                <div className="text-xl font-bold font-mono mt-0.5 text-amber-400">
                  {state.pressure_score}
                  <span className="text-xs text-slate-400 font-normal">/100</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Composite deterministic stress
                </div>
              </div>
              <div className="p-2 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
            </div>

            {/* Cash Runway */}
            <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700/80 flex items-center justify-between">
              <div>
                <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                  Cash Runway
                </div>
                <div className="text-xl font-bold font-mono mt-0.5 text-sky-400">
                  {state.cash_runway.formatted_value}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Net burn sustainable window
                </div>
              </div>
              <div className="p-2 rounded bg-sky-500/10 border border-sky-500/30 text-sky-400">
                <Flame className="w-5 h-5" />
              </div>
            </div>

            {/* Net Working Capital */}
            <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700/80 flex items-center justify-between">
              <div>
                <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                  Net Working Capital
                </div>
                <div className="text-xl font-bold font-mono mt-0.5 text-emerald-400">
                  {state.working_capital_formatted}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Current Ratio: {state.current_ratio}x
                </div>
              </div>
              <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Dynamic Insight Banner */}
          <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700 text-xs text-slate-300 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white mr-1.5">
                {state.liquidity_outlook_headline}:
              </span>
              <span>{state.liquidity_outlook_summary}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs for Analytical Clarity */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'overview'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Layers className="w-3.5 h-3.5" /> 10 Economic Dimensions
        </button>

        <button
          onClick={() => setActiveTab('drivers')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'drivers'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" /> Pressure Drivers ({driversList.length})
        </button>

        <button
          onClick={() => setActiveTab('timeline')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'timeline'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Activity className="w-3.5 h-3.5" /> Health Timeline &amp; CCC
        </button>

        <button
          onClick={() => setActiveTab('delta')}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'delta'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" /> State Delta (30-Day Shift)
        </button>
      </div>

      {/* TAB 1: 10 ECONOMIC DIMENSIONS SCORECARD GRID */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                10-Dimension Core Economic State
              </h3>
              <span className="text-xs text-slate-400">
                Authoritative calculations from transactional ledgers
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
              {dimensions.map((dim) => (
                <StatCard
                  key={dim.dimension}
                  title={dim.name}
                  value={dim.formatted_value}
                  subtitle={dim.label}
                  status={dim.status}
                  trend={dim.trend}
                  trendPct={dim.trend_pct}
                  benchmark={dim.benchmark}
                  compact
                />
              ))}
            </div>
          </section>

          {/* Economic Balance & Key Financial Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8">
              <Card>
                <CardHeader className="border-b border-slate-100 pb-3">
                  <div>
                    <CardTitle>Economic Position &amp; Working Capital Conversion</CardTitle>
                    <CardDescription>
                      Balance distribution across liquidity, credit commitments, and asset turns
                    </CardDescription>
                  </div>
                  <Badge variant="brand" size="sm">
                    CCC: {state.cash_conversion_cycle} Days
                  </Badge>
                </CardHeader>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200/80 mb-4">
                  <div className="p-2">
                    <div className="text-[11px] text-slate-500 font-medium">Current Ratio</div>
                    <div className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                      {state.current_ratio}x
                    </div>
                    <div className="text-[10px] text-slate-400">Target &gt; 2.0x</div>
                  </div>

                  <div className="p-2">
                    <div className="text-[11px] text-slate-500 font-medium">Quick Ratio</div>
                    <div className="text-lg font-bold text-slate-900 font-mono mt-0.5">
                      {state.quick_ratio}x
                    </div>
                    <div className="text-[10px] text-slate-400">Target &gt; 1.0x</div>
                  </div>

                  <div className="p-2">
                    <div className="text-[11px] text-slate-500 font-medium">DSO (Receivables)</div>
                    <div className="text-lg font-bold text-amber-700 font-mono mt-0.5">
                      {formatDays(state.dso_days)}
                    </div>
                    <div className="text-[10px] text-slate-400">Standard 30d</div>
                  </div>

                  <div className="p-2">
                    <div className="text-[11px] text-slate-500 font-medium">DIO (Inventory)</div>
                    <div className="text-lg font-bold text-slate-800 font-mono mt-0.5">
                      {formatDays(state.dio_days)}
                    </div>
                    <div className="text-[10px] text-slate-400">Turnover cycle</div>
                  </div>

                  <div className="p-2">
                    <div className="text-[11px] text-slate-500 font-medium">DPO (Payables)</div>
                    <div className="text-lg font-bold text-slate-800 font-mono mt-0.5">
                      {formatDays(state.dpo_days)}
                    </div>
                    <div className="text-[10px] text-slate-400">Vendor terms</div>
                  </div>

                  <div className="p-2">
                    <div className="text-[11px] text-slate-500 font-medium">Cash Cycle (CCC)</div>
                    <div className="text-lg font-bold text-indigo-700 font-mono mt-0.5">
                      {formatDays(state.cash_conversion_cycle)}
                    </div>
                    <div className="text-[10px] text-slate-400">DIO + DSO - DPO</div>
                  </div>
                </div>

                {/* Quick Timeline Preview */}
                <div className="pt-2">
                  <div className="text-xs font-semibold text-slate-700 mb-2">
                    Economic Twin Memory (30-Day Multi-Series Trajectory)
                  </div>
                  <EconomicHealthTimelineChart data={snapshots?.data || []} height={260} />
                </div>
              </Card>
            </div>

            {/* Right Column: Top Pressure Drivers Summary */}
            <div className="lg:col-span-4 space-y-4">
              <Card className="border-amber-200 bg-amber-50/20">
                <CardHeader className="border-b border-amber-100 pb-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <div>
                      <CardTitle className="text-amber-950">Top Pressure Drivers</CardTitle>
                      <CardDescription className="text-amber-800">
                        Ranked by computed contribution
                      </CardDescription>
                    </div>
                  </div>
                  <button
                    onClick={() => setActiveTab('drivers')}
                    className="text-xs font-semibold text-amber-900 hover:text-amber-950 inline-flex items-center gap-1"
                  >
                    All <ArrowRight className="w-3 h-3" />
                  </button>
                </CardHeader>

                <div className="mt-3 space-y-2.5">
                  {driversList.slice(0, 3).map((driver) => (
                    <div
                      key={driver.id}
                      className="p-3 bg-white rounded-md border border-slate-200 text-xs shadow-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-slate-900 line-clamp-1">
                          #{driver.rank || 1} {driver.title}
                        </span>
                        <Badge variant={driver.severity} size="sm">
                          {driver.severity}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-slate-600 leading-snug">
                        {driver.description}
                      </p>
                      <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-100">
                        <span>Category: {driver.category}</span>
                        {driver.contribution_score && (
                          <span className="font-mono font-medium text-amber-700">
                            Weight: +{driver.contribution_score} pts
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: RANKED PRESSURE DRIVERS IN-DEPTH */}
      {activeTab === 'drivers' && (
        <Card>
          <CardHeader className="border-b border-slate-100 pb-3">
            <div>
              <CardTitle>Deterministic Economic Pressure Drivers</CardTitle>
              <CardDescription>
                Systematic ranking of financial and operational factors elevating merchant stress from baseline
              </CardDescription>
            </div>
            <Badge variant={state.liquidity_status} size="sm">
              Score: {state.pressure_score}/100 • {state.state}
            </Badge>
          </CardHeader>

          <div className="p-4 space-y-3">
            {driversList.map((driver) => (
              <div
                key={driver.id}
                className="p-4 rounded-lg border border-slate-200 bg-white hover:border-slate-300 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2.5">
                    <span className="h-6 w-6 rounded-full bg-slate-100 border border-slate-300 text-slate-700 font-mono font-bold text-xs flex items-center justify-center shrink-0">
                      {driver.rank || '#'}
                    </span>
                    <h4 className="font-semibold text-slate-900 text-sm">{driver.title}</h4>
                    <Badge variant={driver.severity} size="sm">
                      {driver.severity}
                    </Badge>
                    <Badge variant="outline" size="sm">
                      {driver.category}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 pl-8 leading-relaxed">
                    {driver.description}
                  </p>
                </div>

                <div className="md:text-right pl-8 md:pl-0 shrink-0 space-y-0.5">
                  {driver.impact_amount && (
                    <div className="font-mono font-bold text-slate-900 text-sm">
                      {driver.impact_formatted}
                    </div>
                  )}
                  {driver.contribution_score && (
                    <div className="text-[11px] font-mono text-amber-700 font-semibold">
                      +{driver.contribution_score} pressure points
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 3: TIMELINE & CASH CONVERSION CYCLE */}
      {activeTab === 'timeline' && (
        <Card>
          <CardHeader className="border-b border-slate-100 pb-3">
            <div>
              <CardTitle>Economic Health Timeline &amp; State Memory</CardTitle>
              <CardDescription>
                Chronological trajectory of liquid cash, receivables ledger, inventory capital, and stress index
              </CardDescription>
            </div>
            <div className="text-xs text-slate-400">
              {snapshots?.total_points || 30} Historical Data Points
            </div>
          </CardHeader>

          <div className="p-4 space-y-6">
            <EconomicHealthTimelineChart data={snapshots?.data || []} height={340} />

            {/* Daily Snapshots Log Table */}
            <div className="border-t border-slate-200 pt-4">
              <div className="text-xs font-semibold text-slate-800 mb-2">
                Recent Daily Economic Snapshots
              </div>
              <div className="overflow-x-auto rounded border border-slate-200">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-600 uppercase text-[11px] border-b border-slate-200">
                      <th className="py-2.5 px-3 font-semibold">Date</th>
                      <th className="py-2.5 px-3 font-semibold">Cash Balance</th>
                      <th className="py-2.5 px-3 font-semibold">Receivables</th>
                      <th className="py-2.5 px-3 font-semibold">Payables</th>
                      <th className="py-2.5 px-3 font-semibold">Working Capital</th>
                      <th className="py-2.5 px-3 font-semibold">Runway</th>
                      <th className="py-2.5 px-3 font-semibold">Stress Index</th>
                      <th className="py-2.5 px-3 font-semibold">Event</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {snapshots?.recent_snapshots?.slice(0, 8).map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-medium text-slate-900 whitespace-nowrap">
                          {s.snapshot_date.substring(0, 10)}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-sky-700 font-medium">
                          {s.cash_balance_formatted}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-emerald-700">
                          {s.receivables_formatted}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-rose-700">
                          {s.payables_formatted}
                        </td>
                        <td className="py-2.5 px-3 font-mono font-semibold text-slate-900">
                          {s.working_capital_formatted}
                        </td>
                        <td className="py-2.5 px-3 font-mono">{s.cash_runway_days}d</td>
                        <td className="py-2.5 px-3 font-mono font-semibold">
                          <span
                            className={
                              s.liquidity_stress_score > 65
                                ? 'text-rose-600'
                                : s.liquidity_stress_score > 45
                                ? 'text-amber-600'
                                : 'text-emerald-600'
                            }
                          >
                            {s.liquidity_stress_score}/100
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 max-w-xs truncate">
                          {s.event_marker || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* TAB 4: STATE DELTA & TRANSITION COMPARISON */}
      {activeTab === 'delta' && (
        <Card>
          <CardHeader className="border-b border-slate-100 pb-3">
            <div>
              <CardTitle>State Transition Comparison: State(t) → State(t+Δ)</CardTitle>
              <CardDescription>
                Deterministic comparison of the merchant's financial trajectory against 30-day baseline
              </CardDescription>
            </div>
            {deltaData && (
              <Badge variant="outline" size="sm">
                Score Shift: {deltaData.baseline_pressure_score} → {deltaData.current_pressure_score} pts
              </Badge>
            )}
          </CardHeader>

          <div className="p-4 space-y-4">
            {deltaData && (
              <>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed">
                  <span className="font-bold text-slate-900">Transition Summary: </span>
                  {deltaData.summary}
                </div>

                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 uppercase text-[11px] border-b border-slate-200">
                        <th className="py-2.5 px-4 font-semibold">Dimension</th>
                        <th className="py-2.5 px-4 font-semibold">Baseline (30d Ago)</th>
                        <th className="py-2.5 px-4 font-semibold">Current State</th>
                        <th className="py-2.5 px-4 font-semibold text-right">Absolute Change</th>
                        <th className="py-2.5 px-4 font-semibold text-right">% Change</th>
                        <th className="py-2.5 px-4 font-semibold text-center">Direction</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {deltaData.deltas.map((delta) => (
                        <tr key={delta.metric} className="hover:bg-slate-50">
                          <td className="py-3 px-4 font-semibold text-slate-900">
                            {delta.label}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-600">
                            {delta.formatted_before}
                          </td>
                          <td className="py-3 px-4 font-mono font-medium text-slate-900">
                            {delta.formatted_after}
                          </td>
                          <td className="py-3 px-4 font-mono text-right font-semibold">
                            <span
                              className={
                                delta.direction === 'Positive'
                                  ? 'text-emerald-700'
                                  : delta.direction === 'Negative'
                                  ? 'text-rose-700'
                                  : 'text-slate-600'
                              }
                            >
                              {delta.formatted_change}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-mono text-right text-slate-600">
                            {delta.percentage_change > 0 ? `+${delta.percentage_change}%` : `${delta.percentage_change}%`}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                                delta.direction === 'Positive'
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : delta.direction === 'Negative'
                                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {delta.direction}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
