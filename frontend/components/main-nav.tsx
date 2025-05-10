"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

export function MainNav() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    if (path === "/") {
      return pathname === path
    }
    return pathname.startsWith(path)
  }

  return (
    <nav className="flex items-center space-x-1 text-sm font-medium">
      <Link 
        href="/dashboard" 
        className={`rounded-md px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
          isActive("/dashboard") ? "bg-accent text-accent-foreground" : "text-muted-foreground"
        }`}
      >
        Dashboard
      </Link>
      <Link 
        href="/data" 
        className={`rounded-md px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
          isActive("/data") ? "bg-accent text-accent-foreground" : "text-muted-foreground"
        }`}
      >
        Data Management
      </Link>
      <Link 
        href="/backtest" 
        className={`rounded-md px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
          isActive("/backtest") ? "bg-accent text-accent-foreground" : "text-muted-foreground"
        }`}
      >
        Backtest
      </Link>
      <Link 
        href="/results" 
        className={`rounded-md px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
          isActive("/results") ? "bg-accent text-accent-foreground" : "text-muted-foreground"
        }`}
      >
        Results
      </Link>
      <Link 
        href="/models" 
        className={`rounded-md px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
          isActive("/models") ? "bg-accent text-accent-foreground" : "text-muted-foreground"
        }`}
      >
        Models
      </Link>
    </nav>
  )
} 