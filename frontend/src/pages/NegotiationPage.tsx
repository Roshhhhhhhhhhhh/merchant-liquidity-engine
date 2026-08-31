import React, { useState, useEffect } from 'react'
import {
  Bot,
  User,
  Sparkles,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  Send,
  Zap,
  Activity,
  Layers,
  Terminal,
  FileCheck2,
} from 'lucide-react'
import {
  useNegotiations,
  useNegotiationSession,
  useParseBuyerRequest,
  useStartNegotiation,
  useSendBuyerCounter,
  useAcceptOffer,
  useRejectOffer,
  useRunDemoNegotiation,
} from '@/hooks/useNegotiation'
import {
  useCreatePaymentOrder,
  usePaymentByNegotiation,
  useRazorpayCheckout,
} from '@/hooks/usePayment'
import { PaymentExecutionModal } from '@/components/payment/PaymentExecutionModal'
import { useBusinessState } from '@/hooks/useMerchant'
import { formatINR } from '@/utils/formatters'
import type { BuyerRequest, BuyerCounterRequest, PaymentVerifyResponse } from '@/types'

export const NegotiationPage: React.FC = () => {
  const { data: negotiationsData, refetch: refetchList } = useNegotiations()
  const { data: merchantState } = useBusinessState()

  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'timeline' | 'traces'>('timeline')

  // Payment Execution States (Phase 5)
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false)
  const [paymentExecutionData, setPaymentExecutionData] = useState<PaymentVerifyResponse | null>(null)
  const [paymentErrorMessage, setPaymentErrorMessage] = useState<string | null>(null)

  // Input states
  const [rawInquiry, setRawInquiry] = useState<string>(
    'We need 300 units of Industrial Control Valves within 6 days. Target budget ₹3.60 Lakh with immediate payment.'
  )
  const [buyerId] = useState<string>('buyer_apex_infrastructure_ltd')
  const [quantity, setQuantity] = useState<number>(300)
  const [targetBudget, setTargetBudget] = useState<number>(360000)
  const [deliveryDays, setDeliveryDays] = useState<number>(6)
  const [paymentDays, setPaymentDays] = useState<number>(0)

  // Counteroffer input states
  const [counterMessage, setCounterMessage] = useState<string>(
    'Can you meet ₹3.45 Lakh for 350 units with immediate settlement?'
  )
  const [counterTargetBudget, setCounterTargetBudget] = useState<number>(345000)
  const [counterQuantity, setCounterQuantity] = useState<number>(350)
  const [counterPaymentDays] = useState<number>(0)

  // Hooks
  const {
    data: activeSession,
    refetch: refetchSession,
  } = useNegotiationSession(selectedSessionId || undefined)

  const parseRequestMutation = useParseBuyerRequest()
  const startNegotiationMutation = useStartNegotiation()
  const sendCounterMutation = useSendBuyerCounter(selectedSessionId || '')
  const acceptOfferMutation = useAcceptOffer(selectedSessionId || '')
  const rejectOfferMutation = useRejectOffer(selectedSessionId || '')
  const runDemoMutation = useRunDemoNegotiation()

  // Phase 5 Payment Hooks
  const createPaymentOrderMutation = useCreatePaymentOrder()
  const { data: linkedPaymentOrder, refetch: refetchPaymentOrder } = usePaymentByNegotiation(selectedSessionId)
  const { initiatePayment, isProcessing: isRazorpayProcessing } = useRazorpayCheckout()

  const isSessionPaid = linkedPaymentOrder?.status === 'PAID'

  // Auto-select latest session if none selected
  useEffect(() => {
    if (!selectedSessionId && negotiationsData?.sessions && negotiationsData.sessions.length > 0) {
      setSelectedSessionId(negotiationsData.sessions[0].id)
    }
  }, [negotiationsData, selectedSessionId])

  const handleParseNaturalLanguage = async () => {
    if (!rawInquiry.trim()) return
    try {
      const parsed = await parseRequestMutation.mutateAsync(rawInquiry)
      if (parsed.quantity) setQuantity(parsed.quantity)
      if (parsed.maximum_budget) setTargetBudget(parsed.maximum_budget)
      if (parsed.maximum_delivery_days) setDeliveryDays(parsed.maximum_delivery_days)
      if (parsed.preferred_payment_days !== undefined) setPaymentDays(parsed.preferred_payment_days)
    } catch (e) {
      console.error('Failed to parse inquiry', e)
    }
  }

  const handleStartNegotiation = async () => {
    const req: BuyerRequest = {
      buyer_id: buyerId,
      intent: 'bulk_order',
      product_requirements: ['Industrial Hardware'],
      quantity,
      maximum_budget: targetBudget,
      maximum_delivery_days: deliveryDays,
      preferred_payment_days: paymentDays,
      raw_inquiry_text: rawInquiry,
    }

    const session = await startNegotiationMutation.mutateAsync(req)
    setSelectedSessionId(session.id)
    refetchList()
  }

  const handleSendCounter = async () => {
    if (!selectedSessionId) return
    const payload: BuyerCounterRequest = {
      counter_message: counterMessage,
      target_budget: counterTargetBudget,
      requested_quantity: counterQuantity,
      preferred_payment_days: counterPaymentDays,
      max_delivery_days: deliveryDays,
    }
    await sendCounterMutation.mutateAsync(payload)
  }

  const handleAcceptOffer = async () => {
    if (!selectedSessionId) return
    await acceptOfferMutation.mutateAsync()
  }

  const handleRejectOffer = async () => {
    if (!selectedSessionId) return
    await rejectOfferMutation.mutateAsync('Commercial terms unacceptable after multiple rounds')
  }

  const handleProceedToPayment = async () => {
    if (!selectedSessionId) return
    setPaymentErrorMessage(null)
    try {
      const order = await createPaymentOrderMutation.mutateAsync(selectedSessionId)
      initiatePayment({
        order,
        onSuccess: (verifyRes) => {
          setPaymentExecutionData(verifyRes)
          setIsPaymentModalOpen(true)
          refetchSession()
          refetchPaymentOrder()
          refetchList()
        },
        onError: (err) => {
          setPaymentErrorMessage(err)
        },
      })
    } catch (e: any) {
      setPaymentErrorMessage(e?.response?.data?.detail || e.message || 'Failed to create payment order')
    }
  }

  const handleInspectRealizedImpact = () => {
    if (paymentExecutionData) {
      setIsPaymentModalOpen(true)
    } else if (linkedPaymentOrder) {
      // Re-fetch and open modal
      refetchPaymentOrder().then(() => {
        setIsPaymentModalOpen(true)
      })
    }
  }

  const handleRunDemo = async () => {
    const session = await runDemoMutation.mutateAsync()
    setSelectedSessionId(session.id)
    refetchList()
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'ACCEPTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Agreement Reached
          </span>
        )
      case 'OFFERED':
      case 'COUNTER_OFFERED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Zap className="w-3.5 h-3.5" /> Merchant Offer Active
          </span>
        )
      case 'BUYER_COUNTERED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5" /> Buyer Countered
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" /> Negotiation Terminated
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <Activity className="w-3.5 h-3.5" /> {status || 'ANALYZING'}
          </span>
        )
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] overflow-hidden bg-slate-50">
      {/* Top Action & Sub-Header Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600 font-bold">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 leading-none">
                Agentic Commerce & Autonomous Negotiation
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                Phase 4
              </span>
              <span className="px-2 py-0.5 text-[10px] font-medium rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                Agent Mode: Fallback Safe
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Autonomous multi-agent protocol between AI Buyer Agent and Merchant Economic Twin
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Active Session Selector */}
          {negotiationsData?.sessions && negotiationsData.sessions.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-slate-500">Session:</span>
              <select
                className="text-xs border border-slate-200 rounded-md px-2.5 py-1.5 bg-white text-slate-800 font-medium focus:ring-1 focus:ring-brand-500 focus:outline-none"
                value={selectedSessionId || ''}
                onChange={(e) => setSelectedSessionId(e.target.value)}
              >
                {negotiationsData.sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id.slice(0, 14)} — {s.status} (R{s.round_number}/{s.max_rounds})
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={handleRunDemo}
            disabled={runDemoMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-gradient-to-r from-brand-600 to-indigo-600 text-white hover:from-brand-700 hover:to-indigo-700 shadow-sm transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {runDemoMutation.isPending ? 'Simulating...' : 'Run B2B Demo Scenario'}
          </button>

          <button
            onClick={() => {
              refetchList()
              refetchSession()
            }}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100 transition-colors"
            title="Refresh"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main 3-Column Workstation Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* COLUMN 1: BUYER INQUIRY & CONTROLS */}
        <div className="w-80 border-r border-slate-200 bg-white flex flex-col shrink-0 overflow-y-auto">
          <div className="p-4 border-b border-slate-100 bg-slate-50/70">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-brand-600" />
              AI Buyer Agent Setup
            </h2>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Simulate procurement inquiries with deterministic budget utility
            </p>
          </div>

          <div className="p-4 space-y-4 flex-1">
            {/* Natural Language Prompt Box */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-700">Commercial Inquiry</label>
                <button
                  type="button"
                  onClick={handleParseNaturalLanguage}
                  disabled={parseRequestMutation.isPending}
                  className="text-[10px] font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" />
                  {parseRequestMutation.isPending ? 'Parsing...' : 'Extract'}
                </button>
              </div>
              <textarea
                rows={3}
                value={rawInquiry}
                onChange={(e) => setRawInquiry(e.target.value)}
                placeholder="Type natural procurement request..."
                className="w-full text-xs p-2.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none resize-none font-sans"
              />
            </div>

            {/* Extracted Structured Parameters */}
            <div className="space-y-3 pt-2 border-t border-slate-100">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Extracted Parameters
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Target Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">
                  Maximum Budget ({formatINR(targetBudget)})
                </label>
                <input
                  type="number"
                  value={targetBudget}
                  onChange={(e) => setTargetBudget(Number(e.target.value))}
                  className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Max Delivery (Days)</label>
                  <input
                    type="number"
                    value={deliveryDays}
                    onChange={(e) => setDeliveryDays(Number(e.target.value))}
                    className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Payment (Days)</label>
                  <input
                    type="number"
                    value={paymentDays}
                    onChange={(e) => setPaymentDays(Number(e.target.value))}
                    className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleStartNegotiation}
                disabled={startNegotiationMutation.isPending}
                className="w-full mt-2 py-2 px-3 rounded-md text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                {startNegotiationMutation.isPending ? 'Negotiating...' : 'Submit Buyer Request'}
              </button>
            </div>

            {/* Active Session Counter Controls */}
            {activeSession && activeSession.status !== 'ACCEPTED' && activeSession.status !== 'REJECTED' && (
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-700 flex items-center justify-between">
                  <span>Buyer Counteroffer</span>
                  <span className="text-[10px] text-amber-600 font-medium">Round {activeSession.round_number}/5</span>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Counter Message</label>
                  <input
                    type="text"
                    value={counterMessage}
                    onChange={(e) => setCounterMessage(e.target.value)}
                    className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs font-medium text-slate-600 block mb-1">Target Budget</label>
                    <input
                      type="number"
                      value={counterTargetBudget}
                      onChange={(e) => setCounterTargetBudget(Number(e.target.value))}
                      className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-600 block mb-1">Quantity</label>
                    <input
                      type="number"
                      value={counterQuantity}
                      onChange={(e) => setCounterQuantity(Number(e.target.value))}
                      className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-md focus:ring-1 focus:ring-brand-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleSendCounter}
                    disabled={sendCounterMutation.isPending}
                    className="flex-1 py-1.5 px-2 rounded-md text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-white shadow-xs transition-colors disabled:opacity-50"
                  >
                    {sendCounterMutation.isPending ? 'Sending...' : 'Send Counter'}
                  </button>
                  <button
                    type="button"
                    onClick={handleAcceptOffer}
                    disabled={acceptOfferMutation.isPending}
                    className="flex-1 py-1.5 px-2 rounded-md text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-colors disabled:opacity-50"
                  >
                    Accept
                  </button>
                  <button
                    type="button"
                    onClick={handleRejectOffer}
                    disabled={rejectOfferMutation.isPending}
                    className="py-1.5 px-2 rounded-md text-xs font-semibold border border-rose-200 text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}

            {/* ACCEPTED Session: Payment Execution Action Card */}
            {activeSession && activeSession.status === 'ACCEPTED' && (
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-300 space-y-2.5 shadow-xs">
                  <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs">
                    <FileCheck2 className="w-4 h-4 text-emerald-600" />
                    <span>Commercial Deal Accepted</span>
                  </div>

                  <p className="text-[11px] text-emerald-700 leading-relaxed">
                    Terms are locked and immutable. Execute payment in Razorpay Test Mode to trigger real-time balance sheet realization.
                  </p>

                  {paymentErrorMessage && (
                    <div className="p-2 rounded bg-rose-50 border border-rose-200 text-[11px] text-rose-700">
                      {paymentErrorMessage}
                    </div>
                  )}

                  {!isSessionPaid ? (
                    <button
                      type="button"
                      onClick={handleProceedToPayment}
                      disabled={createPaymentOrderMutation.isPending || isRazorpayProcessing}
                      className="w-full py-2.5 px-3 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md flex items-center justify-center gap-2 transition-all disabled:opacity-50 hover:shadow-emerald-900/20"
                    >
                      <Zap className="w-4 h-4 fill-current text-emerald-200" />
                      {createPaymentOrderMutation.isPending || isRazorpayProcessing
                        ? 'Processing Razorpay...'
                        : `Proceed to Payment (${formatINR(activeSession.current_offer?.gross_value || 0)})`}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleInspectRealizedImpact}
                      className="w-full py-2 px-3 rounded-lg text-xs font-bold bg-slate-900 hover:bg-slate-800 text-emerald-400 border border-emerald-500/30 flex items-center justify-center gap-2 transition-all shadow-sm"
                    >
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      Inspect Realized Economic Impact
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* COLUMN 2: STRUCTURED NEGOTIATION TIMELINE & AUDIT TRACE */}
        <div className="flex-1 flex flex-col bg-slate-100/60 overflow-hidden border-r border-slate-200">
          {/* Timeline Tab Header */}
          <div className="bg-white border-b border-slate-200 px-5 py-2.5 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setActiveTab('timeline')}
                className={`text-xs font-semibold pb-1 border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'timeline'
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                Negotiation Timeline
                {activeSession?.messages && (
                  <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
                    {activeSession.messages.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('traces')}
                className={`text-xs font-semibold pb-1 border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'traces'
                    ? 'border-purple-600 text-purple-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                <Terminal className="w-3.5 h-3.5" />
                Deterministic Agent Audit Traces
                {activeSession?.traces && (
                  <span className="px-1.5 py-0.2 rounded-full bg-purple-50 text-[10px] text-purple-700">
                    {activeSession.traces.length}
                  </span>
                )}
              </button>
            </div>

            {activeSession && (
              <div className="flex items-center gap-2">
                {getStatusBadge(activeSession.status)}
                <span className="text-[11px] font-mono text-slate-400">
                  Round {activeSession.round_number} of {activeSession.max_rounds}
                </span>
              </div>
            )}
          </div>

          {/* Timeline / Trace Content Area */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {!activeSession ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8">
                <div className="h-12 w-12 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-center text-slate-400 mb-3">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800">No Active Negotiation Session</h3>
                <p className="text-xs text-slate-500 max-w-sm mt-1 mb-4">
                  Submit a new buyer inquiry from the left panel or run a one-click automated B2B demo scenario to
                  watch the agents negotiate in real time.
                </p>
                <button
                  onClick={handleRunDemo}
                  className="px-3.5 py-2 rounded-md text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-xs flex items-center gap-1.5 transition-colors"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Run Automated Demo Scenario
                </button>
              </div>
            ) : activeTab === 'timeline' ? (
              /* Structured B2B Event Stream */
              <div className="space-y-4 max-w-2xl mx-auto">
                {activeSession.messages.map((msg, index) => {
                  const isBuyer = msg.sender === 'buyer'
                  const isMerchant = msg.sender === 'merchant'

                  return (
                    <div
                      key={msg.id || index}
                      className={`flex flex-col rounded-xl border transition-all ${
                        msg.message_type === 'acceptance'
                          ? 'bg-emerald-50/70 border-emerald-300 shadow-xs'
                          : isMerchant
                          ? 'bg-white border-slate-200 shadow-xs'
                          : isBuyer
                          ? 'bg-blue-50/40 border-blue-200 shadow-xs'
                          : 'bg-slate-50 border-slate-200'
                      } p-4`}
                    >
                      {/* Event Header */}
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2.5">
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-6 w-6 rounded-md flex items-center justify-center text-xs font-bold ${
                              isMerchant
                                ? 'bg-purple-100 text-purple-700'
                                : isBuyer
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-slate-200 text-slate-700'
                            }`}
                          >
                            {isMerchant ? <Bot className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
                          </span>
                          <div>
                            <span className="text-xs font-bold text-slate-800">
                              {isMerchant ? 'Merchant Agent' : isBuyer ? 'AI Buyer Agent' : 'System Engine'}
                            </span>
                            <span className="text-[10px] text-slate-400 ml-2">
                              Round {msg.round_number} • {msg.message_type.toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>

                      {/* Natural Language / Formatted Narrative */}
                      <p className="text-xs text-slate-700 leading-relaxed">{msg.raw_message}</p>

                      {/* Structured Commercial Offer Table */}
                      {msg.structured_data && typeof msg.structured_data === 'object' && msg.structured_data.offer && (
                        <div className="mt-3 pt-3 border-t border-slate-100">
                          <div className="rounded-lg bg-slate-50 border border-slate-200/80 p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-[11px] font-bold text-slate-800">
                                {msg.structured_data.offer.product_name || 'Industrial Lot'}
                              </span>
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                                {msg.structured_data.offer.strategy_tag || 'Optimized Proposal'}
                              </span>
                            </div>

                            <div className="grid grid-cols-4 gap-2 text-center text-xs">
                              <div className="bg-white p-1.5 rounded border border-slate-200">
                                <div className="text-[10px] text-slate-400 font-medium">Quantity</div>
                                <div className="font-bold text-slate-800">{msg.structured_data.offer.quantity} units</div>
                              </div>
                              <div className="bg-white p-1.5 rounded border border-slate-200">
                                <div className="text-[10px] text-slate-400 font-medium">Unit Price</div>
                                <div className="font-bold text-slate-800">₹{msg.structured_data.offer.unit_price}</div>
                              </div>
                              <div className="bg-white p-1.5 rounded border border-slate-200">
                                <div className="text-[10px] text-slate-400 font-medium">Gross Value</div>
                                <div className="font-bold text-brand-600">
                                  {msg.structured_data.offer.gross_value_formatted || formatINR(msg.structured_data.offer.gross_value)}
                                </div>
                              </div>
                              <div className="bg-white p-1.5 rounded border border-slate-200">
                                <div className="text-[10px] text-slate-400 font-medium">Payment</div>
                                <div className="font-bold text-slate-800">
                                  {msg.structured_data.offer.payment_timing_days === 0 ? 'Immediate UPI' : `Net ${msg.structured_data.offer.payment_timing_days}d`}
                                </div>
                              </div>
                            </div>

                            {/* Economic Engine Impact Summary */}
                            <div className="mt-2.5 pt-2 border-t border-slate-200 flex items-center justify-between text-[11px]">
                              <span className="text-slate-500">
                                Economic Value Created: <strong className="text-emerald-700">{msg.structured_data.offer.economic_value_formatted || formatINR(msg.structured_data.offer.economic_value)}</strong>
                              </span>
                              <span className="text-slate-500">
                                Pressure Delta: <strong className="text-blue-700">{msg.structured_data.offer.pressure_score_delta} pts</strong>
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Final Agreement Certificate */}
                      {msg.message_type === 'acceptance' && (
                        <div className="mt-3 pt-3 border-t border-emerald-200 space-y-2.5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-emerald-800 text-xs font-semibold">
                              <FileCheck2 className="w-4 h-4 text-emerald-600" />
                              Binding Commercial Terms Confirmed
                            </div>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                              Ready for Settlement
                            </span>
                          </div>

                          {!isSessionPaid ? (
                            <button
                              type="button"
                              onClick={handleProceedToPayment}
                              disabled={createPaymentOrderMutation.isPending || isRazorpayProcessing}
                              className="w-full py-2.5 px-3 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md flex items-center justify-center gap-2 transition-all disabled:opacity-50 hover:shadow-emerald-900/20"
                            >
                              <Zap className="w-4 h-4 fill-current text-emerald-200" />
                              {createPaymentOrderMutation.isPending || isRazorpayProcessing
                                ? 'Connecting to Razorpay Sandbox...'
                                : `Proceed to Payment (${formatINR(activeSession.current_offer?.gross_value || 0)})`}
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={handleInspectRealizedImpact}
                              className="w-full py-2 px-3 rounded-lg text-xs font-bold bg-slate-900 hover:bg-slate-800 text-emerald-400 border border-emerald-500/30 flex items-center justify-center gap-2 transition-all shadow-sm"
                            >
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                              Inspect Realized Economic Impact
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              /* Observability Audit Traces */
              <div className="space-y-3 max-w-3xl mx-auto">
                <div className="text-xs text-slate-500 pb-2 border-b border-slate-200 flex items-center justify-between">
                  <span>Audit Trail of Deterministic Tool Invocations</span>
                  <span className="font-mono text-[11px]">{activeSession.traces.length} steps logged</span>
                </div>

                {activeSession.traces.map((tr, idx) => (
                  <div key={tr.id || idx} className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="h-5 px-1.5 rounded bg-purple-100 text-purple-800 text-[10px] font-bold flex items-center">
                          {tr.agent}
                        </span>
                        <span className="font-semibold text-slate-800">{tr.action}</span>
                        {tr.tool_called && (
                          <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-slate-100 text-slate-600 border border-slate-200">
                            {tr.tool_called}()
                          </span>
                        )}
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        tr.result === 'SUCCESS' || tr.result === 'ACCEPTED'
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}>
                        {tr.result || 'OK'}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 font-sans">
                      {tr.tool_output_summary || tr.decision}
                    </div>

                    {tr.decision && tr.tool_output_summary && (
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 italic">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        Rationale: {tr.decision}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* COLUMN 3: LIVE ECONOMIC CONTEXT & PROJECTED DELTA */}
        <div className="w-80 bg-white flex flex-col shrink-0 overflow-y-auto">
          <div className="p-4 border-b border-slate-100 bg-slate-50/70">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-brand-600" />
              Live Merchant Twin State
            </h2>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Authoritative economic decision boundary
            </p>
          </div>

          <div className="p-4 space-y-4 flex-1">
            {/* Merchant Health Snapshot */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Current Health</div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400">Cash Balance</div>
                  <div className="font-bold text-slate-900">
                    {merchantState?.cash?.formatted_value || '₹14.20 Lakh'}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400">Receivables</div>
                  <div className="font-bold text-slate-900">
                    {merchantState?.receivables?.formatted_value || '₹19.65 Lakh'}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400">Aging Inventory</div>
                  <div className="font-bold text-amber-700">
                    {merchantState?.aging_inventory?.formatted_value || '₹5.80 Lakh'}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                  <div className="text-[10px] text-slate-400">Pressure Score</div>
                  <div className="font-bold text-brand-600">
                    {merchantState?.pressure_score ?? 58} / 100
                  </div>
                </div>
              </div>
            </div>

            {/* Active Offer Projected Counterfactual Delta */}
            {activeSession?.current_offer && (
              <div className="pt-3 border-t border-slate-100 space-y-2.5">
                <div className="text-[11px] font-bold uppercase tracking-wider text-purple-700 flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5" />
                  Projected Deal Transition
                </div>

                <div className="p-3 rounded-lg bg-purple-50/60 border border-purple-200 space-y-2 text-xs">
                  <div className="flex justify-between items-center pb-1.5 border-b border-purple-200/60">
                    <span className="text-slate-600">Economic Value Created</span>
                    <span className="font-bold text-emerald-700">
                      {activeSession.current_offer.economic_value_formatted ||
                        formatINR(activeSession.current_offer.economic_value)}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Pressure Score</span>
                    <span className="font-semibold text-slate-800 flex items-center gap-1">
                      {activeSession.current_offer.current_pressure_score}
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <strong className="text-emerald-700">
                        {activeSession.current_offer.projected_pressure_score}
                      </strong>
                      <span className="text-[10px] text-emerald-600">
                        ({activeSession.current_offer.pressure_score_delta} pts)
                      </span>
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Settlement Velocity</span>
                    <span className="font-semibold text-slate-800">
                      {activeSession.current_offer.payment_timing_days === 0
                        ? '0 Days (Immediate Cash)'
                        : `${activeSession.current_offer.payment_timing_days} Days`}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Offered Strategy</span>
                    <span className="font-semibold text-purple-800">
                      {activeSession.current_offer.strategy_tag || 'Balanced Value'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Policy Boundary Guardrails */}
            <div className="pt-3 border-t border-slate-100 space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Policy Guardrails
              </div>
              <ul className="text-xs space-y-1 text-slate-600">
                <li className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span>Minimum Margin Floor</span>
                  <span className="font-semibold text-slate-800">12.0%</span>
                </li>
                <li className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span>Maximum Discount</span>
                  <span className="font-semibold text-slate-800">18.0%</span>
                </li>
                <li className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span>Maximum Negotiation</span>
                  <span className="font-semibold text-slate-800">5 Rounds</span>
                </li>
                <li className="flex items-center justify-between py-1">
                  <span>Cash Velocity Preference</span>
                  <span className="font-semibold text-emerald-700">Immediate Settlement</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Realized Economic Impact & Razorpay Execution Modal */}
      <PaymentExecutionModal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        data={paymentExecutionData}
      />
    </div>
  )
}
