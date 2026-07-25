import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { ws } from '../lib/ws'
import MetricsBar from '../components/MetricsBar'
import ActivityFeed from '../components/ActivityFeed'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PolarAngleAxis
} from 'recharts'
import { Brain, Network, Cpu, CheckCircle, AlertOctagon, Layers, Zap } from 'lucide-react'
import clsx from 'clsx'

export default function Dashboard() {
  const [overview, setOverview] = useState<any>(null)
  const [aura, setAura] = useState<any>(null)
  const [history, setHistory] = useState<any[]>([])
  const [task, setTask] = useState('')
  const [running, setRunning] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)

  const load = async () => {
    try {
      const [ov, au] = await Promise.all([api.overview(), api.auraScore()])
      setOverview(ov); setAura(au)
    } catch {}
  }

  useEffect(() => {
    load()
    const iv = setInterval(load, 8000)
    const off = ws.on('pipeline_result', (data) => {
      setLastResult(data)
      setRunning(false)
      setHistory(h => [{ score: (data.aura_score * 100).toFixed(0), time: new Date().toLocaleTimeString() }, ...h.slice(0, 19)].reverse())
      load()
    })
    return () => { clearInterval(iv); off() }
  }, [])

  const submitTask = async () => {
    if (!task.trim() || running) return
    setRunning(true)
    ws.send('run_pipeline', { task })
  }

  const auraScore = aura?.aura_score ?? 0
  const radialData = [{ name: 'AURA', value: Math.round(auraScore * 100) }]

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="flex-1 p-6 overflow-y-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-aura-text font-mono">
            <span className="text-aura-accent">PROJECT</span> AURA-EAGLE
          </h1>
          <p className="text-aura-muted text-sm mt-1">
            Autonomous Unified Reasoning Architecture · Enhanced Adaptive Graph Learning Engine
          </p>
        </div>

        {/* Top KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiCard
            icon={<Layers className="w-5 h-5" />}
            label="Memory Entries"
            value={overview ? Object.values(overview.memory?.layers ?? {}).reduce((a: any, b: any) => a + b, 0) : '—'}
            color="text-aura-accent"
          />
          <KpiCard
            icon={<Network className="w-5 h-5" />}
            label="KG Nodes"
            value={overview?.knowledge_graph?.node_count ?? '—'}
            color="text-aura-accent2"
          />
          <KpiCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="Decisions Made"
            value={overview?.decisions?.total ?? '—'}
            color="text-aura-accent3"
          />
          <KpiCard
            icon={<Cpu className="w-5 h-5" />}
            label="Pipeline Runs"
            value={overview?.pipeline_runs ?? '—'}
            color="text-aura-warn"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* AURA Score Radial */}
          <div className="card glow-cyan">
            <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-2">AURA Score</div>
            <div className="flex items-center justify-center h-40">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%" cy="50%"
                  innerRadius="60%" outerRadius="90%"
                  startAngle={90} endAngle={-270}
                  data={radialData}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                  <RadialBar
                    dataKey="value"
                    angleAxisId={0}
                    cornerRadius={8}
                    fill={auraScore > 0.7 ? '#10b981' : auraScore > 0.4 ? '#f59e0b' : '#ef4444'}
                    background={{ fill: '#1a2744' }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center -mt-4">
              <div className="text-3xl font-bold font-mono text-aura-accent">{(auraScore * 100).toFixed(1)}<span className="text-lg text-aura-muted">%</span></div>
              <div className="text-[10px] text-aura-muted font-mono">Intelligence × Reliability / Cost × Risk</div>
            </div>
          </div>

          {/* AURA History Chart */}
          <div className="card col-span-1 lg:col-span-2">
            <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-3">AURA Score History</div>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="auraGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" tick={{ fontSize: 9, fill: '#64748b' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ background: '#0b1220', border: '1px solid #1a2744', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: '#64748b' }}
                />
                <Area type="monotone" dataKey="score" stroke="#00d4ff" fill="url(#auraGrad)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Task Runner */}
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-aura-accent" />
              <span className="text-xs text-aura-muted font-mono uppercase tracking-widest">Cognitive Pipeline</span>
            </div>
            <textarea
              value={task}
              onChange={e => setTask(e.target.value)}
              placeholder="Submit a task to the reasoning pipeline…"
              rows={3}
              className="w-full bg-aura-bg border border-aura-border rounded-lg px-3 py-2 text-sm text-aura-text placeholder-aura-muted resize-none focus:outline-none focus:border-aura-accent/50 font-mono mb-3"
              onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) submitTask() }}
            />
            <button
              onClick={submitTask}
              disabled={running || !task.trim()}
              className="btn-primary w-full justify-center disabled:opacity-40"
            >
              {running ? (
                <><span className="w-3 h-3 border border-aura-accent border-t-transparent rounded-full animate-spin" /> Processing…</>
              ) : 'EXECUTE PIPELINE ⌘↵'}
            </button>

            {lastResult && (
              <div className="mt-3 p-3 bg-aura-bg rounded-lg border border-aura-accent3/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-aura-accent3 uppercase">Last Result</span>
                  <span className="text-xs font-mono text-aura-muted">{lastResult.duration_ms?.toFixed(0)}ms</span>
                </div>
                <div className="text-xs text-aura-text">
                  {lastResult.agent_outputs?.[0]?.conclusion?.slice(0, 200)}
                </div>
                <div className="mt-2 flex gap-2 flex-wrap">
                  {lastResult.stages?.filter((s: any) => s.status === 'complete').map((s: any) => (
                    <span key={s.name} className="badge bg-aura-accent3/10 text-aura-accent3">{s.name}</span>
                  ))}
                  {lastResult.stages?.filter((s: any) => s.status === 'failed').map((s: any) => (
                    <span key={s.name} className="badge bg-aura-danger/10 text-aura-danger">{s.name}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Activity Feed */}
          <div className="card">
            <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-3">Live Event Stream</div>
            <ActivityFeed />
          </div>
        </div>

        {/* Components overview */}
        {aura && (
          <div className="card">
            <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-4">AURA Score Decomposition</div>
            <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(aura.components).map(([key, val]: [string, any]) => (
                <div key={key} className="text-center">
                  <div className="text-lg font-bold font-mono text-aura-text">{(val * 100).toFixed(0)}<span className="text-xs text-aura-muted">%</span></div>
                  <div className="text-[10px] text-aura-muted uppercase tracking-wider font-mono mt-0.5">{key}</div>
                  <div className="mt-1.5 h-1 bg-aura-border rounded-full overflow-hidden">
                    <div className="h-full bg-aura-accent/60 rounded-full" style={{ width: `${val * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function KpiCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: any; color: string }) {
  return (
    <div className="card flex items-center gap-3">
      <div className={clsx('p-2 rounded-lg bg-white/5', color)}>{icon}</div>
      <div>
        <div className="metric-value">{value}</div>
        <div className="metric-label">{label}</div>
      </div>
    </div>
  )
}
