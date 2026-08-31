import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function useActivity(params?: { category?: string; severity?: string }) {
  return useQuery({
    queryKey: ['activity', params],
    queryFn: () => api.getActivity(params),
    refetchInterval: 1000 * 20, // 20s live polling
  })
}
