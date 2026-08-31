import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { OverviewPage } from '@/pages/OverviewPage'
import { BusinessStatePage } from '@/pages/BusinessStatePage'
import { InventoryPage } from '@/pages/InventoryPage'
import { ReceivablesPage } from '@/pages/ReceivablesPage'
import { TransactionsPage } from '@/pages/TransactionsPage'
import { ScenariosPage } from '@/pages/ScenariosPage'
import { NegotiationPage } from '@/pages/NegotiationPage'
import { ActivityPage } from '@/pages/ActivityPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <OverviewPage />,
      },
      {
        path: 'business-state',
        element: <BusinessStatePage />,
      },
      {
        path: 'inventory',
        element: <InventoryPage />,
      },
      {
        path: 'receivables',
        element: <ReceivablesPage />,
      },
      {
        path: 'transactions',
        element: <TransactionsPage />,
      },
      {
        path: 'scenarios',
        element: <ScenariosPage />,
      },
      {
        path: 'negotiations',
        element: <NegotiationPage />,
      },
      {
        path: 'activity',
        element: <ActivityPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])
