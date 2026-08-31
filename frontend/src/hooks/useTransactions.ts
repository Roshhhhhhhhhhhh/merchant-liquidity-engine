import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function useTransactions(params?: {
  payment_status?: string
  settlement_status?: string
  search?: string
}) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: () => api.getTransactions(params),
  })
}
