export type DimensionStatus = 'Healthy' | 'Watch' | 'Warning' | 'Critical' | 'Softening'
export type LiquiditySeverity = 'Critical' | 'Warning' | 'Watch' | 'Info'
export type BusinessStateClassification = 'Strong' | 'Healthy' | 'Watch' | 'Stressed' | 'Critical'

export interface Merchant {
  id: string
  name: string
  trade_name: string
  gst_number: string
  industry: string
  address?: string
  base_currency: string
  created_at: string
  updated_at: string
}

export interface LiquidityPressureDriver {
  id: string
  title: string
  impact_amount?: number
  impact_formatted: string
  category: 'Receivables' | 'Inventory' | 'Payables' | 'Demand' | 'Margin' | 'Liquidity'
  description: string
  severity: LiquiditySeverity
  contribution_score?: number
  rank?: number
}

export interface DimensionState {
  dimension: string
  name: string
  value: number
  formatted_value: string
  status: DimensionStatus
  label: string
  trend?: 'Up' | 'Down' | 'Stable'
  trend_pct?: number
  benchmark?: string
}

export interface BusinessState {
  merchant_id: string
  merchant_name: string
  trade_name: string
  gst_number: string
  industry: string
  as_of: string

  // Score & Classification
  pressure_score: number
  liquidity_stress_score: number
  state: BusinessStateClassification
  liquidity_status: 'Healthy' | 'Watch' | 'Warning' | 'Critical'
  liquidity_outlook_headline: string
  liquidity_outlook_summary: string
  top_drivers: LiquidityPressureDriver[]
  drivers: LiquidityPressureDriver[]

  // Core 10 Dimensions
  cash: DimensionState
  receivables: DimensionState
  payables: DimensionState
  inventory_value: DimensionState
  aging_inventory: DimensionState
  gross_margin: DimensionState
  demand_trend: DimensionState
  customer_value: DimensionState
  fulfillment_capacity: DimensionState
  cash_runway: DimensionState

  // Direct Financial Measures
  cash_position?: number
  total_receivables?: number
  overdue_receivables?: number
  total_payables?: number
  near_term_payables?: number
  inventory_valuation?: number
  aging_inventory_value?: number
  available_inventory_units?: number
  gross_margin_pct?: number
  recent_revenue?: number
  recent_demand_trend_pct?: number
  payment_velocity?: number
  customer_portfolio_value?: number
  fulfillment_capacity_pct?: number
  cash_runway_days: number
  cash_runway_display?: string

  // Working Capital & Ratios
  working_capital: number
  working_capital_formatted: string
  quick_ratio: number
  current_ratio: number
  dso_days: number
  dpo_days: number
  dio_days: number
  cash_conversion_cycle: number
}

export interface CategoryBreakdown {
  category: string
  item_count: number
  total_value: number
  aging_value: number
  percentage: number
}

export interface InventorySummary {
  total_skus: number
  total_units: number
  total_inventory_value: number
  total_inventory_value_formatted: string
  total_aging_value: number
  total_aging_value_formatted: string
  aging_pct: number
  low_stock_count: number
  healthy_count: number
  watch_count: number
  aging_count: number
  critical_count: number
  category_breakdown: CategoryBreakdown[]
}

export interface InventoryItem {
  id: string
  product_id: string
  merchant_id: string
  product_sku: string
  product_name: string
  product_category: string
  unit: string
  unit_cost: number
  current_price: number
  min_stock_threshold: number
  available_quantity: number
  reserved_quantity: number
  days_in_stock: number
  batch_number?: string
  location: string
  status: 'Healthy' | 'Watch' | 'Aging' | 'Critical'
  demand_trend: 'Increasing' | 'Stable' | 'Softening' | 'Declining'
  inventory_value: number
  inventory_value_formatted: string
  gross_margin_pct: number
  last_restocked_at: string
  updated_at: string
}

export interface InventoryListResponse {
  summary: InventorySummary
  items: InventoryItem[]
}

export interface AgingBucket {
  bucket: string
  min_days: number
  max_days?: number
  count: number
  amount: number
  amount_formatted: string
  percentage: number
  status: DimensionStatus
}

export interface ReceivablesSummary {
  total_outstanding: number
  total_outstanding_formatted: string
  due_this_week: number
  due_this_week_formatted: string
  total_overdue: number
  total_overdue_formatted: string
  severely_overdue: number
  severely_overdue_formatted: string
  average_dso_days: number
  current_count: number
  due_soon_count: number
  overdue_count: number
  severely_overdue_count: number
  aging_buckets: AgingBucket[]
}

export interface ReceivableItem {
  id: string
  merchant_id: string
  customer_id: string
  customer_name: string
  customer_company: string
  customer_tier: 'Enterprise' | 'Tier-1' | 'Standard'
  invoice_number: string
  amount: number
  paid_amount: number
  balance_due: number
  amount_formatted: string
  balance_due_formatted: string
  issue_date: string
  due_date: string
  days_outstanding: number
  days_overdue: number
  status: 'Current' | 'Due Soon' | 'Overdue' | 'Severely Overdue'
  notes?: string
  created_at: string
  updated_at: string
}

export interface ReceivablesListResponse {
  summary: ReceivablesSummary
  items: ReceivableItem[]
}

export interface Customer {
  id: string
  merchant_id: string
  name: string
  company_name: string
  email: string
  phone?: string
  gstin?: string
  credit_limit: number
  credit_terms_days: number
  total_revenue: number
  customer_tier: 'Enterprise' | 'Tier-1' | 'Standard'
  payment_score: number
  created_at: string
  updated_at: string
}

export interface CustomerSummary {
  total_customers: number
  enterprise_count: number
  tier_1_count: number
  standard_count: number
  total_credit_granted: number
  total_outstanding_exposure: number
  avg_payment_score: number
}

export interface CustomerListResponse {
  summary: CustomerSummary
  customers: Customer[]
}

export interface PayableItem {
  id: string
  merchant_id: string
  vendor_name: string
  invoice_number: string
  amount: number
  paid_amount: number
  balance_due: number
  amount_formatted: string
  balance_due_formatted: string
  days_until_due: number
  issue_date: string
  due_date: string
  category: string
  status: 'Pending' | 'Scheduled' | 'Paid'
  priority: 'Critical' | 'High' | 'Medium' | 'Low'
  notes?: string
  created_at: string
  updated_at: string
}

export interface PayablesSummary {
  total_payables: number
  total_payables_formatted: string
  due_within_12_days: number
  due_within_12_days_formatted: string
  critical_priority_amount: number
  critical_priority_formatted: string
  average_dpo_days: number
  pending_count: number
  scheduled_count: number
  paid_count: number
}

export interface PayablesListResponse {
  summary: PayablesSummary
  items: PayableItem[]
}

export interface TransactionItem {
  id: string
  merchant_id: string
  customer_id: string
  product_id: string
  reference_id: string
  quantity: number
  unit_price: number
  gross_value: number
  cost_value: number
  net_margin_pct: number
  payment_status: 'Captured' | 'Pending' | 'Refunded' | 'Failed'
  settlement_status: 'Settled' | 'In Transit' | 'Pending'
  payment_method: string
  channel: string
  customer_name: string
  customer_company: string
  product_name: string
  product_sku: string
  product_category: string
  gross_value_formatted: string
  unit_price_formatted: string
  created_at: string
  source?: string
  negotiation_id?: string
  payment_order_id?: string
  razorpay_payment_id?: string
  razorpay_order_id?: string
  paid_at?: string
}

export interface TransactionSummary {
  total_transactions: number
  total_gross_volume: number
  total_gross_volume_formatted: string
  settled_volume: number
  settled_volume_formatted: string
  in_transit_volume: number
  in_transit_volume_formatted: string
  pending_volume: number
  pending_volume_formatted: string
  avg_order_value: number
  avg_order_value_formatted: string
  avg_gross_margin_pct: number
}

export interface TransactionListResponse {
  summary: TransactionSummary
  items: TransactionItem[]
}

export interface SnapshotTrendPoint {
  date: string
  timestamp: string
  cash_balance: number
  total_receivables: number
  total_payables: number
  inventory_value: number
  working_capital: number
  cash_runway_days: number
  liquidity_stress_score: number
  event_marker?: string
}

export interface EconomicSnapshotRecord {
  id: string
  merchant_id: string
  snapshot_date: string
  cash_balance: number
  total_receivables: number
  total_payables: number
  inventory_value: number
  aging_inventory_value: number
  gross_margin_pct: number
  cash_runway_days: number
  quick_ratio: number
  current_ratio: number
  working_capital: number
  dso_days: number
  dpo_days: number
  dio_days: number
  cash_conversion_cycle: number
  liquidity_stress_score: number
  event_marker?: string
  notes?: string
  cash_balance_formatted: string
  receivables_formatted: string
  payables_formatted: string
  inventory_formatted: string
  working_capital_formatted: string
  created_at: string
}

export interface SnapshotTimelineResponse {
  total_points: number
  start_date: string
  end_date: string
  data: SnapshotTrendPoint[]
  recent_snapshots: EconomicSnapshotRecord[]
}

export interface ActivityEventItem {
  id: string
  merchant_id: string
  event_type: string
  category: string
  title: string
  description: string
  severity: 'Info' | 'Low' | 'Medium' | 'High' | 'Critical'
  metadata_json?: string
  parsed_metadata?: Record<string, any>
  created_at: string
}

export interface ActivitySummary {
  total_events: number
  critical_count: number
  high_count: number
  medium_count: number
  info_count: number
  categories: string[]
}

export interface ActivityListResponse {
  summary: ActivitySummary
  events: ActivityEventItem[]
}

// Phase 2 New Interfaces
export interface MetricDelta {
  metric: string
  label: string
  before: number
  after: number
  absolute_change: number
  percentage_change: number
  direction: 'Positive' | 'Negative' | 'Neutral'
  unit: string
  formatted_before: string
  formatted_after: string
  formatted_change: string
}

export interface StateDeltaResponse {
  merchant_id: string
  baseline_date: string
  current_date: string
  baseline_state: string
  current_state: string
  baseline_pressure_score: number
  current_pressure_score: number
  deltas: MetricDelta[]
  summary: string
}

export interface StateScoreResponse {
  pressure_score: number
  state: BusinessStateClassification
  state_description: string
  component_scores: Record<string, number>
  component_weights: Record<string, number>
}

export interface StateDriversResponse {
  merchant_id: string
  as_of: string
  pressure_score: number
  state: BusinessStateClassification
  drivers: LiquidityPressureDriver[]
  total_drivers_count: number
}

export interface StateHistoryPoint {
  date: string
  timestamp: string
  cash: number
  receivables: number
  overdue_receivables: number
  payables: number
  inventory: number
  aging_inventory: number
  gross_margin_pct: number
  runway_days: number
  pressure_score: number
  state: string
  demand_trend_pct: number
  working_capital: number
  event_marker?: string
}

export interface StateHistoryResponse {
  merchant_id: string
  total_points: number
  start_date: string
  end_date: string
  history: StateHistoryPoint[]
}

export interface EconomicValueCreated {
  contribution_margin_value: number
  liquidity_improvement_value: number
  inventory_relief_value: number
  receivable_improvement_value: number
  economic_risk_cost: number
  total_economic_value_created: number
  assumptions: Record<string, any>
}

export interface EconomicAction {
  action_type: string
  target_id?: string
  parameters?: Record<string, any>
  description: string
}

export interface ActionEvaluationResponse {
  action: EconomicAction
  is_favorable: boolean
  current_pressure_score: number
  projected_pressure_score: number
  pressure_score_delta: number
  current_state: string
  projected_state: string
  economic_value_created: EconomicValueCreated
  deltas: MetricDelta[]
  recommendation_summary: string
}

// -------------------------------------------------------------
// PHASE 3: Counterfactual Economic Simulator Types
// -------------------------------------------------------------

export interface BuyerRequestModel {
  product_id?: string
  product_name?: string
  requested_quantity: number
  target_budget?: number
  max_delivery_days: number
  preferred_payment_timing_days: number
  custom_notes?: string
}

export interface MerchantConstraintsModel {
  min_margin_pct: number
  max_credit_days: number
  require_advance_payment: boolean
  max_discount_pct: number
  allow_aging_clearance_bonus: boolean
}

export interface EconomicValueBreakdownModel {
  contribution_margin_value: number
  liquidity_improvement_value: number
  inventory_relief_value: number
  receivable_improvement_value: number
  economic_risk_cost: number
  capacity_cost: number
  stockout_opportunity_cost: number
  total_economic_value_created: number
  weights_used: Record<string, number>
}

export interface DealCandidateModel {
  id: string
  label: string
  strategy_tag: string
  is_recommended: boolean
  rank: number
  action_type: string
  quantity: number
  unit_price: number
  gross_value: number
  estimated_cogs: number
  contribution_margin: number
  margin_pct: number
  discount_pct: number
  payment_timing_days: number
  delivery_days: number
  cash_impact: number
  inventory_impact: number
  aging_inventory_impact: number
  receivable_impact: number
  capacity_impact_pct: number
  days_inventory_coverage: number
  stockout_risk: string
  economic_value: number
  economic_value_breakdown: EconomicValueBreakdownModel
  current_pressure_score: number
  projected_pressure_score: number
  pressure_score_delta: number
  current_state: string
  projected_state: string
  gross_value_formatted: string
  contribution_margin_formatted: string
  cash_impact_formatted: string
  inventory_impact_formatted: string
  aging_inventory_impact_formatted: string
  receivable_impact_formatted: string
  economic_value_formatted: string
  explanation: string
  deltas: MetricDelta[]
}

export interface ScenarioSimulateRequest {
  merchant_id?: string
  scenario_name?: string
  request: BuyerRequestModel
  constraints?: MerchantConstraintsModel
}

export interface ScenarioSimulateResponse {
  scenario_id: string
  merchant_id: string
  scenario_name: string
  request: BuyerRequestModel
  current_state: BusinessState
  candidates: DealCandidateModel[]
  recommended_candidate: DealCandidateModel
  ranking_explanation: string
  created_at: string
}

export interface ScenarioListItem {
  id: string
  merchant_id: string
  name: string
  status: string
  requested_quantity: number
  target_budget: number
  target_budget_formatted: string
  recommended_deal_label?: string
  recommended_deal_strategy?: string
  economic_value: number
  economic_value_formatted: string
  projected_pressure_score: number
  projected_state: string
  created_at: string
}

export interface ScenarioListResponse {
  total_scenarios: number
  scenarios: ScenarioListItem[]
}

// ==========================================
// PHASE 4: AGENTIC COMMERCE & NEGOTIATION
// ==========================================

export type NegotiationStatus =
  | 'REQUESTED'
  | 'ANALYZING'
  | 'OFFERED'
  | 'BUYER_COUNTERED'
  | 'RE_EVALUATING'
  | 'COUNTER_OFFERED'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'EXPIRED'

export type NegotiationMessageType =
  | 'request'
  | 'analysis'
  | 'offer'
  | 'counter'
  | 'acceptance'
  | 'rejection'
  | 'system_notice'

export interface BuyerRequest {
  buyer_id: string
  intent: string
  product_requirements?: string[]
  product_id?: string
  quantity: number
  maximum_budget: number
  maximum_delivery_days: number
  preferred_payment_days: number
  constraints?: Record<string, any>
  raw_inquiry_text?: string
}

export interface BuyerCounterRequest {
  counter_message: string
  target_budget?: number
  requested_quantity?: number
  preferred_payment_days?: number
  max_delivery_days?: number
}

export interface NegotiationMessage {
  id: string
  session_id: string
  sender: 'buyer' | 'merchant' | 'system'
  message_type: NegotiationMessageType
  round_number: number
  raw_message: string
  structured_data?: any
  created_at: string
}

export interface NegotiationOffer {
  id: string
  session_id: string
  candidate_id?: string
  round_number: number
  product_id: string
  product_name: string
  quantity: number
  unit_price: number
  gross_value: number
  gross_value_formatted?: string
  payment_timing_days: number
  delivery_days: number
  economic_value: number
  economic_value_formatted?: string
  economic_value_breakdown?: Record<string, any>
  current_pressure_score: number
  projected_pressure_score: number
  pressure_score_delta: number
  status: string
  strategy_tag?: string
  rationale?: string
  created_at: string
}

export interface AgentTrace {
  id: string
  session_id: string
  round_number: number
  timestamp: string
  agent: string
  action: string
  tool_called?: string
  tool_input?: any
  tool_output_summary?: string
  decision?: string
  result?: string
}

export interface NegotiationSession {
  id: string
  merchant_id: string
  buyer_id: string
  status: NegotiationStatus
  round_number: number
  max_rounds: number
  current_offer_id?: string
  current_offer?: NegotiationOffer
  buyer_request: BuyerRequest
  messages: NegotiationMessage[]
  offers: NegotiationOffer[]
  traces: AgentTrace[]
  final_agreement?: Record<string, any>
  agreement_reached: boolean
  created_at: string
  updated_at: string
}

export interface NegotiationListItem {
  id: string
  merchant_id: string
  buyer_id: string
  status: NegotiationStatus
  round_number: number
  max_rounds: number
  requested_quantity: number
  target_budget: number
  target_budget_formatted: string
  current_offer_gross?: number
  current_offer_gross_formatted?: string
  current_offer_evc?: number
  current_offer_evc_formatted?: string
  agreement_reached: boolean
  updated_at: string
  created_at: string
}

export interface NegotiationListResponse {
  total_sessions: number
  sessions: NegotiationListItem[]
}

export interface PaymentOrder {
  id: string
  negotiation_id: string
  merchant_id: string
  razorpay_order_id: string
  amount: number
  amount_formatted: string
  amount_paise: number
  currency: string
  status: string
  receipt: string
  razorpay_key_id: string
  merchant_name: string
  product_name: string
  quantity: number
  unit_price: number
  created_at: string
}

export interface PaymentVerifyRequest {
  payment_order_id: string
  razorpay_order_id: string
  razorpay_payment_id: string
  razorpay_signature: string
}

export interface EconomicMetricComparison {
  metric: string
  before_value: number
  after_value: number
  delta: number
  before_formatted: string
  after_formatted: string
  delta_formatted: string
  direction: 'favorable' | 'unfavorable' | 'neutral'
}

export interface PaymentVerifyResponse {
  success: boolean
  payment_order_id: string
  transaction_id: string
  reference_id: string
  razorpay_payment_id: string
  amount: number
  amount_formatted: string
  status: string
  settlement_status: string
  paid_at: string
  inventory_updated: {
    quantity_deducted: number
    status: string
  }
  metrics_comparison: EconomicMetricComparison[]
  projected_evc: number
  projected_evc_formatted: string
  realized_evc: number
  realized_evc_formatted: string
  evc_variance: number
  evc_variance_formatted: string
  message: string
}

export interface PaymentDetailsResponse {
  id: string
  negotiation_id: string
  merchant_id: string
  razorpay_order_id: string
  razorpay_payment_id?: string
  amount: number
  amount_formatted: string
  currency: string
  status: string
  receipt: string
  created_at: string
  paid_at?: string
  projected_evc?: number
  realized_evc?: number
}

