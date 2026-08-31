import React from 'react'
import {
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Package,
  Wallet,
  Clock,
  Sparkles,
  ExternalLink,
  X,
} from 'lucide-react'
import type { PaymentVerifyResponse } from '@/types'
import { Link } from 'react-router-dom'

interface PaymentExecutionModalProps {
  isOpen: boolean
  onClose: () => void
  data: PaymentVerifyResponse | null
}

export const PaymentExecutionModal: React.FC<PaymentExecutionModalProps> = ({
  isOpen,
  onClose,
  data,
}) => {
  if (!isOpen || !data) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-emerald-500/30 rounded-2xl shadow-2xl shadow-emerald-950/50 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Top Glowing Header Banner */}
        <div className="p-6 bg-gradient-to-r from-emerald-950/80 via-slate-900 to-slate-900 border-b border-slate-800 flex items-start justify-between relative">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-tight">Payment Executed & Settled</h2>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Razorpay Test Mode
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Cryptographic HMAC signature verified. Merchant Economic Twin balance sheet updated.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 custom-scrollbar">
          {/* Key Reference Stats Banner */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Gross Amount</div>
              <div className="text-lg font-bold text-white mt-0.5">{data.amount_formatted}</div>
              <div className="text-[10px] text-emerald-400 flex items-center gap-1 mt-1">
                <CheckCircle2 className="w-3 h-3" /> Captured via UPI
              </div>
            </div>

            <div className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Transaction Ref</div>
              <div className="text-sm font-bold text-cyan-400 font-mono mt-1 truncate">{data.reference_id}</div>
              <div className="text-[10px] text-slate-400 mt-1 truncate">ID: {data.transaction_id}</div>
            </div>

            <div className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Razorpay Payment ID</div>
              <div className="text-xs font-bold text-emerald-400 font-mono mt-1.5 truncate">
                {data.razorpay_payment_id}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">Signature Verified</div>
            </div>

            <div className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Stock Decrement</div>
              <div className="text-sm font-bold text-amber-400 mt-1">
                -{data.inventory_updated?.quantity_deducted || 50} units
              </div>
              <div className="text-[10px] text-emerald-400 mt-1">Warehouse Updated</div>
            </div>
          </div>

          {/* EVC Comparison Banner (Projected vs Realized) */}
          <div className="p-4 bg-emerald-950/30 border border-emerald-500/20 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs text-emerald-400/90 font-semibold uppercase tracking-wider">
                  Economic Value Creation (EVC) Realization
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Comparison between pre-deal simulation projection and actual realized balance sheet gain.
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6 text-right">
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Projected EVC</div>
                <div className="text-sm font-bold text-slate-300">{data.projected_evc_formatted}</div>
              </div>
              <ArrowRight className="w-4 h-4 text-emerald-500" />
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Realized EVC</div>
                <div className="text-base font-extrabold text-emerald-400">{data.realized_evc_formatted}</div>
              </div>
            </div>
          </div>

          {/* Before vs After Balance Sheet Delta Table */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Before → After Economic State Transition
              </h3>
              <span className="text-xs text-slate-400">Real-time Snapshot Delta</span>
            </div>

            <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-900/50">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-800/40 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="py-2.5 px-4">Financial Dimension</th>
                    <th className="py-2.5 px-4 text-right">Pre-Deal (Before)</th>
                    <th className="py-2.5 px-4 text-right">Realized (After)</th>
                    <th className="py-2.5 px-4 text-right">Net Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {data.metrics_comparison?.map((m, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-medium text-slate-200 flex items-center gap-2">
                        {m.metric.includes('Cash') && <Wallet className="w-3.5 h-3.5 text-emerald-400" />}
                        {m.metric.includes('Inventory') && <Package className="w-3.5 h-3.5 text-amber-400" />}
                        {m.metric.includes('Runway') && <Clock className="w-3.5 h-3.5 text-cyan-400" />}
                        {m.metric.includes('Pressure') && <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />}
                        {m.metric}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400 font-mono">{m.before_formatted}</td>
                      <td className="py-3 px-4 text-right font-bold text-white font-mono">{m.after_formatted}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] ${
                            m.direction === 'favorable'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : m.direction === 'unfavorable'
                              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {m.delta_formatted}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Modal Footer Controls */}
        <div className="p-4 bg-slate-900 border-t border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Economic Twin state synced in SQLite database.</span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/transactions"
              onClick={onClose}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-colors border border-slate-700"
            >
              View in Ledger <ExternalLink className="w-3.5 h-3.5" />
            </Link>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors shadow-lg shadow-emerald-900/30"
            >
              Done & Return to Workspace
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
