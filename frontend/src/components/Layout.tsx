/**
 * Main layout component
 */
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Aurix</h1>
        </div>
      </nav>
      <main className="container mx-auto">
        {children}
      </main>
    </div>
  )
}
