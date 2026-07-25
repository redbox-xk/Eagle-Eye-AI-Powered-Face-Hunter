import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import MetricsBar from '../components/MetricsBar'
import { GitBranch, Play, Shield, TrendingUp, CheckCircle, XCircle, Clock } from 'lucide-react'
import clsx from 'clsx'
import { formatMs } from '../lib/time'

const STAGE_ICONS: Record<string, string> = {
  'Understand Objective': '🎯',
  'Retrieve Memory': '🧠',
  'Knowledge Graph Query': '🕸',
  'ORION: Task Decomposition': '🔱',
  'Specialist Agent Ensemble': '⚡',
  'Simulation Engine': '🔮',
  'Critic Review': '🔍',
  'Risk Analysis': '⚠',
  'Governance Check': '🛡',
  'Decision Engine': '⚖',
  'Update Memory': '💾',
}

export default function Reasoning() {
  const [history, setHistory] = useState<any[]>([])
  const [decisions, setDecisions] = useState<any>(null)
  const [selected, setSelected] = useState<any>(null)
  const [task, setTask] = useState('')
  const [running, setRunning] = useState(false)
  const [simTask, setSimTask] = useState('')
  const [simResult, setSimResult] = useState<any>(null)

  const load = async () => {
    try {
      const [h, d] = await Promise.all([api.pipelineHistory(10), api.decisions()])
      setHistory(h.history || [])
      setDecisions(d)
    } catch {}
  }

  useEffect(() => { load() }, [])

  const runPipeline = async () => {
    if (!task.trim() || running) return
    setRunning(true)
    try {
      const result = await api.runPipeline(task)
      setSelected(result)
      await load()
    } finally {
      setRunning(false)
    }
  }

  const runSimulation = async () => {
    if (!simTask.trim()) return
    const r = await api.simulate(simTask)
    setSimResult(r)
  }

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-2">
          <GitBranch className="w-5 h-5 text-aura-accent" />
          <h1 className="text-xl font-bold font-mono">Reasoning Pipeline</h1>
        </div>
        <p className="text-sm text-aura-muted mb-6">
          11-stage cognitive pipeline: Understand → Memory → KG → ORION → Agents → Simulate → Critic → Risk → Governance → Decide → Update
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: run + history */}
          <div className="space-y-4">
            {/* Runner */}
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <Play className="w-3 h-3 text-aura-accent" />
                <span className="text-xs font-mono text-aura-muted uppercase tracking-widest">Run Pipeline</span>
              </div>
              <textarea
                value={task}
                onChange={e => setTask(e.target.value)}
                placeholder="Describe a task for the pipeline…"
                rows={3}
                className="w-full bg-aura-bg border border-aura-border rounded-lg px-3 py-2 text-sm font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50 resize-none mb-2"
              />
              <button onClick={runPipeline} disabled={running || !task.trim()} className="btn-primary w-full justify-center disabled:opacity-40">
                {running ? <><span className="w-3 h-3 border border-aura-accent border-t-transparent rounded-full animate-spin" /> Running…</> : 'EXECUTE'}
              </button>
            </div>

            {/* Decision Stats */}
            {decisions && (
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-3 h-3 text-aura-accent3" />
                  <span className="text-xs font-mono text-aura-muted uppercase tracking-widest">Decision Stats</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Total', value: decisions.stats?.total ?? 0 },
                    { label: 'Approved', value: decisions.stats?.approved ?? 0 },
                    { label: 'Approval %', value: `${((decisions.stats?.approval_rate ?? 0) * 100).toFixed(0)}%` },
                    { label: 'Avg Score', value: (decisions.stats?.avg_score ?? 0).toFixed(2) },
                  ].map(m => (
                    <div key={m.label} className="bg-aura-bg rounded-lg p-2 text-center">
                      <div className="font-mono font-bold text-aura-text">{m.value}</div>
                      <div className="text-[10px] font-mono text-aura-muted uppercase">{m.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* History list */}
            <div className="card">
              <div className="text-xs font-mono text-aura-muted uppercase tracking-widest mb-2">History</div>
              <div className="space-y-1.5 max-h-64 overflow-y-auto">
                {history.length === 0 && <div className="text-xs text-aura-muted font-mono text-center py-4">No runs yet</div>}
                {history.map((r: any) => (
                  <button
                    key={r.task_id}
                    onClick={() => setSelected(r)}
                    className={clsx(
                      'w-full text-left p-2 rounded-lg border transition-all text-xs',
                      selected?.task_id === r.task_id
                        ? 'border-aura-accent/40 bg-aura-accent/5'
                        : 'border-aura-border hover:border-aura-accent/20 bg-aura-bg'
                    )}
                  >
                    <div className="font-mono text-aura-text/80 truncate">{r.task}</div>
                    <div className="flex items-center gap-2 mt-0.5 text-aura-muted font-mono">
                      <span className={clsx('text-[10px]', r.aura_score > 0.6 ? 'text-aura-accent3' : 'text-aura-warn')}>
                        AURA {(r.aura_score * 100).toFixed(0)}%
                      </span>
                      <span className="text-[10px]">{formatMs(r.duration_ms)}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right: detail */}
          <div className="lg:col-span-2 space-y-4">
            {selected ? (
              <>
                {/* Pipeline stages */}
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-xs font-mono text-aura-muted uppercase tracking-widest">Pipeline Stages</div>
                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className="text-aura-muted">AURA</span>
                      <span className="text-aura-accent font-bold">{(selected.aura_score * 100).toFixed(1)}%</span>
                      <span className="text-aura-muted">{formatMs(selected.duration_ms)}</span>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    {selected.stages?.map((s: any) => (
                      <div key={s.name} className={clsx(
                        'flex items-start gap-3 p-2 rounded-lg text-xs',
                        s.status === 'complete' ? 'bg-aura-accent3/5 border border-aura-accent3/10' :
                        s.status === 'failed' ? 'bg-aura-danger/5 border border-aura-danger/20' :
                        'bg-aura-bg border border-aura-border'
                      )}>
                        <span className="text-base leading-none">{STAGE_ICONS[s.name] || '○'}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            {s.status === 'complete'
                              ? <CheckCircle className="w-3 h-3 text-aura-accent3 flex-shrink-0" />
                              : <XCircle className="w-3 h-3 text-aura-danger flex-shrink-0" />}
                            <span className="font-mono font-medium text-aura-text">{s.name}</span>
                            <span className="text-aura-muted flex items-center gap-0.5 ml-auto">
                              <Clock className="w-2.5 h-2.5" />{s.duration_ms.toFixed(0)}ms
                            </span>
                          </div>
                          {s.result_summary && (
                            <div className="text-[11px] text-aura-muted mt-0.5 ml-5">{s.result_summary}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Agent outputs */}
                <div className="card">
                  <div className="text-xs font-mono text-aura-muted uppercase tracking-widest mb-3">Agent Outputs</div>
                  <div className="space-y-2">
                    {selected.agent_outputs?.map((o: any, i: number) => (
                      <div key={i} className="p-2 bg-aura-bg rounded-lg border border-aura-border">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-mono font-bold text-aura-accent">{o.agent_id.toUpperCase()}</span>
                          <span className="text-[10px] font-mono text-aura-muted">
                            conf:{(o.confidence * 100).toFixed(0)}% · {o.duration_ms.toFixed(0)}ms
                          </span>
                        </div>
                        <p className="text-xs text-aura-text/80">{o.conclusion}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Decision */}
                {selected.decision && (
                  <div className={clsx(
                    'card border',
                    selected.decision.approved ? 'border-aura-accent3/30' : 'border-aura-warn/30'
                  )}>
                    <div className="flex items-center gap-2 mb-3">
                      <Shield className="w-4 h-4 text-aura-accent" />
                      <span className="text-xs font-mono text-aura-muted uppercase tracking-widest">Decision</span>
                      <span className={clsx(
                        'ml-auto badge font-mono',
                        selected.decision.approved
                          ? 'bg-aura-accent3/10 text-aura-accent3'
                          : 'bg-aura-warn/10 text-aura-warn'
                      )}>
                        {selected.decision.approved ? '✓ APPROVED' : '⚠ PENDING REVIEW'}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {['score', 'confidence', 'risk'].map(k => (
                        <div key={k} className="bg-aura-bg rounded-lg p-2 text-center">
                          <div className="font-mono font-bold text-sm text-aura-text">
                            {(selected.decision[k] * (k === 'score' ? 1 : 100)).toFixed(k === 'score' ? 3 : 0)}{k === 'score' ? '' : '%'}
                          </div>
                          <div className="text-[10px] font-mono text-aura-muted uppercase">{k}</div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-aura-accent3">{selected.decision.recommended_action}</p>
                  </div>
                )}
              </>
            ) : (
              <>
                {/* Simulation panel when nothing selected */}
                <div className="card">
                  <div className="text-xs font-mono text-aura-muted uppercase tracking-widest mb-3 flex items-center gap-2">
                    <span>🔮</span> Simulation Engine
                  </div>
                  <div className="flex gap-2 mb-4">
                    <input
                      value={simTask}
                      onChange={e => setSimTask(e.target.value)}
                      placeholder="Task to simulate…"
                      className="flex-1 bg-aura-bg border border-aura-border rounded-lg px-3 py-1.5 text-sm font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50"
                      onKeyDown={e => e.key === 'Enter' && runSimulation()}
                    />
                    <button onClick={runSimulation} className="btn-primary">Simulate</button>
                  </div>
                  {simResult && (
                    <div className="space-y-2">
                      <div className="text-xs font-mono text-aura-accent mb-2">→ {simResult.recommendation}</div>
                      {simResult.scenarios?.map((s: any) => (
                        <div key={s.name} className={clsx(
                          'p-3 rounded-lg border',
                          simResult.optimal?.name === s.name ? 'border-aura-accent3/40 bg-aura-accent3/5' : 'border-aura-border bg-aura-bg'
                        )}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-mono font-medium text-aura-text">{s.name}</span>
                            <span className="text-xs font-mono text-aura-accent">EV {s.expected_value.toFixed(3)}</span>
                          </div>
                          <div className="flex gap-3 text-[10px] font-mono text-aura-muted">
                            <span>P={( s.probability * 100).toFixed(0)}%</span>
                            <span>Benefit={( s.benefit * 100).toFixed(0)}%</span>
                            <span>Risk={( s.risk * 100).toFixed(0)}%</span>
                          </div>
                          <div className="mt-1.5 h-1 bg-aura-border rounded-full overflow-hidden">
                            <div className="h-full bg-aura-accent/50 rounded-full" style={{ width: `${s.expected_value * 100}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {!simResult && (
                    <div className="text-center py-8 text-aura-muted text-sm font-mono">
                      Run a pipeline or simulation to see results
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
