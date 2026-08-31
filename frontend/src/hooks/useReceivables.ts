import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function useReceivables(params?: { status?: string; search?: string }) {
  return useQuery({
    queryKey: ['receivables', params],
    queryFn: () => api.getReceivables(params),
  })
}

export function useCustomers() {
  return useQuery({
    queryKey: ['customers'],
    queryFn: api.getCustomers,
  })
}
