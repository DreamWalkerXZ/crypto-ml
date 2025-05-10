import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'
import { MainNav } from '@/components/main-nav'
import { Toaster } from "@/components/ui/sonner"

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Crypto ML Platform',
  description: 'A platform for crypto trading with machine learning',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-14 items-center">
              <div className="mr-4 flex">
                <Link href="/" className="mr-6 flex items-center space-x-2">
                  <span className="ml-4 font-bold">Crypto ML Platform</span>
                </Link>
              </div>
              <MainNav />
            </div>
          </header>
          <main className="flex-1 flex justify-center">
            <div className="w-full max-w-[100rem]">
              {children}
            </div>
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  )
}
