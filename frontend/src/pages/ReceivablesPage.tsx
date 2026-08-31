import React, { useState, useMemo } from 'react'
import {
  Receipt,
  Clock,
  AlertCircle,
  Calendar,
  Search,
  ArrowUpDown,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/common/Card'
import { StatCard } from '@/components/common/StatCard'
import { Badge } from '@/components/common/Badge'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/common/Table'
import { LoadingState } from '@/components/common/LoadingState'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { ReceivablesAgingChart } from '@/components/charts/ReceivablesAgingChart'
import { useReceivables, useCustomers } from '@/hooks/useReceivables'
import { formatDate, formatDays, formatINR } from '@/utils/formatters'
import type { ReceivableItem } from '@/types'

export const ReceivablesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [sortField, setSortField] = useState<keyof ReceivableItem>('balance_due')
  const [sortAsc, setSortAsc] = useState<boolean>(false)
  const [showCustomersTab, setShowCustomersTab] = useState<boolean>(false)

  const { data, isLoading, error, refetch } = useReceivables({
    status: statusFilter !== 'ALL' ? statusFilter : undefined,
    search: searchTerm || undefined,
  })

  const { data: customerData, isLoading: custLoading } = useCustomers()

  const sortedItems = useMemo(() => {
    if (!data?.items) return []
    return [...data.items].sort((a, b) => {
      let aVal = a[sortField] ?? ''
      let bVal = b[sortField] ?? ''

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase()
        bVal = (bVal as string).toLowerCase()
      }

      if (aVal < bVal) return sortAsc ? -1 : 1
      if (aVal > bVal) return sortAsc ? 1 : -1
      return 0
    })
  }, [data?.items, sortField, sortAsc])

  const handleSort = (field: keyof ReceivableItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  if (isLoading || custLoading) {
    return <LoadingState message="Loading accounts receivable ledger & aging buckets..." />
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Failed to load receivables"
        message="Could not retrieve the receivables ledger."
        onRetry={() => refetch()}
      />
    )
  }

  const { summary } = data
  const overdueRatioPct =
    summary.total_outstanding > 0
      ? ((summary.total_overdue / summary.total_outstanding) * 100).toFixed(1)
      : '0.0'

  return (
    <div className="space-y-6">
      {/* Dynamic Summary Alert Strip */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 shrink-0">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-rose-400 uppercase tracking-wider">
              Receivables Concentration &amp; Overdue Risk
            </div>
            <p className="text-sm font-semibold text-white mt-0.5">
              {summary.total_overdue_formatted} is currently overdue ({overdueRatioPct}% of total book), extending weighted DSO to {summary.average_dso_days} days.
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Primary collection delays from Pune Thermal Power ({formatINR(240000)}) and Deccan Refineries ({formatINR(330000)}) are restricting operating cash reserves.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Badge variant="Critical" size="md">
            {overdueRatioPct}% Overdue Ratio
          </Badge>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          title="Total Outstanding"
          value={summary.total_outstanding_formatted}
          subtitle={`${summary.current_count + summary.due_soon_count + summary.overdue_count + summary.severely_overdue_count} total open invoices`}
          status="Watch"
          icon={<Receipt className="w-4 h-4" />}
        />
        <StatCard
          title="Due This Week"
          value={summary.due_this_week_formatted}
          subtitle="Expected settlement inflows"
          status="Healthy"
          icon={<Calendar className="w-4 h-4" />}
        />
        <StatCard
          title="Overdue Dues"
          value={summary.total_overdue_formatted}
          subtitle={`${summary.severely_overdue_formatted} severely overdue (>30d)`}
          status="Critical"
          icon={<AlertCircle className="w-4 h-4" />}
        />
        <StatCard
          title="Average DSO"
          value={formatDays(summary.average_dso_days)}
          subtitle="Weighted collection cycle"
          status={summary.average_dso_days > 40 ? 'Warning' : 'Healthy'}
          icon={<Clock className="w-4 h-4" />}
        />
      </section>

      {/* Aging Histogram Card */}
      <Card>
        <CardHeader className="border-b border-slate-100 pb-3">
          <div>
            <CardTitle>Receivables Aging Distribution</CardTitle>
            <CardDescription>
              Capital exposure categorized by days outstanding from invoice generation date
            </CardDescription>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Total Book:</span>
            <span className="font-bold text-slate-900 font-mono">
              {summary.total_outstanding_formatted}
            </span>
          </div>
        </CardHeader>
        <ReceivablesAgingChart buckets={summary.aging_buckets} height={200} />
      </Card>

      {/* Main Table / Directory Section */}
      <Card padding="none">
        {/* Toggle & Filter Bar */}
        <div className="p-4 border-b border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCustomersTab(false)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                !showCustomersTab
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
              }`}
            >
              Invoices Ledger
            </button>
            <button
              onClick={() => setShowCustomersTab(true)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                showCustomersTab
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
              }`}
            >
              Customer Directory ({customerData?.summary?.total_customers || 8})
            </button>
          </div>

          {!showCustomersTab && (
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search customer or invoice #..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-4 py-1.5 text-xs rounded-md border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-md p-1">
                <span className="text-[11px] font-semibold text-slate-400 px-1.5">Filter:</span>
                {['ALL', 'Current', 'Due Soon', 'Overdue', 'Severely Overdue'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                      statusFilter === st
                        ? 'bg-slate-800 text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {showCustomersTab ? (
          /* Customer Directory View */
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer Company</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead className="text-right">Credit Limit</TableHead>
                <TableHead className="text-right">Credit Terms</TableHead>
                <TableHead className="text-right">Total Revenue</TableHead>
                <TableHead className="text-right">Payment Reliability Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {customerData?.customers?.map((cust) => (
                <TableRow key={cust.id}>
                  <TableCell>
                    <div>
                      <div className="font-semibold text-slate-900">{cust.company_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{cust.gstin || 'GST Unregistered'}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={cust.customer_tier} size="sm">
                      {cust.customer_tier}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-slate-700">{cust.name}</div>
                    <div className="text-[11px] text-slate-400">{cust.email}</div>
                  </TableCell>
                  <TableCell className="text-right font-mono font-medium">
                    {formatINR(cust.credit_limit)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {cust.credit_terms_days} Days
                  </TableCell>
                  <TableCell className="text-right font-mono font-semibold text-slate-900">
                    {formatINR(cust.total_revenue)}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${
                        cust.payment_score >= 85
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : cust.payment_score >= 75
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {cust.payment_score}/100
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : sortedItems.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No receivables found"
              description="No open invoices matched your current query."
              action={
                <button
                  onClick={() => {
                    setSearchTerm('')
                    setStatusFilter('ALL')
                  }}
                  className="px-3 py-1.5 bg-white border border-slate-300 rounded text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Reset Filters
                </button>
              }
            />
          </div>
        ) : (
          /* Invoices Table View */
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead onClick={() => handleSort('customer_company')} className="cursor-pointer">
                  <div className="flex items-center gap-1">
                    Customer <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('invoice_number')} className="cursor-pointer">
                  <div className="flex items-center gap-1">
                    Invoice # <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('balance_due')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Balance Due <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('issue_date')} className="cursor-pointer">
                  <div className="flex items-center gap-1">
                    Issue Date <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('due_date')} className="cursor-pointer">
                  <div className="flex items-center gap-1">
                    Due Date <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('days_outstanding')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Days Outstanding <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Audit / Notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedItems.map((rec) => (
                <TableRow key={rec.id}>
                  <TableCell>
                    <div>
                      <div className="font-semibold text-slate-900">{rec.customer_company}</div>
                      <div className="text-[11px] text-slate-400">{rec.customer_name} • {rec.customer_tier}</div>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono font-medium text-slate-700">{rec.invoice_number}</TableCell>
                  <TableCell className="text-right font-bold text-slate-900 font-mono">
                    {rec.balance_due_formatted}
                  </TableCell>
                  <TableCell className="text-slate-600">{formatDate(rec.issue_date, 'short')}</TableCell>
                  <TableCell>
                    <span
                      className={`font-medium ${
                        rec.status.includes('Overdue') ? 'text-rose-600 font-bold' : 'text-slate-700'
                      }`}
                    >
                      {formatDate(rec.due_date, 'short')}
                    </span>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <span
                      className={
                        rec.days_outstanding > 45
                          ? 'text-rose-600 font-bold'
                          : rec.days_outstanding > 30
                          ? 'text-amber-600 font-medium'
                          : 'text-slate-700'
                      }
                    >
                      {rec.days_outstanding}d
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={rec.status} size="sm" dot>
                      {rec.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-[11px] text-slate-500 max-w-xs truncate" title={rec.notes}>
                    {rec.notes || '-'}
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
