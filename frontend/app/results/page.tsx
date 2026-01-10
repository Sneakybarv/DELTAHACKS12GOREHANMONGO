'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FiAlertCircle, FiHeart, FiZap, FiVolume2, FiDownload, FiHome } from 'react-icons/fi'

// Mock health insights data
const mockInsights = {
  allergen_alerts: ['dairy', 'nuts'],
  health_score: 72,
  health_warnings: ['High sugar content in yogurt', 'Processed foods detected'],
  suggestions: [
    'Consider low-sugar alternatives for Greek yogurt',
    'Add more fresh vegetables to your cart',
    'Replace almond butter with sunflower seed butter if nut allergies are a concern',
  ],
  diet_flags: {
    vegetarian_friendly: true,
    vegan_friendly: false,
    gluten_free: false,
    high_protein: true,
    low_sugar: false,
  },
  nutritional_summary:
    'Your grocery haul is moderately healthy with good protein sources but could use more vegetables and less sugar.',
}

export default function ResultsPage() {
  const [speaking, setSpeaking] = useState(false)

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBackground = (score: number) => {
    if (score >= 80) return 'bg-green-100 border-green-300'
    if (score >= 60) return 'bg-yellow-100 border-yellow-300'
    return 'bg-red-100 border-red-300'
  }

  const speakResults = () => {
    const text = `Your health score is ${mockInsights.health_score} out of 100. ${mockInsights.nutritional_summary}. Allergen alerts: ${mockInsights.allergen_alerts.join(', ')}. Health warnings: ${mockInsights.health_warnings.join('. ')}. Suggestions: ${mockInsights.suggestions.join('. ')}`

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.9
      utterance.pitch = 1
      utterance.onstart = () => setSpeaking(true)
      utterance.onend = () => setSpeaking(false)
      window.speechSynthesis.speak(utterance)
    }
  }

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
    }
  }

  const handleDownload = () => {
    // TODO: Generate and download PDF summary
    announceToScreenReader('Downloading summary PDF')
  }

  const announceToScreenReader = (message: string) => {
    const announcer = document.getElementById('a11y-announcer')
    if (announcer) {
      announcer.textContent = message
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Health Insights</h1>
          <div className="flex gap-3">
            <button
              onClick={speaking ? stopSpeaking : speakResults}
              className="btn-primary flex items-center gap-2"
              aria-label={speaking ? 'Stop reading results' : 'Read results aloud'}
            >
              <FiVolume2 size={20} />
              <span>{speaking ? 'Stop' : 'Read Aloud'}</span>
            </button>
          </div>
        </div>

        {/* Health Score */}
        <div className={`card ${getScoreBackground(mockInsights.health_score)} border-2 mb-8`}>
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-4">Your Health Score</h2>
            <div className={`text-7xl font-bold mb-2 ${getScoreColor(mockInsights.health_score)}`}>
              {mockInsights.health_score}
              <span className="text-3xl">/100</span>
            </div>
            <p className="text-lg text-gray-700">{mockInsights.nutritional_summary}</p>
          </div>
        </div>

        {/* Allergen Alerts */}
        <div className="card border-l-4 border-red-500 mb-8">
          <div className="flex items-start gap-4">
            <FiAlertCircle className="text-3xl text-red-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h2 className="text-2xl font-semibold text-red-700 mb-3">Allergen Alerts</h2>
              {mockInsights.allergen_alerts.length > 0 ? (
                <>
                  <p className="text-gray-700 mb-3">
                    The following potential allergens were detected in your items:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {mockInsights.allergen_alerts.map((allergen) => (
                      <span
                        key={allergen}
                        className="px-4 py-2 bg-red-100 text-red-800 rounded-full font-semibold text-lg"
                        role="status"
                        aria-label={`Allergen: ${allergen}`}
                      >
                        {allergen.charAt(0).toUpperCase() + allergen.slice(1)}
                      </span>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-gray-700">No common allergens detected.</p>
              )}
            </div>
          </div>
        </div>

        {/* Health Warnings */}
        <div className="card border-l-4 border-yellow-500 mb-8">
          <div className="flex items-start gap-4">
            <FiHeart className="text-3xl text-yellow-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h2 className="text-2xl font-semibold text-yellow-700 mb-3">Health Warnings</h2>
              {mockInsights.health_warnings.length > 0 ? (
                <ul className="space-y-2" role="list">
                  {mockInsights.health_warnings.map((warning, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-yellow-600 font-bold mt-1">•</span>
                      <span className="text-gray-700 text-lg">{warning}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-700">No health warnings. Great job!</p>
              )}
            </div>
          </div>
        </div>

        {/* Suggestions */}
        <div className="card border-l-4 border-blue-500 mb-8">
          <div className="flex items-start gap-4">
            <FiZap className="text-3xl text-blue-600 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h2 className="text-2xl font-semibold text-blue-700 mb-3">
                Personalized Suggestions
              </h2>
              <ul className="space-y-3" role="list">
                {mockInsights.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-blue-600 font-bold mt-1">✓</span>
                    <span className="text-gray-700 text-lg">{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Diet Flags */}
        <div className="card mb-8">
          <h2 className="text-2xl font-semibold mb-4">Dietary Profile</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(mockInsights.diet_flags).map(([flag, value]) => (
              <div
                key={flag}
                className={`p-4 rounded-lg border-2 text-center ${
                  value
                    ? 'bg-green-50 border-green-300'
                    : 'bg-gray-50 border-gray-300'
                }`}
              >
                <div className="text-2xl mb-1">{value ? '✓' : '✗'}</div>
                <div className="text-sm font-semibold capitalize">
                  {flag.replace(/_/g, ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={handleDownload}
            className="btn-secondary flex-1 flex items-center justify-center gap-2"
          >
            <FiDownload size={20} />
            <span>Download Summary</span>
          </button>

          <Link href="/upload" className="btn-primary flex-1 flex items-center justify-center gap-2">
            <FiHome size={20} />
            <span>Scan Another Receipt</span>
          </Link>

          <Link href="/dashboard" className="btn-primary flex-1 flex items-center justify-center gap-2">
            <span>View Dashboard</span>
          </Link>
        </div>

        {/* Accessibility note */}
        <div className="mt-8 p-4 bg-green-50 rounded-lg border border-green-200">
          <h3 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
            <span>♿</span> Results Summary Saved
          </h3>
          <p className="text-sm text-green-800">
            These insights have been saved to your dashboard. You can review them anytime,
            and we'll track your health score trends over time.
          </p>
        </div>
      </div>
    </div>
  )
}
