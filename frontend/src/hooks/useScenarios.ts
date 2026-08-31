import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type {
  ScenarioSimulateRequest,
  ScenarioSimulateResponse,
  ScenarioListResponse,
  BuyerRequestModel,
} from '@/types'

export function useScenarios() {
  return useQuery<ScenarioListResponse>({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
    staleTime: 30000,
  })
}

export function useScenarioDetails(scenarioId: string | null) {
  return useQuery<ScenarioSimulateResponse>({
    queryKey: ['scenario', scenarioId],
    queryFn: () => {
      if (!scenarioId) throw new Error('No scenario ID provided')
      return api.getScenarioById(scenarioId)
    },
    enabled: Boolean(scenarioId),
  })
}

export function useSimulateScenario() {
  const queryClient = useQueryClient()

  return useMutation<ScenarioSimulateResponse, Error, ScenarioSimulateRequest>({
    mutationFn: (payload) => api.simulateScenario(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
      queryClient.setQueryData(['scenario', data.scenario_id], data)
    },
  })
}

export function useGenerateDeals() {
  return useMutation({
    mutationFn: (payload: BuyerRequestModel) => api.generateDealOptions(payload),
  })
}
