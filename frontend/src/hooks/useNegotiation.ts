import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import type {
  BuyerRequest,
  BuyerCounterRequest,
  NegotiationSession,
  NegotiationListResponse,
} from '../types'

export const useNegotiations = () => {
  return useQuery<NegotiationListResponse>({
    queryKey: ['negotiations'],
    queryFn: () => api.getNegotiations(),
    refetchInterval: 10000,
  })
}

export const useNegotiationSession = (sessionId?: string) => {
  return useQuery<NegotiationSession>({
    queryKey: ['negotiation-session', sessionId],
    queryFn: () => api.getNegotiationById(sessionId!),
    enabled: Boolean(sessionId),
    refetchInterval: (query) => {
      const data = query.state.data
      // Stop polling if final state reached
      if (data?.status === 'ACCEPTED' || data?.status === 'REJECTED' || data?.status === 'EXPIRED') {
        return false
      }
      return 5000
    },
  })
}

export const useParseBuyerRequest = () => {
  return useMutation<BuyerRequest, Error, string>({
    mutationFn: (message: string) => api.parseBuyerRequest(message),
  })
}

export const useStartNegotiation = () => {
  const queryClient = useQueryClient()
  return useMutation<NegotiationSession, Error, BuyerRequest>({
    mutationFn: (req: BuyerRequest) => api.startNegotiation(req),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
      queryClient.setQueryData(['negotiation-session', newSession.id], newSession)
    },
  })
}

export const useSendBuyerCounter = (sessionId: string) => {
  const queryClient = useQueryClient()
  return useMutation<NegotiationSession, Error, BuyerCounterRequest>({
    mutationFn: (payload: BuyerCounterRequest) => api.sendBuyerCounter(sessionId, payload),
    onSuccess: (updatedSession) => {
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
      queryClient.setQueryData(['negotiation-session', sessionId], updatedSession)
    },
  })
}

export const useAcceptOffer = (sessionId: string) => {
  const queryClient = useQueryClient()
  return useMutation<NegotiationSession, Error, void>({
    mutationFn: () => api.acceptNegotiationOffer(sessionId),
    onSuccess: (updatedSession) => {
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
      queryClient.setQueryData(['negotiation-session', sessionId], updatedSession)
    },
  })
}

export const useRejectOffer = (sessionId: string) => {
  const queryClient = useQueryClient()
  return useMutation<NegotiationSession, Error, string | undefined>({
    mutationFn: (reason?: string) => api.rejectNegotiationOffer(sessionId, reason),
    onSuccess: (updatedSession) => {
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
      queryClient.setQueryData(['negotiation-session', sessionId], updatedSession)
    },
  })
}

export const useRunDemoNegotiation = () => {
  const queryClient = useQueryClient()
  return useMutation<NegotiationSession, Error, void>({
    mutationFn: () => api.runDemoNegotiation(),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
      queryClient.setQueryData(['negotiation-session', newSession.id], newSession)
    },
  })
}
