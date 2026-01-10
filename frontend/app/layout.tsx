import type { Metadata } from 'next'
import './globals.css'
import AccessibilityToolbar from '@/components/AccessibilityToolbar'

export const metadata: Metadata = {
  title: 'Receipt Scanner - Accessible Health Insights',
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
      </body>
    </html>
  )
}
