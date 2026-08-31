import React, { useState } from 'react'
import { Bell, Search, Calendar, ChevronDown, CheckCircle2, AlertCircle } from 'lucide-react'
import { Badge } from '@/components/common/Badge'

interface HeaderProps {
  title: string
  subtitle?: string
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  const [showNotifications, setShowNotifications] = useState(false)

  const notifications = [
    {
      id: '1',
      title: 'Receivable Overdue: Pune Thermal Power',
      time: '2 hours ago',
      type: 'warning',
      amount: '₹2.40L',
    },
    {
      id: '2',
      title: 'Upcoming Supplier Due: Mahasagar Steel',
      time: '5 hours ago',
      type: 'info',
      amount: '₹1.85L',
    },
    {
      id: '3',
      title: 'Daily Liquidity Snapshot Computed',
      time: 'Today 00:00',
      type: 'success',
      amount: '24d Runway',
    },
  ]

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Title & Context */}
      <div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-3">
        {/* Date context */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-slate-200 bg-slate-50 text-xs text-slate-600 font-medium">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <span>FY 2026-27 • Q2 Snapshot</span>
        </div>

        {/* Global Search Placeholder */}
        <div className="relative hidden sm:block">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search SKUs, invoices, clients..."
            disabled
            className="w-48 md:w-64 pl-8 pr-3 py-1.5 text-xs rounded-md border border-slate-200 bg-slate-50/70 text-slate-400 placeholder:text-slate-400 cursor-not-allowed select-none"
            title="Global search enabled in Phase 2"
          />
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 relative transition-colors"
            aria-label="View notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-orange-500 ring-2 ring-white" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-fintech-hover py-2 z-30 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-2 border-b border-slate-100 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900">Economic Alerts</span>
                <Badge variant="warning" size="sm">
                  3 New
                </Badge>
              </div>
              <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="p-3 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start gap-2">
                      {n.type === 'warning' && (
                        <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                      )}
                      {n.type === 'success' && (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                      )}
                      {n.type === 'info' && (
                        <Bell className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium text-slate-800 leading-snug">
                          {n.title}
                        </div>
                        <div className="flex items-center justify-between mt-1 text-[11px] text-slate-400">
                          <span>{n.time}</span>
                          <span className="font-semibold text-slate-700">{n.amount}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-3 py-2 border-t border-slate-100 text-center">
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-[11px] text-brand-600 hover:text-brand-700 font-medium"
                >
                  Close Panel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Merchant Selector / Profile Pill */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <div className="h-7 w-7 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0">
            A
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-800 leading-none">Aarav Supplies</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Admin (Pune)</div>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden md:block" />
        </div>
      </div>
    </header>
  )
}
