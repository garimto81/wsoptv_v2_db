'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { RefreshCw, Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/', label: 'Dashboard' },
  { href: '/nas', label: 'NAS' },
  { href: '/sync', label: 'Sync' },
  { href: '/catalog', label: 'Catalog' },
]

export function Header() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 w-full border-b border-zinc-800 bg-zinc-950/95 backdrop-blur supports-[backdrop-filter]:bg-zinc-950/80">
      <div className="container flex h-14 items-center px-4">
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <Database className="h-6 w-6 text-emerald-500" />
          <span className="font-bold text-lg">PokerVOD Quality</span>
        </Link>

        <nav className="flex items-center space-x-6 text-sm font-medium">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'transition-colors hover:text-foreground/80',
                pathname === item.href ||
                  (item.href !== '/' && pathname.startsWith(item.href))
                  ? 'text-emerald-500'
                  : 'text-foreground/60'
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center space-x-4">
          <Button variant="ghost" size="icon" title="Refresh all data">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
