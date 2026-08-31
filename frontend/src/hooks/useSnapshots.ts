import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function useSnapshots() {
  return useQuery({
    queryKey: ['snapshots'],
    queryFn: api.getSnapshots,
  })
}
