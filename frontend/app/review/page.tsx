'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { FiEdit2, FiCheck, FiTrash2, FiPlus } from 'react-icons/fi'
import { useReceipt } from '@/contexts/ReceiptContext'
import { analyzeReceipt } from '@/lib/api'

export default function ReviewPage() {
  const router = useRouter()
  const { currentReceipt, setCurrentReceipt, setHealthInsights, receiptImage } = useReceipt()
  
  const [items, setItems] = useState(currentReceipt?.items || [])
  const [merchant, setMerchant] = useState(currentReceipt?.merchant || '')
  const [date, setDate] = useState(currentReceipt?.date || '')
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editUnitPrice, setEditUnitPrice] = useState('')
  const [editQuantity, setEditQuantity] = useState('1')
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect if no receipt data
  useEffect(() => {
    if (!currentReceipt) {
      router.push('/upload')
    } else {
      setItems(currentReceipt.items)
      setMerchant(currentReceipt.merchant)
      setDate(currentReceipt.date)
    }
  }, [currentReceipt, router])

  const startEdit = (index: number) => {
    setEditingIndex(index)
    setEditName(items[index].name)
    const quantity = items[index].quantity || 1
    const unitPrice = items[index].unit_price || (items[index].price / quantity)
    setEditUnitPrice(unitPrice.toString())
    setEditQuantity(quantity.toString())
  }

  const saveEdit = () => {
    if (editingIndex !== null) {
      const unitPrice = parseFloat(editUnitPrice) || 0
      const quantity = parseInt(editQuantity, 10) || 1
      const lineTotal = unitPrice * quantity
      const updatedItems = [...items]
      updatedItems[editingIndex] = {
        ...updatedItems[editingIndex],
        name: editName,
        unit_price: unitPrice,
        quantity: quantity,
        price: lineTotal,
      }
      setItems(updatedItems)
      setEditingIndex(null)
      announceToScreenReader('Item updated')
    }
  }

  const deleteItem = (index: number) => {
    const updatedItems = items.filter((_, i) => i !== index)
    setItems(updatedItems)
    announceToScreenReader('Item deleted')
  }

  const addItem = () => {
    setItems([...items, { name: 'New Item', unit_price: 0, quantity: 1, price: 0, category: 'other' }])
    announceToScreenReader('New item added')
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setError(null)
    announceToScreenReader('Analyzing receipt for health insights with Gemini AI...')

    try {
      // Update receipt with edited data
      const updatedReceipt = {
        ...currentReceipt!,
        merchant,
        date,
        items,
        total: items.reduce((sum, item) => sum + ((item.unit_price || 0) * (item.quantity || 1)), 0)
      }
      setCurrentReceipt(updatedReceipt)

      // Call backend to analyze with Gemini
      const insights = await analyzeReceipt(updatedReceipt)
      setHealthInsights(insights)
      
      announceToScreenReader(`Analysis complete. Health score: ${insights.health_score}`)
      router.push('/results')
    } catch (error: any) {
      console.error('Analysis error:', error)
      const errorMessage = error.message || 'Failed to analyze receipt'
      setError(errorMessage)
      announceToScreenReader(errorMessage)
    } finally {
      setAnalyzing(false)
    }
  }

  const announceToScreenReader = (message: string) => {
    const announcer = document.getElementById('a11y-announcer')
    if (announcer) {
      announcer.textContent = message
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Review Receipt</h1>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left: Receipt preview */}
          <div className="card">
            <h2 className="text-2xl font-semibold mb-4">Receipt Image</h2>
            {receiptImage ? (
              <img 
                src={receiptImage} 
                alt="Receipt" 
                className="w-full rounded-lg"
              />
            ) : (
              <div className="bg-gray-200 rounded-lg aspect-[3/4] flex items-center justify-center text-gray-500">
                <span>No Image Available</span>
              </div>
            )}
          </div>

          {/* Right: Extracted data */}
          <div className="space-y-6">
            {/* Merchant and date */}
            <div className="card">
              <h2 className="text-2xl font-semibold mb-4">Store Information</h2>

              <div className="space-y-4">
                <div>
                  <label htmlFor="merchant" className="block text-sm font-semibold mb-2">
                    Merchant
                  </label>
                  <input
                    id="merchant"
                    type="text"
                    value={merchant}
                    onChange={(e) => setMerchant(e.target.value)}
                    className="input"
                    aria-label="Merchant name"
                  />
                </div>

                <div>
                  <label htmlFor="date" className="block text-sm font-semibold mb-2">
                    Purchase Date
                  </label>
                  <input
                    id="date"
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="input"
                    aria-label="Purchase date"
                  />
                </div>
              </div>
            </div>

            {/* Items list */}
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold">Items</h2>
                <button
                  onClick={addItem}
                  className="btn-secondary flex items-center gap-2"
                  aria-label="Add new item"
                >
                  <FiPlus size={20} />
                  <span>Add Item</span>
                </button>
              </div>

              <div className="space-y-3" role="list" aria-label="Receipt items">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                    role="listitem"
                  >
                    {editingIndex === index ? (
                      <>
                        <div className="flex-1 space-y-2">
                          <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="input"
                            placeholder="Item name"
                            aria-label="Item name"
                          />
                          <div className="flex gap-2 items-center">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={editUnitPrice}
                              onChange={(e) => setEditUnitPrice(e.target.value)}
                              className="input flex-1"
                              placeholder="Unit Price"
                              aria-label="Unit price per item"
                            />
                            <span className="px-2 font-semibold">×</span>
                            <input
                              type="number"
                              step="1"
                              min="1"
                              value={editQuantity}
                              onChange={(e) => setEditQuantity(e.target.value)}
                              className="input w-20"
                              placeholder="Qty"
                              aria-label="Item quantity"
                            />
                            <span className="px-2 font-semibold">=</span>
                            <div className="px-3 py-2 bg-blue-50 rounded font-semibold text-blue-900 min-w-24">
                              ${((parseFloat(editUnitPrice) || 0) * (parseInt(editQuantity, 10) || 1)).toFixed(2)}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={saveEdit}
                          className="btn-primary"
                          aria-label="Save item"
                        >
                          <FiCheck size={20} />
                        </button>
                      </>
                    ) : (
                      <>
                        <div className="flex-1">
                          <div className="font-semibold">{item.name}</div>
                          <div className="text-sm text-gray-600">
                            ${((item.unit_price || (item.price / (item.quantity || 1))).toFixed(2))} × {item.quantity || 1} = ${((item.unit_price || (item.price / (item.quantity || 1))) * (item.quantity || 1)).toFixed(2)}
                          </div>
                        </div>
                        <button
                          onClick={() => startEdit(index)}
                          className="btn-secondary"
                          aria-label={`Edit ${item.name}`}
                        >
                          <FiEdit2 size={18} />
                        </button>
                        <button
                          onClick={() => deleteItem(index)}
                          className="btn-danger"
                          aria-label={`Delete ${item.name}`}
                        >
                          <FiTrash2 size={18} />
                        </button>
                      </>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t-2 border-gray-300">
                <div className="flex justify-between items-center text-xl font-bold">
                  <span>Total (Subtotal)</span>
                  <span>${items.reduce((sum, item) => sum + ((item.unit_price || (item.price / (item.quantity || 1))) * (item.quantity || 1)), 0).toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Analyze button */}
            {error && (
              <div className="card bg-red-50 border-red-200 mb-4">
                <p className="text-red-800 font-semibold">❌ {error}</p>
              </div>
            )}
            
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="btn-primary btn-large w-full flex items-center justify-center gap-3"
              aria-busy={analyzing}
            >
              {analyzing ? (
                <>
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white" />
                  <span>Analyzing with Gemini AI...</span>
                </>
              ) : (
                <>
                  <FiCheck size={24} />
                  <span>Generate Health Insights</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">Review Instructions</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Check that all items were extracted correctly</li>
            <li>• Edit any incorrect item names or prices</li>
            <li>• Add items that were missed by the scanner</li>
            <li>• Delete any duplicate or incorrect items</li>
            <li>• Click "Generate Health Insights" when ready</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
