import React, { useState } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { formatINR } from '@/utils/formatters'
import type { SnapshotTrendPoint } from '@/types'

interface EconomicSnapshotChartProps {
  data: SnapshotTrendPoint[]
  height?: number
}

export const EconomicSnapshotChart: React.FC<EconomicSnapshotChartProps> = ({
  data,
  height = 320,
}) => {
  const [activeMetrics, setActiveMetrics] = useState({
    cash: true,
    receivables: true,
    payables: true,
    workingCapital: true,
  })

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        No economic snapshot data available
      </div>
    )
  }

  const chartData = data.map((d) => {
    const parts = d.date.split('-')
    return {
      ...d,
      shortDate: `${parts[2]}/${parts[1]}`,
    }
  })

  return (
    <div className="w-full space-y-3">
      {/* Metric Toggles */}
      <div className="flex flex-wrap items-center gap-3 text-xs">
        <span className="text-slate-400 text-[11px] font-medium uppercase">Series:</span>
        <button
          onClick={() => setActiveMetrics((m) => ({ ...m, cash: !m.cash }))}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium transition-all ${
            activeMetrics.cash
              ? 'bg-sky-50 border-sky-300 text-sky-800'
              : 'bg-slate-50 border-slate-200 text-slate-400'
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-sky-500" />
          Cash
        </button>

        <button
          onClick={() => setActiveMetrics((m) => ({ ...m, receivables: !m.receivables }))}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium transition-all ${
            activeMetrics.receivables
              ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
              : 'bg-slate-50 border-slate-200 text-slate-400'
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Receivables
        </button>

        <button
          onClick={() => setActiveMetrics((m) => ({ ...m, payables: !m.payables }))}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium transition-all ${
            activeMetrics.payables
              ? 'bg-rose-50 border-rose-300 text-rose-800'
              : 'bg-slate-50 border-slate-200 text-slate-400'
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-rose-500" />
          Payables
        </button>

        <button
          onClick={() => setActiveMetrics((m) => ({ ...m, workingCapital: !m.workingCapital }))}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium transition-all ${
            activeMetrics.workingCapital
              ? 'bg-indigo-50 border-indigo-300 text-indigo-800'
              : 'bg-slate-50 border-slate-200 text-slate-400'
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-indigo-500" />
          Working Capital
        </button>
      </div>

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="shortDate"
              tick={{ fontSize: 11, fill: '#64748b' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => formatINR(val, { compact: true })}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload as typeof chartData[0]
                  return (
                    <div className="bg-slate-900 text-white text-xs p-3 rounded-lg shadow-xl border border-slate-800 space-y-1.5 min-w-[220px]">
                      <div className="text-slate-400 font-mono text-[11px] pb-1 border-b border-slate-800">
                        {item.date}
                      </div>
                      {activeMetrics.cash && (
                        <div className="flex justify-between text-sky-300">
                          <span>Cash:</span>
                          <span className="font-mono">{formatINR(item.cash_balance)}</span>
                        </div>
                      )}
                      {activeMetrics.receivables && (
                        <div className="flex justify-between text-emerald-300">
                          <span>Receivables:</span>
                          <span className="font-mono">{formatINR(item.total_receivables)}</span>
                        </div>
                      )}
                      {activeMetrics.payables && (
                        <div className="flex justify-between text-rose-300">
                          <span>Payables:</span>
                          <span className="font-mono">{formatINR(item.total_payables)}</span>
                        </div>
                      )}
                      {activeMetrics.workingCapital && (
                        <div className="flex justify-between text-indigo-300 font-semibold pt-1 border-t border-slate-800">
                          <span>Working Capital:</span>
                          <span className="font-mono">{formatINR(item.working_capital)}</span>
                        </div>
                      )}
                    </div>
                  )
                }
                return null
              }}
            />
            {activeMetrics.cash && (
              <Line
                type="monotone"
                dataKey="cash_balance"
                stroke="#0284c7"
                strokeWidth={2}
                dot={false}
                name="Cash"
              />
            )}
            {activeMetrics.receivables && (
              <Line
                type="monotone"
                dataKey="total_receivables"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                name="Receivables"
              />
            )}
            {activeMetrics.payables && (
              <Line
                type="monotone"
                dataKey="total_payables"
                stroke="#f43f5e"
                strokeWidth={2}
                dot={false}
                name="Payables"
              />
            )}
            {activeMetrics.workingCapital && (
              <Line
                type="monotone"
                dataKey="working_capital"
                stroke="#6366f1"
                strokeWidth={2.2}
                dot={false}
                strokeDasharray="4 4"
                name="Working Capital"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
