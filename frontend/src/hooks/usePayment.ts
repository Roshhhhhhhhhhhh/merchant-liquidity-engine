import { useState, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type {
  PaymentOrder,
  PaymentVerifyRequest,
  PaymentVerifyResponse,
  PaymentDetailsResponse,
} from '@/types'

declare global {
  interface Window {
    Razorpay: any
  }
}

/**
 * Dynamically loads the official Razorpay Checkout JavaScript SDK.
 */
export function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true)
      return
    }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.onload = () => resolve(true)
    script.onerror = () => {
      console.warn('[Razorpay Checkout] Failed to load external checkout.js script. Falling back to sandbox simulator.')
      resolve(false)
    }
    document.body.appendChild(script)
  })
}

export function usePaymentStatus() {
  return useQuery({
    queryKey: ['payment-status'],
    queryFn: () => api.getPaymentStatus(),
    staleTime: 60000,
  })
}

export function useCreatePaymentOrder() {

  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (negotiationId: string) => api.createPaymentOrder(negotiationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
    },
  })
}

export function useVerifyPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PaymentVerifyRequest) => api.verifyPayment(payload),
    onSuccess: () => {
      // Invalidate all financial twin queries
      queryClient.invalidateQueries({ queryKey: ['business-state'] })
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['snapshots'] })
      queryClient.invalidateQueries({ queryKey: ['activity'] })
      queryClient.invalidateQueries({ queryKey: ['negotiations'] })
    },
  })
}

export function usePaymentByNegotiation(negotiationId: string | null) {
  return useQuery<PaymentDetailsResponse, Error>({
    queryKey: ['payment-order', 'negotiation', negotiationId],
    queryFn: () => api.getPaymentByNegotiation(negotiationId!),
    enabled: Boolean(negotiationId),
    retry: 1,
  })
}

export function usePaymentOrder(paymentOrderId: string | null) {
  return useQuery<PaymentDetailsResponse, Error>({
    queryKey: ['payment-order', paymentOrderId],
    queryFn: () => api.getPaymentOrder(paymentOrderId!),
    enabled: Boolean(paymentOrderId),
  })
}

interface InitiatePaymentOptions {
  order: PaymentOrder
  onSuccess: (verifyResponse: PaymentVerifyResponse) => void
  onError: (error: string) => void
}

export function useRazorpayCheckout() {
  const [isProcessing, setIsProcessing] = useState(false)
  const verifyPaymentMutation = useVerifyPayment()

  const initiatePayment = useCallback(
    async ({ order, onSuccess, onError }: InitiatePaymentOptions) => {
      setIsProcessing(true)
      try {
        const isLoaded = await loadRazorpayScript()

        // 1. If Razorpay SDK loaded and valid key available, open Razorpay Modal
        if (isLoaded && window.Razorpay && !order.razorpay_key_id.startsWith('rzp_test_mock')) {
          const options = {
            key: order.razorpay_key_id,
            amount: order.amount_paise,
            currency: order.currency,
            name: order.merchant_name,
            description: `Payment for ${order.quantity}x ${order.product_name} (${order.receipt})`,
            order_id: order.razorpay_order_id,
            image: 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=128&auto=format&fit=crop&q=60',
            handler: async (response: {
              razorpay_payment_id: string
              razorpay_order_id: string
              razorpay_signature: string
            }) => {
              try {
                const verifyResult = await verifyPaymentMutation.mutateAsync({
                  payment_order_id: order.id,
                  razorpay_order_id: response.razorpay_order_id || order.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                })
                setIsProcessing(false)
                onSuccess(verifyResult)
              } catch (err: any) {
                setIsProcessing(false)
                onError(err?.response?.data?.detail || err.message || 'Signature verification failed.')
              }
            },
            prefill: {
              name: 'Industrial Procurement Agent',
              email: 'procurement@apexindustrial.in',
              contact: '+919876543210',
            },
            theme: {
              color: '#065F46', // Emerald theme matching MLE design system
            },
            modal: {
              ondismiss: () => {
                setIsProcessing(false)
              },
            },
          }

          const rzp = new window.Razorpay(options)
          rzp.on('payment.failed', (response: any) => {
            setIsProcessing(false)
            onError(response.error.description || 'Razorpay payment failed.')
          })
          rzp.open()
        } else {
          // 2. Razorpay Test Sandbox Simulator (Seamless for instant test mode execution)
          const mockPaymentId = `pay_test_${Math.random().toString(36).substring(2, 10)}`
          const verifyResult = await verifyPaymentMutation.mutateAsync({
            payment_order_id: order.id,
            razorpay_order_id: order.razorpay_order_id,
            razorpay_payment_id: mockPaymentId,
            razorpay_signature: 'mock_valid_test_signature',
          })
          setIsProcessing(false)
          onSuccess(verifyResult)
        }
      } catch (err: any) {
        setIsProcessing(false)
        onError(err?.response?.data?.detail || err.message || 'Payment initiation failed.')
      }
    },
    [verifyPaymentMutation]
  )

  return {
    initiatePayment,
    isProcessing,
  }
}
