'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  HardDrive,
  RefreshCcw,
  Link2,
  FileWarning,
  Copy,
  AlertTriangle,
  History,
  GitBranch,
  Unlink,
  BarChart3,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  children?: NavItem[]
}

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  {
    href: '/nas',
    label: 'NAS Inventory',
    icon: HardDrive,
    children: [
      { href: '/nas/unlinked', label: 'Unlinked Files', icon: FileWarning },
      { href: '/nas/duplicates', label: 'Duplicates', icon: Copy },
    ],
  },
  {
    href: '/sync',
    label: 'Sheets Sync',
    icon: RefreshCcw,
    children: [
      { href: '/sync/errors', label: 'Errors', icon: AlertTriangle },
      { href: '/sync/history', label: 'History', icon: History },
    ],
  },
  {
    href: '/catalog',
    label: 'Catalog Linkage',
    icon: Link2,
    children: [
      { href: '/catalog/hierarchy', label: 'Hierarchy', icon: GitBranch },
      { href: '/catalog/orphans', label: 'Orphans', icon: Unlink },
      { href: '/catalog/stats', label: 'Statistics', icon: BarChart3 },
    ],
  },
]

function NavLink({
  item,
  isActive,
}: {
  item: NavItem
  isActive: boolean
}) {
  const Icon = item.icon

  return (
    <Link
      href={item.href}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all',
        isActive
          ? 'bg-emerald-500/10 text-emerald-500'
          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
      )}
    >
      <Icon className="h-4 w-4" />
      {item.label}
    </Link>
  )
}

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden lg:flex w-64 flex-col border-r border-zinc-800 bg-zinc-950">
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href))

          return (
            <div key={item.href}>
              <NavLink item={item} isActive={isActive && !item.children} />
              {item.children && (
                <div className="ml-4 mt-1 space-y-1">
                  {item.children.map((child) => (
                    <NavLink
                      key={child.href}
                      item={child}
                      isActive={pathname === child.href}
                    />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </nav>
    </aside>
  )
}
