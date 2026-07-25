import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Activity, Cpu, MemoryStick, Zap } from 'lucide-react'
import clsx from 'clsx'

export default function MetricsBar() {
  const [sys, setSys] = useState<any>(null)
  const [aura, setAura] = useState<any>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [s, a] = await Promise.all([api.systemMetrics(), api.auraScore()])
        setSys(s); setAura(a)
      } catch {}
    }
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-aura-surface border-b border-aura-border text-xs font-mono">
      {sys && (
        <>
          <MetricChip icon={<Cpu className="w-3 h-3" />} label="CPU" value={`${sys.cpu_percent.toFixed(0)}%`}
            color={sys.cpu_percent > 80 ? 'text-aura-danger' : sys.cpu_percent > 50 ? 'text-aura-warn' : 'text-aura-accent3'} />
          <MetricChip icon={<MemoryStick className="w-3 h-3" />} label="MEM" value={`${sys.memory_percent.toFixed(0)}%`}
            color={sys.memory_percent > 85 ? 'text-aura-danger' : 'text-aura-accent'} />
          <MetricChip icon={<Activity className="w-3 h-3" />} label="UP" value={`${(sys.uptime_seconds / 60).toFixed(0)}m`}
            color="text-aura-muted" />
        </>
      )}
      {aura && (
        <MetricChip
          icon={<Zap className="w-3 h-3" />}
          label="AURA"
          value={(aura.aura_score * 100).toFixed(1) + '%'}
          color={aura.aura_score > 0.7 ? 'text-aura-accent3' : aura.aura_score > 0.4 ? 'text-aura-warn' : 'text-aura-danger'}
        />
      )}
    </div>
  )
}

function MetricChip({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-1.5 text-aura-muted">
      <span className={color}>{icon}</span>
      <span>{label}</span>
      <span className={clsx('font-bold', color)}>{value}</span>
    </div>
  )
}
