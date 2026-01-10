'use client'

import Link from 'next/link'
import { FiCamera, FiPieChart, FiHeart, FiVolumeX, FiVolume2 } from 'react-icons/fi'
import { useState } from 'react'

export default function Home() {
  const [speaking, setSpeaking] = useState(false)

  const speakText = (text: string) => {
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

  const pageDescription = "Receipt Scanner. An accessible tool that turns food receipts into health insights. Upload any grocery or restaurant receipt. We flag allergens, highlight nutrition risks, and summarize your week."

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header with read-aloud button */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900">
            Receipt Scanner
          </h1>
          <button
            onClick={() => speaking ? stopSpeaking() : speakText(pageDescription)}
            className="btn-primary flex items-center gap-2"
            aria-label={speaking ? "Stop reading page" : "Read page aloud"}
          >
            {speaking ? <FiVolumeX size={24} /> : <FiVolume2 size={24} />}
            <span>{speaking ? 'Stop' : 'Read Aloud'}</span>
          </button>
        </div>

        {/* Hero section */}
        <section className="text-center mb-16">
          <h2 className="text-3xl font-semibold text-gray-800 mb-4">
            Turn food receipts into health insights
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Upload any grocery or restaurant receipt. We flag allergens,
            highlight nutrition risks, and summarize your week.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/upload" className="btn-primary btn-large flex items-center gap-3">
              <FiCamera size={28} />
              <span>Scan Receipt</span>
            </Link>
            <Link href="/dashboard" className="btn-secondary btn-large flex items-center gap-3">
              <FiPieChart size={28} />
              <span>View Dashboard</span>
            </Link>
          </div>
        </section>

        {/* How it works */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-10">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="card text-center">
              <div className="text-5xl mb-4">📸</div>
              <h3 className="text-xl font-semibold mb-2">1. Upload</h3>
              <p className="text-gray-600">
                Take a photo or upload an image of your receipt
              </p>
            </div>

            <div className="card text-center">
              <div className="text-5xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold mb-2">2. Read</h3>
              <p className="text-gray-600">
                AI extracts items, prices, and store information
              </p>
            </div>

            <div className="card text-center">
              <div className="text-5xl mb-4">🧬</div>
              <h3 className="text-xl font-semibold mb-2">3. Analyze</h3>
              <p className="text-gray-600">
                Detect allergens, nutrition risks, and health patterns
              </p>
            </div>

            <div className="card text-center">
              <div className="text-5xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">4. Insights</h3>
              <p className="text-gray-600">
                Get personalized health insights and suggestions
              </p>
            </div>
          </div>
        </section>

        {/* Features - Accessibility focused */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-10">
            Built for Everyone
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card">
              <div className="text-4xl mb-4">♿</div>
              <h3 className="text-xl font-semibold mb-3">Fully Accessible</h3>
              <ul className="text-gray-600 space-y-2">
                <li>✓ Screen reader support</li>
                <li>✓ Keyboard navigation</li>
                <li>✓ High contrast mode</li>
                <li>✓ Large text options</li>
                <li>✓ Voice commands</li>
              </ul>
            </div>

            <div className="card">
              <FiHeart className="text-4xl mb-4 text-red-500" />
              <h3 className="text-xl font-semibold mb-3">Health First</h3>
              <ul className="text-gray-600 space-y-2">
                <li>✓ Allergen alerts</li>
                <li>✓ Nutrition analysis</li>
                <li>✓ Custom dietary tracking</li>
                <li>✓ Health score trends</li>
                <li>✓ Smart suggestions</li>
              </ul>
            </div>

            <div className="card">
              <div className="text-4xl mb-4">🔒</div>
              <h3 className="text-xl font-semibold mb-3">Privacy First</h3>
              <ul className="text-gray-600 space-y-2">
                <li>✓ No bank account access</li>
                <li>✓ You control your data</li>
                <li>✓ Local processing option</li>
                <li>✓ Delete anytime</li>
                <li>✓ No data selling</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Example alerts */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-10">
            Example Insights
          </h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* Allergen alert example */}
            <div className="card border-l-4 border-red-500">
              <div className="flex items-start gap-4">
                <div className="text-3xl">⚠️</div>
                <div>
                  <h3 className="text-lg font-semibold text-red-700 mb-2">
                    Allergen Alert
                  </h3>
                  <p className="text-gray-700 mb-2">
                    May contain: <strong>Peanuts, Dairy</strong>
                  </p>
                  <p className="text-sm text-gray-600">
                    Found in 3 items from your last grocery trip
                  </p>
                </div>
              </div>
            </div>

            {/* Health warning example */}
            <div className="card border-l-4 border-yellow-500">
              <div className="flex items-start gap-4">
                <div className="text-3xl">🍬</div>
                <div>
                  <h3 className="text-lg font-semibold text-yellow-700 mb-2">
                    High Sugar Warning
                  </h3>
                  <p className="text-gray-700 mb-2">
                    Your cart has <strong>40% more sugar</strong> than recommended
                  </p>
                  <p className="text-sm text-gray-600">
                    Try: Low-sugar yogurt, unsweetened drinks
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center">
          <div className="card bg-blue-600 text-white max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
            <p className="text-xl mb-6">
              Scan your first receipt and discover your health insights
            </p>
            <Link href="/upload" className="inline-block bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors">
              Scan Now
            </Link>
          </div>
        </section>
      </div>
    </div>
  )
}
