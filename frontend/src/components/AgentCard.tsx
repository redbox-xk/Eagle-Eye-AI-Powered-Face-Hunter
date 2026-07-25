import clsx from 'clsx'
import { Cpu, AlertTriangle, Clock, CheckCircle } from 'lucide-react'

const AGENT_COLORS: Record<string, { accent: string; bg: string; border: string }> = {
  orion: { accent: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/20' },
  nyx:   { accent: 'text-purple-400', bg: 'bg-purple-400/10', border: 'border-purple-400/20' },
  sol:   { accent: 'text-amber-400',  bg: 'bg-amber-400/10',  border: 'border-amber-400/20'  },
  kade:  { accent: 'text-cyan-400',   bg: 'bg-cyan-400/10',   border: 'border-cyan-400/20'   },
  mira:  { accent: 'text-rose-400',   bg: 'bg-rose-400/10',   border: 'border-rose-400/20'   },
  vex:   { accent: 'text-green-400',  bg: 'bg-green-400/10',  border: 'border-green-400/20'  },
}

interface Props {
  agent: {
    agent_id: string
    display_name: string
    domain: string
    description: string
    invocations: number
    errors: number
    avg_latency_ms: number
    last_confidence: number | null
    last_conclusion: string | null
  }
  onRun?: (id: string) => void
}

export default function AgentCard({ agent, onRun }: Props) {
  const colors = AGENT_COLORS[agent.agent_id] || AGENT_COLORS.nyx
  const errorRate = agent.invocations > 0 ? agent.errors / agent.invocations : 0
  const health = errorRate < 0.05 ? 'nominal' : errorRate < 0.2 ? 'degraded' : 'critical'

  return (
    <div className={clsx('card border transition-all duration-200 hover:glow-cyan', colors.border)}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className={clsx('text-lg font-bold font-mono', colors.accent)}>{agent.display_name}</div>
          <div className="text-xs text-aura-muted uppercase tracking-widest font-mono">{agent.domain}</div>
        </div>
        <div className={clsx(
          'px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase',
          health === 'nominal' ? 'bg-green-400/10 text-green-400' :
          health === 'degraded' ? 'bg-yellow-400/10 text-yellow-400' :
          'bg-red-400/10 text-red-400'
        )}>
          {health}
        </div>
      </div>

      <p className="text-xs text-aura-muted mb-4 leading-relaxed">{agent.description}</p>

      <div className="grid grid-cols-3 gap-2 mb-3">
        <Stat label="Invocations" value={agent.invocations} icon={<Cpu className="w-3 h-3" />} />
        <Stat label="Errors" value={agent.errors} icon={<AlertTriangle className="w-3 h-3" />} warn={agent.errors > 0} />
        <Stat label="Avg ms" value={agent.avg_latency_ms.toFixed(0)} icon={<Clock className="w-3 h-3" />} />
      </div>

      {agent.last_confidence !== null && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-aura-muted font-mono">CONFIDENCE</span>
            <span className={clsx('font-mono font-bold', colors.accent)}>
              {(agent.last_confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1.5 bg-aura-border rounded-full overflow-hidden">
            <div
              className={clsx('h-full rounded-full transition-all duration-500', colors.bg.replace('/10', '/60'))}
              style={{ width: `${agent.last_confidence * 100}%` }}
            />
          </div>
        </div>
      )}

      {agent.last_conclusion && (
        <p className="text-[11px] text-aura-muted italic truncate mb-3">
          "{agent.last_conclusion}"
        </p>
      )}

      {onRun && (
        <button
          onClick={() => onRun(agent.agent_id)}
          className={clsx('w-full py-1.5 rounded-lg text-xs font-mono font-medium transition-all duration-200 border', colors.border, colors.accent, colors.bg, 'hover:opacity-80')}
        >
          RUN AGENT
        </button>
      )}
    </div>
  )
}

function Stat({ label, value, icon, warn }: { label: string; value: any; icon: React.ReactNode; warn?: boolean }) {
  return (
    <div className="bg-aura-bg rounded-lg p-2 text-center">
      <div className={clsx('flex items-center justify-center gap-1 mb-1', warn && value > 0 ? 'text-yellow-400' : 'text-aura-muted')}>
        {icon}
      </div>
      <div className={clsx('font-mono font-bold text-sm', warn && value > 0 ? 'text-yellow-400' : 'text-aura-text')}>
        {value}
      </div>
      <div className="text-[9px] text-aura-muted uppercase tracking-wider font-mono">{label}</div>
    </div>
  )
}
