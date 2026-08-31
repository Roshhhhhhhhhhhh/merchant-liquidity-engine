import React from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts'
import { formatINR } from '@/utils/formatters'
import type { AgingBucket } from '@/types'

interface ReceivablesAgingChartProps {
  buckets: AgingBucket[]
  height?: number
}

export const ReceivablesAgingChart: React.FC<ReceivablesAgingChartProps> = ({
  buckets,
  height = 200,
}) => {
  if (!buckets || buckets.length === 0) {
    return (
      <div className="h-44 flex items-center justify-center text-xs text-slate-400">
        No aging bucket data available
      </div>
    )
  }

  const getBucketColor = (bucket: string) => {
    if (bucket.includes('0-15')) return '#10b981' // emerald
    if (bucket.includes('16-30')) return '#38bdf8' // sky
    if (bucket.includes('31-60')) return '#f59e0b' // amber
    return '#f43f5e' // rose (60+)
  }

  const chartData = buckets.map((b) => ({
    name: b.bucket,
    amount: Number(b.amount),
    count: b.count,
    percentage: Number(b.percentage),
    color: getBucketColor(b.bucket),
  }))

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="name"
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
                  <div className="bg-slate-900 text-white text-xs p-3 rounded-lg shadow-xl border border-slate-800 space-y-1 min-w-[170px]">
                    <div className="font-semibold text-slate-200">{item.name}</div>
                    <div className="flex justify-between text-slate-300">
                      <span>Invoices:</span>
                      <span>{item.count} Invoices</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Share of Book:</span>
                      <span className="font-mono">{item.percentage}%</span>
                    </div>
                    <div className="flex justify-between font-semibold pt-1 border-t border-slate-800 text-amber-300">
                      <span>Balance Due:</span>
                      <span className="font-mono">{formatINR(item.amount)}</span>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
