'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { FiEdit2, FiCheck, FiTrash2, FiPlus } from 'react-icons/fi'

// Mock data - will be replaced with real API data
const mockReceiptData = {
  merchant: "Whole Foods Market",
  date: "2026-01-10",
  items: [
    { name: "Organic Milk", price: 4.99, category: "dairy" },
    { name: "Almond Butter", price: 8.99, category: "nuts" },
    { name: "Whole Wheat Bread", price: 3.49, category: "grains" },
    { name: "Fresh Strawberries", price: 5.99, category: "produce" },
    { name: "Greek Yogurt", price: 6.49, category: "dairy" },
  ],
  total: 29.95,
}

export default function ReviewPage() {
  const router = useRouter()
  const [items, setItems] = useState(mockReceiptData.items)
  const [merchant, setMerchant] = useState(mockReceiptData.merchant)
  const [date, setDate] = useState(mockReceiptData.date)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editPrice, setEditPrice] = useState('')

  const startEdit = (index: number) => {
    setEditingIndex(index)
    setEditName(items[index].name)
    setEditPrice(items[index].price.toString())
  }

  const saveEdit = () => {
    if (editingIndex !== null) {
      const updatedItems = [...items]
      updatedItems[editingIndex] = {
        ...updatedItems[editingIndex],
        name: editName,
        price: parseFloat(editPrice) || 0,
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
    setItems([...items, { name: 'New Item', price: 0, category: 'other' }])
    announceToScreenReader('New item added')
  }

  const handleAnalyze = () => {
    announceToScreenReader('Analyzing receipt for health insights')
    router.push('/results')
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
            <div className="bg-gray-200 rounded-lg aspect-[3/4] flex items-center justify-center text-gray-500">
              <span>Receipt Preview</span>
            </div>
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
                          <input
                            type="number"
                            step="0.01"
                            value={editPrice}
                            onChange={(e) => setEditPrice(e.target.value)}
                            className="input"
                            placeholder="Price"
                            aria-label="Item price"
                          />
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
                          <div className="text-gray-600">${item.price.toFixed(2)}</div>
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
                  <span>Total</span>
                  <span>${items.reduce((sum, item) => sum + item.price, 0).toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Analyze button */}
            <button
              onClick={handleAnalyze}
              className="btn-primary btn-large w-full flex items-center justify-center gap-3"
            >
              <FiCheck size={24} />
              <span>Generate Health Insights</span>
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
