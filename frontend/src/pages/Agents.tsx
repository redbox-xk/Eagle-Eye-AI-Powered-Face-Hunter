import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import MetricsBar from '../components/MetricsBar'
import AgentCard from '../components/AgentCard'
import { Bot, Send } from 'lucide-react'

export default function Agents() {
  const [agents, setAgents] = useState<any[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [task, setTask] = useState('')
  const [result, setResult] = useState<any>(null)
  const [running, setRunning] = useState(false)

  const load = async () => {
    try {
      const data = await api.listAgents()
      setAgents(data.agents)
    } catch {}
  }

  useEffect(() => {
    load()
    const iv = setInterval(load, 10000)
    return () => clearInterval(iv)
  }, [])

  const runAgent = async (agentId: string) => {
    if (!task.trim()) {
      setSelectedAgent(agentId)
      return
    }
    setRunning(true)
    setSelectedAgent(agentId)
    try {
      const out = await api.runAgent(agentId, task)
      setResult(out)
      await load()
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-2">
          <Bot className="w-5 h-5 text-aura-accent" />
          <h1 className="text-xl font-bold font-mono text-aura-text">Cognitive Agents</h1>
        </div>
        <p className="text-sm text-aura-muted mb-6">ORION supervises NYX · SOL · KADE · MIRA · VEX — each specialized in a reasoning domain</p>

        {/* Direct agent runner */}
        <div className="card mb-6">
          <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-3 flex items-center gap-2">
            <Send className="w-3 h-3" /> Direct Agent Invocation
          </div>
          <div className="flex gap-3">
            <input
              value={task}
              onChange={e => setTask(e.target.value)}
              placeholder="Task to send to selected agent…"
              className="flex-1 bg-aura-bg border border-aura-border rounded-lg px-3 py-2 text-sm font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50"
            />
            {selectedAgent && (
              <button
                onClick={() => runAgent(selectedAgent)}
                disabled={running || !task.trim()}
                className="btn-primary disabled:opacity-40"
              >
                {running ? '…' : `RUN ${selectedAgent.toUpperCase()}`}
              </button>
            )}
          </div>

          {result && (
            <div className="mt-4 space-y-3">
              <div className="p-3 bg-aura-bg rounded-lg border border-aura-border">
                <div className="text-[10px] font-mono text-aura-muted mb-1">CONCLUSION</div>
                <p className="text-sm text-aura-text">{result.conclusion}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-aura-bg rounded-lg border border-aura-border">
                  <div className="text-[10px] font-mono text-aura-muted mb-1">CONFIDENCE</div>
                  <div className="text-xl font-bold font-mono text-aura-accent">{(result.confidence * 100).toFixed(1)}%</div>
                </div>
                <div className="p-3 bg-aura-bg rounded-lg border border-aura-border">
                  <div className="text-[10px] font-mono text-aura-muted mb-1">UNCERTAINTY</div>
                  <div className="text-xl font-bold font-mono text-aura-warn">{(result.uncertainty * 100).toFixed(1)}%</div>
                </div>
              </div>
              {result.evidence?.length > 0 && (
                <div className="p-3 bg-aura-bg rounded-lg border border-aura-border">
                  <div className="text-[10px] font-mono text-aura-muted mb-2">EVIDENCE</div>
                  <ul className="space-y-1">
                    {result.evidence.map((e: string, i: number) => (
                      <li key={i} className="text-xs text-aura-text/80 flex gap-2">
                        <span className="text-aura-accent3 flex-shrink-0">→</span> {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="p-3 bg-aura-bg rounded-lg border border-aura-accent3/20">
                <div className="text-[10px] font-mono text-aura-muted mb-1">RECOMMENDED ACTION</div>
                <p className="text-xs text-aura-accent3">{result.recommended_action}</p>
              </div>
            </div>
          )}
        </div>

        {/* Agent grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map(a => (
            <AgentCard key={a.agent_id} agent={a} onRun={runAgent} />
          ))}
        </div>
      </div>
    </div>
  )
}
