import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { EconomicAction } from '@/types'

export function useMerchant() {
  return useQuery({
    queryKey: ['merchant'],
    queryFn: api.getMerchant,
    staleTime: 1000 * 60 * 5, // 5 mins
  })
}

export function useBusinessState() {
  return useQuery({
    queryKey: ['business-state'],
    queryFn: api.getBusinessState,
    refetchInterval: 1000 * 30, // 30s auto-refresh for live status
  })
}

export function useStateScore() {
  return useQuery({
    queryKey: ['merchant-state-score'],
    queryFn: api.getStateScore,
    staleTime: 1000 * 30,
  })
}

export function useStateDrivers() {
  return useQuery({
    queryKey: ['merchant-state-drivers'],
    queryFn: api.getStateDrivers,
    staleTime: 1000 * 30,
  })
}

export function useStateHistory() {
  return useQuery({
    queryKey: ['merchant-state-history'],
    queryFn: api.getStateHistory,
    staleTime: 1000 * 60,
  })
}

export function useStateDelta(daysAgo: number = 30) {
  return useQuery({
    queryKey: ['merchant-state-delta', daysAgo],
    queryFn: () => api.getStateDelta(daysAgo),
    staleTime: 1000 * 60,
  })
}

export function useEvaluateAction() {
  return useMutation({
    mutationFn: (action: EconomicAction) => api.evaluateAction(action),
  })
}
