import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import {
  LayoutDashboard, Bot, Brain, Network, GitBranch,
  Activity, Zap, Shield
} from 'lucide-react'
import { ws } from '../lib/ws'
import clsx from 'clsx'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/agents', label: 'Agents', icon: Bot },
  { to: '/reasoning', label: 'Reasoning', icon: GitBranch },
  { to: '/memory', label: 'Memory', icon: Brain },
  { to: '/knowledge', label: 'Knowledge', icon: Network },
]

export default function Layout() {
  const [connected, setConnected] = useState(false)
  const [aura, setAura] = useState<number | null>(null)
  const location = useLocation()

  useEffect(() => {
    const off1 = ws.on('connection', ({ status }) => setConnected(status === 'connected'))
    const off2 = ws.on('state_snapshot', (data) => {
      // extract aura from decisions approval rate as proxy
      const rate = data?.decisions?.approval_rate ?? null
      if (rate !== null) setAura(rate)
    })
    return () => { off1(); off2() }
  }, [])

  return (
    <div className="flex h-screen overflow-hidden grid-bg">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-aura-surface border-r border-aura-border flex flex-col">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-aura-border">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-aura-accent to-aura-accent2 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-mono font-bold text-sm text-aura-accent tracking-wider">AURA-EAGLE</span>
          </div>
          <p className="text-[10px] text-aura-muted font-mono leading-tight">
            Autonomous Unified<br />Reasoning Architecture
          </p>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-aura-accent/10 text-aura-accent border border-aura-accent/20'
                    : 'text-aura-muted hover:text-aura-text hover:bg-white/5'
                )
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Status bar */}
        <div className="px-4 py-3 border-t border-aura-border space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 text-aura-muted font-mono">
              <span className={clsx('status-dot', connected ? 'status-dot-active' : 'status-dot-idle')} />
              {connected ? 'ONLINE' : 'OFFLINE'}
            </div>
            <div className="flex items-center gap-1 text-aura-muted">
              <Shield className="w-3 h-3" />
              <span className="font-mono text-[10px]">SECURE</span>
            </div>
          </div>
          {aura !== null && (
            <div className="text-[10px] font-mono text-aura-muted">
              APPROVAL <span className="text-aura-accent3">{(aura * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
