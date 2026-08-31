import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function usePayables(params?: { status?: string; priority?: string; search?: string }) {
  return useQuery({
    queryKey: ['payables', params],
    queryFn: () => api.getPayables(params),
  })
}
