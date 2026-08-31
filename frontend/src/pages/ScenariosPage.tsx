import React, { useState, useEffect } from 'react'
import {
  Zap,
  Clock,
  Layers,
  ArrowRight,
  RefreshCw,
  Sliders,
  CheckCircle2,
  BarChart3,
  Cpu,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { useScenarios, useSimulateScenario, useScenarioDetails } from '@/hooks/useScenarios'
import { useBusinessState } from '@/hooks/useMerchant'
import type {
  BuyerRequestModel,
  MerchantConstraintsModel,
  ScenarioSimulateResponse,
} from '@/types'

// Quick Presets for instant simulation
const PRESETS = [
  {
    label: 'Standard Inquiry',
    description: '250 units, target ₹3.2L, 5-day delivery',
    data: {
      requested_quantity: 250,
      target_budget: 320000,
      max_delivery_days: 5,
      preferred_payment_timing_days: 0,
      custom_notes: 'Standard industrial inquiry for valves/actuators.',
    },
  },
  {
    label: 'Bulk Cash Deal',
    description: '400 units, target ₹4.8L, immediate cash',
    data: {
      requested_quantity: 400,
      target_budget: 480000,
      max_delivery_days: 7,
      preferred_payment_timing_days: 0,
      custom_notes: 'Buyer seeks high volume discount with instant UPI/settlement.',
    },
  },
  {
    label: 'Aging Stock Clearance',
    description: '180 units, clearing slow-moving inventory',
    data: {
      requested_quantity: 180,
      target_budget: 210000,
      max_delivery_days: 4,
      preferred_payment_timing_days: 0,
      custom_notes: 'Targeted clearance of inventory in stock >45 days.',
    },
  },
  {
    label: 'Delayed Credit Request',
    description: '300 units, requesting 30-day payment terms',
    data: {
      requested_quantity: 300,
      target_budget: 380000,
      max_delivery_days: 6,
      preferred_payment_timing_days: 30,
      custom_notes: 'Buyer requests standard enterprise 30-day deferred credit.',
    },
  },
]

export const ScenariosPage: React.FC = () => {
  const { data: economicState } = useBusinessState()
  const { data: scenarioHistory, refetch: refetchHistory } = useScenarios()
  const simulateMutation = useSimulateScenario()

  // Form State
  const [requestForm, setRequestForm] = useState<BuyerRequestModel>({
    requested_quantity: 250,
    target_budget: 320000,
    max_delivery_days: 5,
    preferred_payment_timing_days: 0,
    custom_notes: '',
  })

  const [constraints, setConstraints] = useState<MerchantConstraintsModel>({
    min_margin_pct: 12.0,
    max_credit_days: 30,
    require_advance_payment: false,
    max_discount_pct: 10.0,
    allow_aging_clearance_bonus: true,
  })

  const [showConstraints, setShowConstraints] = useState(false)
  const [activeSimulation, setActiveSimulation] = useState<ScenarioSimulateResponse | null>(null)
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null)

  const { data: fetchedScenario } = useScenarioDetails(selectedHistoryId)

  useEffect(() => {
    if (fetchedScenario) {
      setActiveSimulation(fetchedScenario)
      setSelectedCandidateId(fetchedScenario.recommended_candidate.id)
    }
  }, [fetchedScenario])

  // Run initial simulation on mount if none active
  useEffect(() => {
    if (!activeSimulation && !simulateMutation.isPending) {
      handleSimulate(requestForm)
    }
  }, [])

  const handleSimulate = (formData: BuyerRequestModel) => {
    simulateMutation.mutate(
      {
        scenario_name: `Inquiry: ${formData.requested_quantity} units`,
        request: formData,
        constraints,
      },
      {
        onSuccess: (data) => {
          setActiveSimulation(data)
          setSelectedCandidateId(data.recommended_candidate.id)
          refetchHistory()
        },
      }
    )
  }

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setRequestForm(preset.data)
    handleSimulate(preset.data)
  }

  const selectedCandidate =
    activeSimulation?.candidates.find((c) => c.id === selectedCandidateId) ||
    activeSimulation?.recommended_candidate

  return (
    <div className="space-y-6">
      {/* Header & Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              Counterfactual Economic Simulator
            </h1>
            <Badge variant="brand" size="sm">
              Phase 3 • Deterministic Engine
            </Badge>
          </div>
          <p className="text-xs text-slate-600 max-w-3xl">
            Simulate commercial transactions as future economic state transitions. Evaluates the multi-dimensional
            trade-off between revenue, immediate cash flow, receivables timing, inventory aging relief, and fulfillment capacity.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <div className="text-[11px] font-semibold text-slate-500 uppercase">Live Economic Twin</div>
            <div className="text-xs font-bold text-slate-800 flex items-center justify-end gap-1 mt-0.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              Pressure Score: {economicState?.pressure_score ?? 47}/100 ({economicState?.state ?? 'Watch'})
            </div>
          </div>
        </div>
      </div>

      {/* Preset Quick Actions */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {PRESETS.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => applyPreset(preset)}
            className="text-left p-3 rounded-lg border border-slate-200 bg-white hover:border-brand-500 hover:bg-brand-50/30 transition-all text-xs group"
          >
            <div className="font-semibold text-slate-900 group-hover:text-brand-700 flex items-center justify-between">
              {preset.label}
              <Zap className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-600" />
            </div>
            <div className="text-[11px] text-slate-500 mt-1">{preset.description}</div>
          </button>
        ))}
      </div>

      {/* Simulator Inquiry Input & Constraints Panel */}
      <Card className="border-slate-200">
        <CardHeader className="pb-3 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Sliders className="w-4 h-4 text-brand-600" />
                Commercial Inquiry Parameters
              </CardTitle>
              <CardDescription className="text-xs">
                Configure buyer order request and merchant boundary conditions to simulate candidates.
              </CardDescription>
            </div>
            <button
              onClick={() => setShowConstraints(!showConstraints)}
              className="text-xs font-semibold text-brand-600 hover:text-brand-800 flex items-center gap-1"
            >
              {showConstraints ? 'Hide Policy Constraints' : 'Customize Policy Constraints'}
            </button>
          </div>
        </CardHeader>

        <div className="p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Requested Quantity (Units)
              </label>
              <input
                type="number"
                min="10"
                max="5000"
                step="10"
                value={requestForm.requested_quantity}
                onChange={(e) =>
                  setRequestForm({ ...requestForm, requested_quantity: parseInt(e.target.value) || 0 })
                }
                className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Target Budget (₹)
              </label>
              <input
                type="number"
                min="10000"
                step="10000"
                value={requestForm.target_budget}
                onChange={(e) =>
                  setRequestForm({ ...requestForm, target_budget: parseFloat(e.target.value) || 0 })
                }
                className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Max Delivery Window (Days)
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={requestForm.max_delivery_days}
                onChange={(e) =>
                  setRequestForm({ ...requestForm, max_delivery_days: parseInt(e.target.value) || 1 })
                }
                className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Payment Timing Preference
              </label>
              <select
                value={requestForm.preferred_payment_timing_days}
                onChange={(e) =>
                  setRequestForm({
                    ...requestForm,
                    preferred_payment_timing_days: parseInt(e.target.value),
                  })
                }
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:ring-1 focus:ring-brand-500 focus:border-brand-500 bg-white"
              >
                <option value={0}>0 Days (Immediate UPI / Cash)</option>
                <option value={7}>7 Days (Accelerated Terms)</option>
                <option value={15}>15 Days (Semi-Monthly)</option>
                <option value={30}>30 Days (Standard Trade Credit)</option>
                <option value={45}>45 Days (Extended Terms)</option>
              </select>
            </div>
          </div>

          {/* Expandable Policy Constraints */}
          {showConstraints && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs animate-in fade-in">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Margin Floor: {constraints.min_margin_pct}%
                </label>
                <input
                  type="range"
                  min="5"
                  max="30"
                  step="1"
                  value={constraints.min_margin_pct}
                  onChange={(e) =>
                    setConstraints({ ...constraints, min_margin_pct: parseFloat(e.target.value) })
                  }
                  className="w-full accent-brand-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Max Credit Limit: {constraints.max_credit_days} Days
                </label>
                <input
                  type="range"
                  min="0"
                  max="60"
                  step="5"
                  value={constraints.max_credit_days}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_credit_days: parseInt(e.target.value) })
                  }
                  className="w-full accent-brand-600"
                />
              </div>

              <div className="flex items-center gap-2 pt-4">
                <input
                  type="checkbox"
                  id="aging_bonus"
                  checked={constraints.allow_aging_clearance_bonus}
                  onChange={(e) =>
                    setConstraints({ ...constraints, allow_aging_clearance_bonus: e.target.checked })
                  }
                  className="rounded text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="aging_bonus" className="font-semibold text-slate-700 cursor-pointer">
                  Prioritize Aging Stock Relief (&gt;45d)
                </label>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <div className="text-[11px] text-slate-500">
              Deterministic calculation: Simulates 4 discrete deal candidates across 7 economic dimensions.
            </div>

            <button
              onClick={() => handleSimulate(requestForm)}
              disabled={simulateMutation.isPending}
              className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {simulateMutation.isPending ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Simulating Future States...
                </>
              ) : (
                <>
                  <Cpu className="w-3.5 h-3.5" />
                  Run Counterfactual Simulation
                </>
              )}
            </button>
          </div>
        </div>
      </Card>

      {/* Simulation Results Section */}
      {activeSimulation && (
        <div className="space-y-6">
          {/* Spotlight Recommended Deal Banner */}
          <div className="relative overflow-hidden rounded-xl border border-emerald-300 bg-gradient-to-r from-emerald-50 via-teal-50/50 to-white p-6 shadow-sm">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider rounded bg-emerald-600 text-white flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Rank #1 Recommended Economic Choice
                  </span>
                  <Badge variant="success" size="sm">
                    {activeSimulation.recommended_candidate.strategy_tag}
                  </Badge>
                </div>

                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  {activeSimulation.recommended_candidate.label}
                </h2>

                <p className="text-xs text-slate-700 max-w-3xl leading-relaxed font-medium">
                  {activeSimulation.ranking_explanation}
                </p>
              </div>

              {/* Metric Highlights */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white/80 backdrop-blur-xs p-4 rounded-lg border border-emerald-200 shrink-0">
                <div className="text-center">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Net Economic Value</div>
                  <div className="text-sm font-bold text-emerald-700 font-mono mt-0.5">
                    {activeSimulation.recommended_candidate.economic_value_formatted}
                  </div>
                </div>

                <div className="text-center border-l border-slate-100 pl-3">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Immediate Cash</div>
                  <div className="text-sm font-bold text-slate-900 font-mono mt-0.5">
                    {activeSimulation.recommended_candidate.cash_impact_formatted}
                  </div>
                </div>

                <div className="text-center border-l border-slate-100 pl-3">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Aging Stock Cleared</div>
                  <div className="text-sm font-bold text-amber-700 font-mono mt-0.5">
                    {activeSimulation.recommended_candidate.aging_inventory_impact_formatted}
                  </div>
                </div>

                <div className="text-center border-l border-slate-100 pl-3">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Pressure Score</div>
                  <div className="text-sm font-bold text-emerald-700 font-mono mt-0.5 flex items-center justify-center gap-1">
                    {activeSimulation.recommended_candidate.projected_pressure_score}
                    <span className="text-[11px] font-normal text-emerald-600">
                      ({activeSimulation.recommended_candidate.pressure_score_delta} pts)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 4-Way Candidate Matrix */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                4-Way Deal Candidate Comparison Matrix
              </h3>
              <span className="text-xs text-slate-400">Strictly Ranked by Economic Value Created ($EVC$)</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {activeSimulation.candidates.map((cand) => {
                const isSelected = cand.id === selectedCandidateId
                const isRec = cand.is_recommended

                return (
                  <div
                    key={cand.id}
                    onClick={() => setSelectedCandidateId(cand.id)}
                    className={`cursor-pointer rounded-xl border transition-all p-4 flex flex-col justify-between relative bg-white ${
                      isSelected
                        ? 'border-brand-600 ring-2 ring-brand-500/20 shadow-md'
                        : isRec
                        ? 'border-emerald-300 hover:border-emerald-400 shadow-xs'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {isRec && (
                      <div className="absolute -top-2.5 right-4 bg-emerald-600 text-white text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                        Top Outcome
                      </div>
                    )}

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <Badge
                          variant={isRec ? 'success' : cand.rank === 2 ? 'brand' : 'neutral'}
                          size="sm"
                        >
                          Rank #{cand.rank}
                        </Badge>
                        <span className="text-[11px] font-mono text-slate-500">
                          {cand.payment_timing_days === 0 ? '0d (Cash)' : `${cand.payment_timing_days}d Credit`}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-slate-900 mb-1">{cand.label}</h4>
                      <p className="text-[11px] text-slate-600 line-clamp-2 mb-3">{cand.explanation}</p>

                      <div className="space-y-1.5 border-t border-slate-100 pt-3 text-xs">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Gross Volume:</span>
                          <span className="font-mono font-semibold text-slate-800">
                            {cand.gross_value_formatted}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-slate-500">Unit Price:</span>
                          <span className="font-mono text-slate-700">₹{cand.unit_price} / unit</span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-slate-500">Contribution Margin:</span>
                          <span className="font-mono font-semibold text-emerald-700">
                            {cand.contribution_margin_formatted} ({cand.margin_pct}%)
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-slate-500">Liquid Cash Inflow:</span>
                          <span
                            className={`font-mono font-semibold ${
                              cand.cash_impact > 0 ? 'text-emerald-700' : 'text-slate-400'
                            }`}
                          >
                            {cand.cash_impact_formatted}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-slate-500">Aging Stock Relief:</span>
                          <span
                            className={`font-mono font-semibold ${
                              cand.aging_inventory_impact > 0 ? 'text-amber-700' : 'text-slate-400'
                            }`}
                          >
                            {cand.aging_inventory_impact_formatted}
                          </span>
                        </div>

                        <div className="flex justify-between">
                          <span className="text-slate-500">Receivables Book:</span>
                          <span
                            className={`font-mono ${
                              cand.receivable_impact > 0 ? 'text-rose-600' : 'text-slate-400'
                            }`}
                          >
                            +{cand.receivable_impact_formatted}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 bg-slate-50/80 -mx-4 -mb-4 p-3 rounded-b-xl">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400">
                          Economic Value ($EVC$)
                        </span>
                        <span className="text-xs font-bold font-mono text-slate-900">
                          {cand.economic_value_formatted}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-500">Pressure Score:</span>
                        <span
                          className={`font-mono font-bold ${
                            cand.pressure_score_delta < 0
                              ? 'text-emerald-600'
                              : cand.pressure_score_delta > 0
                              ? 'text-rose-600'
                              : 'text-slate-700'
                          }`}
                        >
                          {cand.projected_pressure_score} ({cand.pressure_score_delta} pts)
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          {/* Selected Candidate Detailed Inspection */}
          {selectedCandidate && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* EVC Waterfall Breakdown */}
              <Card className="border-slate-200">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-brand-600" />
                    Economic Value Created ($EVC$) Waterfall
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Component breakdown for {selectedCandidate.label} ({selectedCandidate.economic_value_formatted} Total)
                  </CardDescription>
                </CardHeader>

                <div className="p-5 space-y-3">
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between p-2 rounded bg-emerald-50 border border-emerald-100">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-emerald-700">+35%</span>
                        <span className="font-medium text-slate-800">Contribution Margin (Gross Profit)</span>
                      </div>
                      <span className="font-mono font-bold text-emerald-700">
                        ₹{selectedCandidate.economic_value_breakdown.contribution_margin_value.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded bg-emerald-50 border border-emerald-100">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-emerald-700">+25%</span>
                        <span className="font-medium text-slate-800">Liquidity Utility (Immediate Cash Value)</span>
                      </div>
                      <span className="font-mono font-bold text-emerald-700">
                        ₹{selectedCandidate.economic_value_breakdown.liquidity_improvement_value.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded bg-amber-50 border border-amber-100">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-amber-700">+15%</span>
                        <span className="font-medium text-slate-800">Aging Inventory Velocity Relief</span>
                      </div>
                      <span className="font-mono font-bold text-amber-700">
                        ₹{selectedCandidate.economic_value_breakdown.inventory_relief_value.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded bg-blue-50 border border-blue-100">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-blue-700">+10%</span>
                        <span className="font-medium text-slate-800">Receivable Acceleration Benefit</span>
                      </div>
                      <span className="font-mono font-bold text-blue-700">
                        ₹{selectedCandidate.economic_value_breakdown.receivable_improvement_value.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded bg-rose-50 border border-rose-100">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-rose-700">-10%</span>
                        <span className="font-medium text-slate-800">Credit Delay &amp; Default Friction Cost</span>
                      </div>
                      <span className="font-mono font-bold text-rose-700">
                        -₹{selectedCandidate.economic_value_breakdown.economic_risk_cost.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-600">-5%</span>
                        <span className="font-medium text-slate-800">Capacity Overload Penalty</span>
                      </div>
                      <span className="font-mono font-bold text-slate-700">
                        -₹{selectedCandidate.economic_value_breakdown.capacity_cost.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-600">-5%</span>
                        <span className="font-medium text-slate-800">Stockout Opportunity Cost</span>
                      </div>
                      <span className="font-mono font-bold text-slate-700">
                        -₹{selectedCandidate.economic_value_breakdown.stockout_opportunity_cost.toLocaleString('en-IN')}
                      </span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">Total Net Economic Value ($EVC$):</span>
                    <span className="text-sm font-bold font-mono text-emerald-700">
                      {selectedCandidate.economic_value_formatted}
                    </span>
                  </div>
                </div>
              </Card>

              {/* State Transition Matrix */}
              <Card className="border-slate-200">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <Layers className="w-4 h-4 text-brand-600" />
                    Future Economic State Projection
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Directional shifts across primary balance sheet variables
                  </CardDescription>
                </CardHeader>

                <div className="p-5 space-y-4">
                  <div className="space-y-2.5">
                    {selectedCandidate.deltas.map((d, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 bg-slate-50/60 text-xs"
                      >
                        <div>
                          <div className="font-semibold text-slate-800">{d.label}</div>
                          <div className="text-[11px] text-slate-500 font-mono">
                            {d.formatted_before} <ArrowRight className="inline w-3 h-3 mx-1 text-slate-400" /> {d.formatted_after}
                          </div>
                        </div>

                        <div className="text-right">
                          <span
                            className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                              d.direction === 'Positive'
                                ? 'bg-emerald-100 text-emerald-800'
                                : d.direction === 'Negative'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-slate-200 text-slate-700'
                            }`}
                          >
                            {d.formatted_change}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 bg-brand-50/50 border border-brand-200 rounded-lg text-xs flex items-center justify-between">
                    <div>
                      <div className="font-bold text-slate-900">Projected Business Health Tier</div>
                      <div className="text-[11px] text-slate-600 mt-0.5">
                        Transition from {activeSimulation.current_state.state} to {selectedCandidate.projected_state}
                      </div>
                    </div>

                    <Badge
                      variant={
                        selectedCandidate.projected_state === 'Strong'
                          ? 'success'
                          : selectedCandidate.projected_state === 'Healthy'
                          ? 'brand'
                          : selectedCandidate.projected_state === 'Watch'
                          ? 'warning'
                          : 'danger'
                      }
                    >
                      {selectedCandidate.projected_state} Tier
                    </Badge>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Scenario Run History */}
          {scenarioHistory && scenarioHistory.scenarios.length > 0 && (
            <Card className="border-slate-200">
              <CardHeader className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                      <Clock className="w-4 h-4 text-slate-500" />
                      Simulation Run History
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Past counterfactual simulations recorded in database ({scenarioHistory.total_scenarios} total)
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase text-[10px] font-semibold tracking-wider">
                    <tr>
                      <th className="px-4 py-2.5">Scenario Name</th>
                      <th className="px-4 py-2.5">Requested Qty</th>
                      <th className="px-4 py-2.5">Target Budget</th>
                      <th className="px-4 py-2.5">Recommended Deal</th>
                      <th className="px-4 py-2.5">Economic Value</th>
                      <th className="px-4 py-2.5">Projected Pressure</th>
                      <th className="px-4 py-2.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {scenarioHistory.scenarios.map((sc) => (
                      <tr key={sc.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3 font-sans font-semibold text-slate-900">{sc.name}</td>
                        <td className="px-4 py-3 text-slate-700">{sc.requested_quantity} units</td>
                        <td className="px-4 py-3 text-slate-700">{sc.target_budget_formatted}</td>
                        <td className="px-4 py-3 font-sans">
                          <Badge variant="brand" size="sm">
                            {sc.recommended_deal_label || 'Optimal'}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 font-bold text-emerald-700">{sc.economic_value_formatted}</td>
                        <td className="px-4 py-3 text-slate-700">
                          {sc.projected_pressure_score}/100 ({sc.projected_state})
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => setSelectedHistoryId(sc.id)}
                            className="text-brand-600 hover:text-brand-800 font-sans font-semibold text-xs"
                          >
                            Load Run
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
