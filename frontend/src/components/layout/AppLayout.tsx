import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useMerchant } from '@/hooks/useMerchant'

export const AppLayout: React.FC = () => {
  const location = useLocation()
  const { data: merchant } = useMerchant()

  // Map route to page title and subtitle
  const pageMeta = (() => {
    switch (location.pathname) {
      case '/':
        return {
          title: 'Merchant Overview',
          subtitle: 'Current economic position and liquidity outlook',
        }
      case '/business-state':
        return {
          title: 'Business State',
          subtitle: 'Multi-dimensional economic scorecard and working capital velocity',
        }
      case '/inventory':
        return {
          title: 'Inventory Operations',
          subtitle: 'Stock valuation, aging inventory analysis, and reorder health',
        }
      case '/receivables':
        return {
          title: 'Receivables & Collections',
          subtitle: 'DSO tracking, invoice aging distribution, and cash exposure',
        }
      case '/transactions':
        return {
          title: 'Transactions Log',
          subtitle: 'Order fulfillment, payment capture, and settlement audit trail',
        }
      case '/scenarios':
        return {
          title: 'Scenarios & Counterfactuals',
          subtitle: 'Evaluate how commercial decisions may change the merchant’s future state',
        }
      case '/activity':
        return {
          title: 'Operational Activity',
          subtitle: 'System audit feed, threshold breaches, and liquidity events',
        }
      default:
        return {
          title: 'Merchant Liquidity Engine',
          subtitle: 'Optimize what a transaction does to the business',
        }
    }
  })()

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      {/* Sidebar */}
      <Sidebar merchantName={merchant?.trade_name || 'Aarav Industrial Supplies'} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={pageMeta.title} subtitle={pageMeta.subtitle} />

        <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
