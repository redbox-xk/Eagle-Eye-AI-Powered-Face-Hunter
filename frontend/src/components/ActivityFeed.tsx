import { useEffect, useState } from 'react'
import { ws } from '../lib/ws'
import clsx from 'clsx'
import { formatDistanceToNow } from '../lib/time'

interface Event {
  id: string
  type: string
  data: any
  ts: Date
}

export default function ActivityFeed() {
  const [events, setEvents] = useState<Event[]>([])

  useEffect(() => {
    const off = ws.on('*', ({ type, data }) => {
      if (type === 'connection') return
      setEvents(prev => [
        { id: Math.random().toString(36).slice(2), type, data, ts: new Date() },
        ...prev.slice(0, 49),
      ])
    })
    return off
  }, [])

  return (
    <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
      {events.length === 0 && (
        <div className="text-center py-8 text-aura-muted text-xs font-mono">
          Awaiting cognitive events…
        </div>
      )}
      {events.map(e => (
        <div key={e.id} className="flex items-start gap-2 text-xs">
          <span className={clsx('mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5', eventColor(e.type))} />
          <div className="flex-1 min-w-0">
            <span className="font-mono text-aura-muted">{formatDistanceToNow(e.ts)} </span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-aura-accent/70">[{e.type}] </span>
            <span className="text-aura-text/80">{summarize(e)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function eventColor(type: string) {
  if (type.includes('result')) return 'bg-aura-accent3'
  if (type.includes('error')) return 'bg-aura-danger'
  if (type.includes('started')) return 'bg-aura-warn'
  if (type.includes('snapshot')) return 'bg-aura-accent'
  return 'bg-aura-muted'
}

function summarize(e: Event): string {
  if (e.type === 'pipeline_result') {
    const d = e.data
    return `Pipeline complete — AURA ${(d.aura_score * 100).toFixed(0)}% | ${d.agent_outputs?.length ?? 0} agents | ${d.duration_ms?.toFixed(0) ?? '?'}ms`
  }
  if (e.type === 'pipeline_started') return `Task submitted: "${e.data?.task?.slice(0, 60)}"`
  if (e.type === 'state_snapshot') return `System snapshot — ${e.data?.agents?.length ?? 0} agents active`
  return JSON.stringify(e.data).slice(0, 80)
}
