import React, { useState } from 'react'
import {
  ArrowLeftRight,
  CheckCircle2,
  Clock,
  Search,
  CreditCard,
  Percent,
} from 'lucide-react'
import { Card } from '@/components/common/Card'
import { StatCard } from '@/components/common/StatCard'
import { Badge } from '@/components/common/Badge'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/common/Table'
import { LoadingState } from '@/components/common/LoadingState'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { useTransactions } from '@/hooks/useTransactions'
import { formatDate } from '@/utils/formatters'

export const TransactionsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [settlementFilter, setSettlementFilter] = useState<string>('ALL')

  const { data, isLoading, error, refetch } = useTransactions({
    settlement_status: settlementFilter !== 'ALL' ? settlementFilter : undefined,
    search: searchTerm || undefined,
  })

  if (isLoading) {
    return <LoadingState message="Loading transactions ledger & settlement pipelines..." />
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Failed to load transactions"
        message="Could not retrieve transactions record."
        onRetry={() => refetch()}
      />
    )
  }

  const { summary, items } = data

  return (
    <div className="space-y-6">
      {/* Razorpay Integration Active Execution Banner */}
      <Card className="bg-gradient-to-r from-slate-950 via-slate-900 to-emerald-950 text-white border-emerald-500/30 p-4 shadow-lg shadow-emerald-950/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/40 shrink-0">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-white uppercase tracking-tight flex items-center gap-2">
                <span>Razorpay Test Mode Active • End-to-End Execution Engine</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Phase 5 Verified
                </span>
              </div>
              <p className="text-[11px] text-slate-300 mt-0.5">
                Every agentic commercial agreement is executed via cryptographic Razorpay test order creation, HMAC signature verification, and real-time Economic Twin realization.
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 bg-emerald-950/80 text-emerald-300 rounded border border-emerald-500/30 text-[11px] font-mono shrink-0">
            Gateway: Razorpay Test Sandbox
          </span>
        </div>
      </Card>

      {/* Summary KPI Strip */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          title="Total Gross Volume"
          value={summary.total_gross_volume_formatted}
          subtitle={`${summary.total_transactions} orders fulfilled (30d)`}
          status="Healthy"
          icon={<ArrowLeftRight className="w-4 h-4" />}
        />
        <StatCard
          title="Settled In Bank"
          value={summary.settled_volume_formatted}
          subtitle="Funds cleared to primary account"
          status="Healthy"
          icon={<CheckCircle2 className="w-4 h-4" />}
        />
        <StatCard
          title="In Transit / Clearing"
          value={summary.in_transit_volume_formatted}
          subtitle="T+1 / T+2 settlement window"
          status="Watch"
          icon={<Clock className="w-4 h-4" />}
        />
        <StatCard
          title="Average Realized Margin"
          value={`${summary.avg_gross_margin_pct}%`}
          subtitle={`Avg order: ${summary.avg_order_value_formatted}`}
          status="Healthy"
          icon={<Percent className="w-4 h-4" />}
        />
      </section>

      {/* Transactions Table Container */}
      <Card padding="none">
        {/* Filter Bar */}
        <div className="p-4 border-b border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-50/50">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search reference #, client company, or product SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-md border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-md p-1 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 px-1.5">Settlement:</span>
            {['ALL', 'Settled', 'In Transit', 'Pending'].map((st) => (
              <button
                key={st}
                onClick={() => setSettlementFilter(st)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  settlementFilter === st
                    ? 'bg-brand-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {items.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No transactions found"
              description="No transaction records matched your filter criteria."
              action={
                <button
                  onClick={() => {
                    setSearchTerm('')
                    setSettlementFilter('ALL')
                  }}
                  className="px-3 py-1.5 bg-white border border-slate-300 rounded text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Reset Filters
                </button>
              }
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date / Time</TableHead>
                <TableHead>Transaction Ref</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Product Ordered</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Gross Value</TableHead>
                <TableHead className="text-right">Net Margin</TableHead>
                <TableHead>Payment Status</TableHead>
                <TableHead>Settlement Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((tx) => (
                <TableRow key={tx.id} className={tx.source === 'agentic_negotiation' ? 'bg-emerald-50/30' : ''}>
                  <TableCell className="text-slate-600 whitespace-nowrap">
                    <div>{formatDate(tx.created_at, 'short')}</div>
                    {tx.paid_at && (
                      <div className="text-[10px] text-emerald-600 font-medium">
                        Paid: {new Date(tx.paid_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="font-mono font-medium text-slate-800 flex items-center gap-1.5">
                      <span>{tx.reference_id}</span>
                      {tx.source === 'agentic_negotiation' && (
                        <span className="px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
                          Agentic Deal
                        </span>
                      )}
                    </div>
                    {tx.razorpay_payment_id && (
                      <div className="text-[10px] font-mono text-emerald-600 font-medium mt-0.5">
                        Rzp: {tx.razorpay_payment_id}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-slate-900">{tx.customer_company}</div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-1">
                      <span>{tx.channel}</span>
                      <span>•</span>
                      <span className="text-slate-500 font-medium">{tx.payment_method}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-slate-800">{tx.product_name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{tx.product_sku}</div>
                  </TableCell>
                  <TableCell className="text-right font-mono font-medium">{tx.quantity}</TableCell>
                  <TableCell className="text-right font-mono font-bold text-slate-900">
                    {tx.gross_value_formatted}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <span
                      className={`font-semibold ${
                        tx.net_margin_pct >= 28 ? 'text-emerald-700' : 'text-slate-700'
                      }`}
                    >
                      {tx.net_margin_pct}%
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={tx.payment_status} size="sm" dot>
                      {tx.payment_status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={tx.settlement_status} size="sm">
                      {tx.settlement_status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  )
}
