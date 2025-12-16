import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import { SessionProvider } from '@/components/providers/SessionProvider'
import { StoreProvider } from '@/components/providers/StoreProvider'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'BrandTruth AI - Launch Ads at Quantum Speed',
  description: 'The First Autonomous Ad Engine. Transform your website into high-performing ads with Quantum Multi-Model Intelligence.',
  keywords: ['advertising', 'ads', 'marketing', 'automation', 'quantum', 'AI'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">
        <SessionProvider>
          <StoreProvider>
            {children}
          </StoreProvider>
        </SessionProvider>
      </body>
    </html>
  )
}
