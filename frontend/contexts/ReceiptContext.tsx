'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

export interface ReceiptItem {
  name: string
  price: number
  unit_price?: number
  quantity?: number
  category?: string
  allergens?: string[]
  health_flags?: string[]
}

export interface Receipt {
  id?: string
  merchant: string
  date: string
  items: ReceiptItem[]
  total?: number
  subtotal?: number
  tax?: number
  return_policy_days?: number
  return_deadline?: string
  image_url?: string
  text_summary?: string
  created_at?: string
}

export interface HealthInsights {
  allergen_alerts: string[]
  health_score: number
  health_warnings: string[]
  suggestions: string[]
  diet_flags: {
    [key: string]: boolean
  }
  nutritional_summary?: string
}

interface ReceiptContextType {
  currentReceipt: Receipt | null
  setCurrentReceipt: (receipt: Receipt | null) => void
  healthInsights: HealthInsights | null
  setHealthInsights: (insights: HealthInsights | null) => void
  receiptImage: string | null
  setReceiptImage: (image: string | null) => void
}

const ReceiptContext = createContext<ReceiptContextType | undefined>(undefined)

export function ReceiptProvider({ children }: { children: ReactNode }) {
  const [currentReceipt, setCurrentReceipt] = useState<Receipt | null>(null)
  const [healthInsights, setHealthInsights] = useState<HealthInsights | null>(null)
  const [receiptImage, setReceiptImage] = useState<string | null>(null)

  return (
    <ReceiptContext.Provider
      value={{
        currentReceipt,
        setCurrentReceipt,
        healthInsights,
        setHealthInsights,
        receiptImage,
        setReceiptImage,
      }}
    >
      {children}
    </ReceiptContext.Provider>
  )
}

export function useReceipt() {
  const context = useContext(ReceiptContext)
  if (context === undefined) {
    throw new Error('useReceipt must be used within a ReceiptProvider')
  }
  return context
}
