import React from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot,
} from 'recharts'
import { formatINR } from '@/utils/formatters'
import type { SnapshotTrendPoint } from '@/types'

interface CashflowTimelineChartProps {
  data: SnapshotTrendPoint[]
  height?: number
}

export const CashflowTimelineChart: React.FC<CashflowTimelineChartProps> = ({
  data,
  height = 280,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-400">
        No snapshot data available
      </div>
    )
  }

  // Format data for chart display
  const chartData = data.map((d) => {
    const parts = d.date.split('-')
    const shortDate = `${parts[2]}/${parts[1]}`
    return {
      ...d,
      shortDate,
      displayCash: d.cash_balance,
    }
  })

  // Find points with event markers
  const eventPoints = chartData.filter((d) => Boolean(d.event_marker))

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="cashGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0284c7" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0} />
            </linearGradient>
          </defs>
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
            domain={['dataMin - 50000', 'dataMax + 50000']}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload as typeof chartData[0]
                return (
                  <div className="bg-slate-900 text-white text-xs p-3 rounded-lg shadow-xl border border-slate-800 space-y-1.5 min-w-[200px]">
                    <div className="text-slate-400 font-mono text-[11px] flex justify-between">
                      <span>{item.date}</span>
                      <span className="text-amber-400">{item.cash_runway_days}d Runway</span>
                    </div>
                    <div className="flex items-center justify-between font-semibold text-sm">
                      <span>Cash Balance:</span>
                      <span className="text-sky-300 font-mono">
                        {formatINR(item.cash_balance, { compact: false })}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300 flex justify-between">
                      <span>Working Capital:</span>
                      <span>{formatINR(item.working_capital, { compact: true })}</span>
                    </div>
                    {item.event_marker && (
                      <div className="pt-1.5 border-t border-slate-800 text-[11px] text-amber-300 flex items-start gap-1">
                        <span className="shrink-0">•</span>
                        <span>{item.event_marker}</span>
                      </div>
                    )}
                  </div>
                )
              }
              return null
            }}
          />
          <Area
            type="monotone"
            dataKey="displayCash"
            stroke="#0284c7"
            strokeWidth={2.2}
            fillOpacity={1}
            fill="url(#cashGradient)"
          />
          {eventPoints.map((ep, idx) => (
            <ReferenceDot
              key={idx}
              x={ep.shortDate}
              y={ep.displayCash}
              r={4}
              fill="#d97706"
              stroke="#ffffff"
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
