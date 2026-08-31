import React, { useState } from 'react'
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { formatINR } from '@/utils/formatters'
import type { SnapshotTrendPoint, StateHistoryPoint } from '@/types'

interface EconomicHealthTimelineChartProps {
  data: (SnapshotTrendPoint | StateHistoryPoint)[]
  height?: number
}

export const EconomicHealthTimelineChart: React.FC<EconomicHealthTimelineChartProps> = ({
  data,
  height = 340,
}) => {
  const [activeSeries, setActiveSeries] = useState({
    cash: true,
    receivables: true,
    inventory: true,
    pressureScore: true,
  })

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        No economic health timeline data available
      </div>
    )
  }

  const chartData = data.map((d: any) => {
    const parts = d.date.split('-')
    return {
      ...d,
      shortDate: parts.length === 3 ? `${parts[2]}/${parts[1]}` : d.date,
      cash_balance: d.cash_balance ?? d.cash,
      total_receivables: d.total_receivables ?? d.receivables,
      inventory_val: d.inventory_value ?? d.inventory,
      pressure_score: d.liquidity_stress_score ?? d.pressure_score,
    }
  })

  return (
    <div className="w-full space-y-3">
      {/* Series Filter Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-slate-100 pb-2.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
            Twin Memory Series:
          </span>

          <button
            type="button"
            onClick={() => setActiveSeries((s) => ({ ...s, cash: !s.cash }))}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-medium transition-all ${
              activeSeries.cash
                ? 'bg-sky-50 border-sky-300 text-sky-800 shadow-xs'
                : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-sky-500" />
            Cash Position
          </button>

          <button
            type="button"
            onClick={() => setActiveSeries((s) => ({ ...s, receivables: !s.receivables }))}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-medium transition-all ${
              activeSeries.receivables
                ? 'bg-emerald-50 border-emerald-300 text-emerald-800 shadow-xs'
                : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Receivables Book
          </button>

          <button
            type="button"
            onClick={() => setActiveSeries((s) => ({ ...s, inventory: !s.inventory }))}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-medium transition-all ${
              activeSeries.inventory
                ? 'bg-indigo-50 border-indigo-300 text-indigo-800 shadow-xs'
                : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            Inventory Value
          </button>

          <button
            type="button"
            onClick={() => setActiveSeries((s) => ({ ...s, pressureScore: !s.pressureScore }))}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-medium transition-all ${
              activeSeries.pressureScore
                ? 'bg-amber-50 border-amber-300 text-amber-900 font-semibold shadow-xs'
                : 'bg-slate-50 border-slate-200 text-slate-400'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            Pressure Score (0–100)
          </button>
        </div>

        <div className="text-[11px] text-slate-400 hidden sm:block">
          Dual Axis: INR Volume (Left) • Pressure Index (Right)
        </div>
      </div>

      {/* Composed Chart */}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 12, right: 12, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="shortDate"
              tick={{ fontSize: 11, fill: '#64748b' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
            />
            {/* Left YAxis for Monetary Balances */}
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => formatINR(val, { compact: true })}
            />
            {/* Right YAxis for Pressure Score (0-100) */}
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: '#d97706' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => `${val}`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload
                  return (
                    <div className="bg-slate-950 text-white text-xs p-3.5 rounded-lg shadow-2xl border border-slate-800 space-y-2 min-w-[240px]">
                      <div className="flex items-center justify-between pb-1.5 border-b border-slate-800">
                        <span className="font-mono text-slate-400 text-[11px]">{item.date}</span>
                        <span className="font-mono font-bold text-amber-400 text-[11px]">
                          Pressure: {item.pressure_score}/100
                        </span>
                      </div>

                      {activeSeries.cash && (
                        <div className="flex justify-between text-sky-300">
                          <span className="flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" /> Cash:
                          </span>
                          <span className="font-mono font-semibold">{formatINR(item.cash_balance)}</span>
                        </div>
                      )}

                      {activeSeries.receivables && (
                        <div className="flex justify-between text-emerald-300">
                          <span className="flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Receivables:
                          </span>
                          <span className="font-mono font-semibold">{formatINR(item.total_receivables)}</span>
                        </div>
                      )}

                      {activeSeries.inventory && (
                        <div className="flex justify-between text-indigo-300">
                          <span className="flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" /> Inventory:
                          </span>
                          <span className="font-mono font-semibold">{formatINR(item.inventory_val)}</span>
                        </div>
                      )}

                      {item.event_marker && (
                        <div className="pt-1.5 border-t border-slate-800 text-[11px] text-slate-300">
                          <span className="text-amber-400 font-semibold">Event:</span> {item.event_marker}
                        </div>
                      )}
                    </div>
                  )
                }
                return null
              }}
            />

            {/* Inventory Area/Bar */}
            {activeSeries.inventory && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="inventory_val"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
                name="Inventory Value"
              />
            )}

            {/* Receivables Line */}
            {activeSeries.receivables && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="total_receivables"
                stroke="#10b981"
                strokeWidth={2.2}
                dot={false}
                name="Receivables Book"
              />
            )}

            {/* Cash Position Line */}
            {activeSeries.cash && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="cash_balance"
                stroke="#0284c7"
                strokeWidth={2.5}
                dot={false}
                name="Cash Balance"
              />
            )}

            {/* Pressure Score Line (Secondary Axis) */}
            {activeSeries.pressureScore && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="pressure_score"
                stroke="#f59e0b"
                strokeWidth={2.5}
                strokeDasharray="3 3"
                dot={{ r: 2.5, fill: '#f59e0b', strokeWidth: 0 }}
                name="Pressure Score"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
