import type { Metadata } from 'next'
import './globals.css'
import AccessibilityToolbar from '@/components/AccessibilityToolbar'
import { ReceiptProvider } from '@/contexts/ReceiptContext'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata: Metadata = {
  title: 'BiteWise - Accessible Health Insights',
  description: 'Turn receipts into health insights with full accessibility support',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ReceiptProvider>
            {/* Skip to main content link for keyboard users */}
            <a href="#main-content" className="skip-to-main">
              Skip to main content
            </a>

            {/* Accessibility toolbar */}
            <AccessibilityToolbar />

            {/* Main content */}
            <main id="main-content" className="min-h-screen">
              {children}
            </main>

            {/* Screen reader announcements */}
            <div
              role="status"
              aria-live="polite"
              aria-atomic="true"
              className="sr-only"
              id="a11y-announcer"
            />
          </ReceiptProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
