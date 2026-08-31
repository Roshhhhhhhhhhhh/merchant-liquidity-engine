import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function useInventory(params?: { category?: string; status?: string; search?: string }) {
  return useQuery({
    queryKey: ['inventory', params],
    queryFn: () => api.getInventory(params),
  })
}

export function useProducts() {
  return useQuery({
    queryKey: ['products'],
    queryFn: () => api.getInventory().then((res) => res.items),
  })
}
