import React, { useState, useMemo } from 'react'
import {
  Boxes,
  Clock,
  AlertTriangle,
  Search,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
  Minus,
  Package,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/common/Card'
import { StatCard } from '@/components/common/StatCard'
import { Badge } from '@/components/common/Badge'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/common/Table'
import { LoadingState } from '@/components/common/LoadingState'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { InventoryAgingChart } from '@/components/charts/InventoryAgingChart'
import { useInventory } from '@/hooks/useInventory'
import { formatINR, formatNumber } from '@/utils/formatters'
import type { InventoryItem } from '@/types'

export const InventoryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')
  const [sortField, setSortField] = useState<keyof InventoryItem>('inventory_value')
  const [sortAsc, setSortAsc] = useState<boolean>(false)

  const { data, isLoading, error, refetch } = useInventory({
    status: statusFilter !== 'ALL' ? statusFilter : undefined,
    category: categoryFilter !== 'ALL' ? categoryFilter : undefined,
    search: searchTerm || undefined,
  })

  // Extract unique categories from summary
  const categories = data?.summary?.category_breakdown?.map((c) => c.category) || []

  // Client-side sorting for rapid UI interaction
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

  const handleSort = (field: keyof InventoryItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  if (isLoading) {
    return <LoadingState message="Loading merchant inventory catalogue & aging distribution..." />
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Failed to load inventory"
        message="Could not retrieve inventory items. Please check API server."
        onRetry={() => refetch()}
      />
    )
  }

  const { summary } = data

  return (
    <div className="space-y-6">
      {/* Dynamic Summary Alert Strip */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 shrink-0">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-amber-400 uppercase tracking-wider">
              Aging Inventory Pressure Detected
            </div>
            <p className="text-sm font-semibold text-white mt-0.5">
              {summary.total_aging_value_formatted} of inventory is currently older than 45 days ({summary.aging_pct}% of total stock valuation).
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Capital is predominantly tied up in Actuators &amp; High-Value Valves awaiting counterfactual liquidation or bundle opportunities.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Badge variant={summary.aging_pct > 20 ? 'Warning' : 'Watch'} size="md">
            {summary.aging_pct}% Aging Concentration
          </Badge>
        </div>
      </div>

      {/* Summary Strip (4 Cards) */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          title="Total SKUs"
          value={summary.total_skus}
          subtitle={`${formatNumber(summary.total_units)} total units in stock`}
          status="Healthy"
          icon={<Boxes className="w-4 h-4" />}
        />
        <StatCard
          title="Inventory Value"
          value={summary.total_inventory_value_formatted}
          subtitle="At weighted unit cost"
          status="Healthy"
          icon={<Package className="w-4 h-4" />}
        />
        <StatCard
          title="Aging Inventory"
          value={summary.total_aging_value_formatted}
          subtitle={`${summary.aging_pct}% aged over 45 days`}
          status={summary.aging_pct > 20 ? 'Warning' : 'Watch'}
          icon={<Clock className="w-4 h-4" />}
        />
        <StatCard
          title="Low Stock Items"
          value={summary.low_stock_count}
          subtitle={summary.low_stock_count > 0 ? 'Below min buffer threshold' : 'All thresholds met'}
          status={summary.low_stock_count > 0 ? 'Watch' : 'Healthy'}
          icon={<AlertTriangle className="w-4 h-4" />}
        />
      </section>

      {/* Category Breakdown Chart Card */}
      <Card>
        <CardHeader className="border-b border-slate-100 pb-3">
          <div>
            <CardTitle>Inventory Valuation &amp; Aging by Category</CardTitle>
            <CardDescription>
              Valuation distribution across product lines highlighting capital locked in slow-moving items
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <span className="h-2.5 w-2.5 rounded-sm bg-[#0284c7]" /> Healthy
            </span>
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <span className="h-2.5 w-2.5 rounded-sm bg-[#f59e0b]" /> Aging (&gt;45d)
            </span>
          </div>
        </CardHeader>
        <InventoryAgingChart categories={summary.category_breakdown} height={220} />
      </Card>

      {/* Inventory Table Container */}
      <Card padding="none">
        {/* Table Filters & Search Bar */}
        <div className="p-4 border-b border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-50/50">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search product name, SKU, or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-md border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Status Filter */}
            <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-md p-1">
              <span className="text-[11px] font-semibold text-slate-400 px-1.5">Status:</span>
              {['ALL', 'Healthy', 'Watch', 'Aging', 'Critical'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-brand-600 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            {/* Category Dropdown */}
            {categories.length > 0 && (
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                aria-label="Filter inventory by product category"
                className="px-2.5 py-1.5 text-xs rounded-md border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="ALL">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Inventory Items Table */}
        {sortedItems.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No inventory items matched"
              description="Try adjusting your search keyword or clearing the status/category filters."
              action={
                <button
                  onClick={() => {
                    setSearchTerm('')
                    setStatusFilter('ALL')
                    setCategoryFilter('ALL')
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
                <TableHead onClick={() => handleSort('product_name')} className="cursor-pointer">
                  <div className="flex items-center gap-1">
                    Product Name <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('product_sku')} className="cursor-pointer">
                  <div className="flex items-center gap-1">
                    SKU <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('available_quantity')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Available <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('unit_cost')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Unit Cost <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('current_price')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Price <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('inventory_value')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Inventory Value <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead onClick={() => handleSort('days_in_stock')} className="cursor-pointer text-right">
                  <div className="flex items-center justify-end gap-1">
                    Days in Stock <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </TableHead>
                <TableHead>Demand Trend</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div>
                      <div className="font-semibold text-slate-900">{item.product_name}</div>
                      <div className="text-[11px] text-slate-400">{item.product_category} • {item.location}</div>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-slate-600">{item.product_sku}</TableCell>
                  <TableCell className="text-right font-medium">
                    <span className={item.available_quantity <= item.min_stock_threshold ? 'text-rose-600 font-bold' : 'text-slate-900'}>
                      {item.available_quantity} {item.unit}
                    </span>
                    {item.reserved_quantity > 0 && (
                      <div className="text-[10px] text-slate-400">({item.reserved_quantity} rsvd)</div>
                    )}
                  </TableCell>
                  <TableCell className="text-right text-slate-600">
                    {formatINR(item.unit_cost, { compact: false })}
                  </TableCell>
                  <TableCell className="text-right font-medium text-slate-800">
                    {formatINR(item.current_price, { compact: false })}
                  </TableCell>
                  <TableCell className="text-right font-bold text-slate-900">
                    {item.inventory_value_formatted}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={`font-mono font-medium ${
                        item.days_in_stock > 60
                          ? 'text-rose-600'
                          : item.days_in_stock > 45
                          ? 'text-amber-600'
                          : 'text-slate-700'
                      }`}
                    >
                      {item.days_in_stock}d
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-[11px]">
                      {item.demand_trend === 'Increasing' && (
                        <span className="text-emerald-600 flex items-center gap-0.5 font-medium">
                          <TrendingUp className="w-3 h-3" /> Increasing
                        </span>
                      )}
                      {item.demand_trend === 'Stable' && (
                        <span className="text-slate-500 flex items-center gap-0.5">
                          <Minus className="w-3 h-3" /> Stable
                        </span>
                      )}
                      {item.demand_trend === 'Softening' && (
                        <span className="text-amber-600 flex items-center gap-0.5 font-medium">
                          <TrendingDown className="w-3 h-3" /> Softening
                        </span>
                      )}
                      {item.demand_trend === 'Declining' && (
                        <span className="text-rose-600 flex items-center gap-0.5 font-medium">
                          <TrendingDown className="w-3 h-3" /> Declining
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={item.status} size="sm" dot>
                      {item.status}
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
