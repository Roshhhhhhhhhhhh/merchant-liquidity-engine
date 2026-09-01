import axios from 'axios'
import type {
  Merchant,
  BusinessState,
  InventoryListResponse,
  ReceivablesListResponse,
  CustomerListResponse,
  PayablesListResponse,
  TransactionListResponse,
  SnapshotTimelineResponse,
  ActivityListResponse,
  StateScoreResponse,
  StateDriversResponse,
  StateHistoryResponse,
  StateDeltaResponse,
  EconomicAction,
  ActionEvaluationResponse,
  ScenarioSimulateRequest,
  ScenarioSimulateResponse,
  ScenarioListResponse,
  BuyerRequestModel,
  DealCandidateModel,
  BuyerRequest,
  BuyerCounterRequest,
  NegotiationSession,
  NegotiationListResponse,
  PaymentOrder,
  PaymentVerifyRequest,
  PaymentVerifyResponse,
  PaymentDetailsResponse,
  PaymentConfigStatusResponse,
} from '@/types'


// Use relative /api to leverage Vite proxy in development, or explicit env variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Error interceptor for diagnostic logging
apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.debug(`[API ${response.config.method?.toUpperCase()} ${response.config.url}]:`, response.status)
    }
    return response
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.warn(
        `[API Error ${error?.config?.method?.toUpperCase()} ${error?.config?.baseURL}${error?.config?.url}]:`,
        error?.response?.data || error.message
      )
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health')
    return res.data
  },

  // Merchant & Economic State
  getMerchant: async (): Promise<Merchant> => {
    const res = await apiClient.get<Merchant>('/merchant')
    return res.data
  },

  getBusinessState: async (): Promise<BusinessState> => {
    const res = await apiClient.get<BusinessState>('/merchant/state')
    return res.data
  },

  getStateScore: async (): Promise<StateScoreResponse> => {
    const res = await apiClient.get<StateScoreResponse>('/merchant/state/score')
    return res.data
  },

  getStateDrivers: async (): Promise<StateDriversResponse> => {
    const res = await apiClient.get<StateDriversResponse>('/merchant/state/drivers')
    return res.data
  },

  getStateHistory: async (): Promise<StateHistoryResponse> => {
    const res = await apiClient.get<StateHistoryResponse>('/merchant/state/history')
    return res.data
  },

  getStateDelta: async (daysAgo: number = 30): Promise<StateDeltaResponse> => {
    const res = await apiClient.get<StateDeltaResponse>('/merchant/state/delta', {
      params: { days_ago: daysAgo },
    })
    return res.data
  },

  evaluateAction: async (action: EconomicAction): Promise<ActionEvaluationResponse> => {
    const res = await apiClient.post<ActionEvaluationResponse>('/merchant/state/evaluate-action', {
      action,
    })
    return res.data
  },

  // Inventory
  getInventory: async (params?: {
    category?: string
    status?: string
    search?: string
  }): Promise<InventoryListResponse> => {
    const res = await apiClient.get<InventoryListResponse>('/inventory', { params })
    return res.data
  },

  // Receivables & Customers
  getReceivables: async (params?: {
    status?: string
    search?: string
  }): Promise<ReceivablesListResponse> => {
    const res = await apiClient.get<ReceivablesListResponse>('/receivables', { params })
    return res.data
  },

  getCustomers: async (): Promise<CustomerListResponse> => {
    const res = await apiClient.get<CustomerListResponse>('/receivables/customers')
    return res.data
  },

  // Payables
  getPayables: async (params?: {
    status?: string
    priority?: string
    search?: string
  }): Promise<PayablesListResponse> => {
    const res = await apiClient.get<PayablesListResponse>('/payables', { params })
    return res.data
  },

  // Transactions
  getTransactions: async (params?: {
    payment_status?: string
    settlement_status?: string
    search?: string
  }): Promise<TransactionListResponse> => {
    const res = await apiClient.get<TransactionListResponse>('/transactions', { params })
    return res.data
  },

  // Snapshots & Trends
  getSnapshots: async (): Promise<SnapshotTimelineResponse> => {
    const res = await apiClient.get<SnapshotTimelineResponse>('/snapshots')
    return res.data
  },

  // Activity feed
  getActivity: async (params?: {
    category?: string
    severity?: string
  }): Promise<ActivityListResponse> => {
    const res = await apiClient.get<ActivityListResponse>('/activity', { params })
    return res.data
  },

  // Counterfactual Scenario Simulation (Phase 3)
  simulateScenario: async (payload: ScenarioSimulateRequest): Promise<ScenarioSimulateResponse> => {
    const res = await apiClient.post<ScenarioSimulateResponse>('/scenarios/simulate', payload)
    return res.data
  },

  getScenarios: async (): Promise<ScenarioListResponse> => {
    const res = await apiClient.get<ScenarioListResponse>('/scenarios')
    return res.data
  },

  getScenarioById: async (scenarioId: string): Promise<ScenarioSimulateResponse> => {
    const res = await apiClient.get<ScenarioSimulateResponse>(`/scenarios/${scenarioId}`)
    return res.data
  },

  generateDealOptions: async (payload: BuyerRequestModel): Promise<DealCandidateModel[]> => {
    const res = await apiClient.post<DealCandidateModel[]>('/scenarios/deals/generate', payload)
    return res.data
  },

  // Agentic Commerce & Autonomous Negotiation (Phase 4)
  parseBuyerRequest: async (message: string): Promise<BuyerRequest> => {
    const res = await apiClient.post<BuyerRequest>('/agent/buyer/request', { message })
    return res.data
  },

  startNegotiation: async (buyerRequest: BuyerRequest): Promise<NegotiationSession> => {
    const res = await apiClient.post<NegotiationSession>('/agent/negotiations', {
      buyer_request: buyerRequest,
    })
    return res.data
  },

  getNegotiations: async (): Promise<NegotiationListResponse> => {
    const res = await apiClient.get<NegotiationListResponse>('/agent/negotiations')
    return res.data
  },

  getNegotiationById: async (sessionId: string): Promise<NegotiationSession> => {
    const res = await apiClient.get<NegotiationSession>(`/agent/negotiations/${sessionId}`)
    return res.data
  },

  sendBuyerCounter: async (sessionId: string, payload: BuyerCounterRequest): Promise<NegotiationSession> => {
    const res = await apiClient.post<NegotiationSession>(`/agent/negotiations/${sessionId}/message`, payload)
    return res.data
  },

  acceptNegotiationOffer: async (sessionId: string): Promise<NegotiationSession> => {
    const res = await apiClient.post<NegotiationSession>(`/agent/negotiations/${sessionId}/accept`)
    return res.data
  },

  rejectNegotiationOffer: async (sessionId: string, reason?: string): Promise<NegotiationSession> => {
    const res = await apiClient.post<NegotiationSession>(`/agent/negotiations/${sessionId}/reject`, { reason })
    return res.data
  },

  runDemoNegotiation: async (): Promise<NegotiationSession> => {
    const res = await apiClient.post<NegotiationSession>('/agent/negotiations/demo', {})
    return res.data
  },

  // Payment & Execution (Phase 5)
  getPaymentStatus: async (): Promise<PaymentConfigStatusResponse> => {
    const res = await apiClient.get<PaymentConfigStatusResponse>('/payments/status')
    return res.data
  },

  createPaymentOrder: async (negotiationId: string): Promise<PaymentOrder> => {

    const res = await apiClient.post<PaymentOrder>('/payments/orders', {
      negotiation_id: negotiationId,
    })
    return res.data
  },

  verifyPayment: async (payload: PaymentVerifyRequest): Promise<PaymentVerifyResponse> => {
    const res = await apiClient.post<PaymentVerifyResponse>('/payments/verify', payload)
    return res.data
  },

  getPaymentOrder: async (paymentOrderId: string): Promise<PaymentDetailsResponse> => {
    const res = await apiClient.get<PaymentDetailsResponse>(`/payments/${paymentOrderId}`)
    return res.data
  },

  getPaymentByNegotiation: async (negotiationId: string): Promise<PaymentDetailsResponse> => {
    const res = await apiClient.get<PaymentDetailsResponse>(`/payments/negotiation/${negotiationId}`)
    return res.data
  },
}
