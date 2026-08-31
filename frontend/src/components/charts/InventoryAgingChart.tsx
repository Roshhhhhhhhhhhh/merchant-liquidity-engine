import React from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { formatINR } from '@/utils/formatters'
import type { CategoryBreakdown } from '@/types'

interface InventoryAgingChartProps {
  categories: CategoryBreakdown[]
  height?: number
}

export const InventoryAgingChart: React.FC<InventoryAgingChartProps> = ({
  categories,
  height = 240,
}) => {
  if (!categories || categories.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-slate-400">
        No category breakdown data available
      </div>
    )
  }

  const chartData = categories.map((c) => ({
    name: c.category,
    healthyValue: Number(c.total_value) - Number(c.aging_value),
    agingValue: Number(c.aging_value),
    totalValue: Number(c.total_value),
    itemCount: c.item_count,
  }))

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: '#64748b' }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={false}
            interval={0}
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
                  <div className="bg-slate-900 text-white text-xs p-3 rounded-lg shadow-xl border border-slate-800 space-y-1 min-w-[180px]">
                    <div className="font-semibold text-slate-200">{item.name}</div>
                    <div className="text-[11px] text-slate-400">{item.itemCount} Active SKUs</div>
                    <div className="pt-1 border-t border-slate-800 space-y-1">
                      <div className="flex justify-between text-emerald-400">
                        <span>Healthy Stock:</span>
                        <span className="font-mono">{formatINR(item.healthyValue)}</span>
                      </div>
                      <div className="flex justify-between text-amber-400">
                        <span>Aging Stock (&gt;45d):</span>
                        <span className="font-mono">{formatINR(item.agingValue)}</span>
                      </div>
                      <div className="flex justify-between text-white font-semibold pt-1 border-t border-slate-800">
                        <span>Total:</span>
                        <span className="font-mono">{formatINR(item.totalValue)}</span>
                      </div>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <Bar dataKey="healthyValue" stackId="a" fill="#0284c7" radius={[0, 0, 0, 0]} name="Healthy" />
          <Bar dataKey="agingValue" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Aging" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
