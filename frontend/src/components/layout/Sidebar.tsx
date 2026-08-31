import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Activity,
  Layers,
  Boxes,
  Receipt,
  ArrowLeftRight,
  GitFork,
  Bot,
  Building2,
  SlidersHorizontal,
} from 'lucide-react'
import { cn } from '@/utils/cn'

interface SidebarProps {
  merchantName?: string
}

export const Sidebar: React.FC<SidebarProps> = ({
  merchantName = 'Aarav Industrial Supplies',
}) => {
  const navItems = [
    { name: 'Overview', to: '/', icon: LayoutDashboard, exact: true },
    { name: 'Business State', to: '/business-state', icon: Layers },
    { name: 'Inventory', to: '/inventory', icon: Boxes },
    { name: 'Receivables', to: '/receivables', icon: Receipt },
    { name: 'Transactions', to: '/transactions', icon: ArrowLeftRight },
    { name: 'Scenarios', to: '/scenarios', icon: GitFork },
    { name: 'Negotiations', to: '/negotiations', icon: Bot },
    { name: 'Activity', to: '/activity', icon: Activity },
  ]

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 h-screen sticky top-0 select-none">
      {/* Brand & Engine Identification */}
      <div className="p-5 border-b border-slate-200/80">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-md bg-brand-600 flex items-center justify-center text-white font-bold text-base shadow-sm shrink-0">
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
              <polyline points="16 7 22 7 22 13" />
            </svg>
          </div>
          <div className="overflow-hidden">
            <h1 className="text-xs font-bold text-slate-900 tracking-tight leading-none uppercase">
              Liquidity Engine
            </h1>
            <p className="text-[10px] text-slate-500 truncate mt-0.5 font-medium">
              Economic Intelligence
            </p>
          </div>
        </div>

        {/* Merchant & Sandbox Pill */}
        <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 truncate">
            <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-xs font-medium text-slate-800 truncate" title={merchantName}>
              {merchantName}
            </span>
          </div>
          <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
            Sandbox
          </span>
        </div>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Platform Operations
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors group',
                  isActive
                    ? 'bg-brand-50/80 text-brand-700 font-semibold shadow-xs border border-brand-100'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={cn(
                      'w-4 h-4 shrink-0 transition-colors',
                      isActive ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-600'
                    )}
                  />
                  <span>{item.name}</span>
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer / System Status */}
      <div className="p-3.5 border-t border-slate-200/80 bg-slate-50/50">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-medium text-slate-600">Engine Online</span>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
            <SlidersHorizontal className="w-3 h-3" />
            v1.0.0
          </div>
        </div>
      </div>
    </aside>
  )
}
