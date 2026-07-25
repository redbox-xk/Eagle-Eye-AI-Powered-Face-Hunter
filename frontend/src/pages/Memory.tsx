import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import MetricsBar from '../components/MetricsBar'
import { Brain, Plus, Search } from 'lucide-react'
import clsx from 'clsx'

const LAYERS = ['sensory', 'working', 'semantic', 'episodic', 'causal']

const LAYER_META: Record<string, { color: string; desc: string }> = {
  sensory:  { color: 'text-red-400 border-red-400/20 bg-red-400/5',    desc: 'Raw ephemeral data (TTL 30s)' },
  working:  { color: 'text-yellow-400 border-yellow-400/20 bg-yellow-400/5', desc: 'Active reasoning window' },
  semantic: { color: 'text-blue-400 border-blue-400/20 bg-blue-400/5',  desc: 'Long-term facts & concepts' },
  episodic: { color: 'text-purple-400 border-purple-400/20 bg-purple-400/5', desc: 'Event history' },
  causal:   { color: 'text-green-400 border-green-400/20 bg-green-400/5',  desc: 'Why-relationships' },
}

export default function Memory() {
  const [stats, setStats] = useState<any>(null)
  const [layers, setLayers] = useState<any>({})
  const [activeLayer, setActiveLayer] = useState('episodic')
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState<any[]>([])
  const [form, setForm] = useState({ content: '', layer: 'semantic', tags: '' })

  const load = async () => {
    try {
      const [s, l] = await Promise.all([api.memoryStats(), api.memoryLayers()])
      setStats(s); setLayers(l)
    } catch {}
  }

  useEffect(() => { load(); const iv = setInterval(load, 6000); return () => clearInterval(iv) }, [])

  const search = async () => {
    if (!query.trim()) return
    const tags = query.split(/\s+/)
    const r = await api.retrieveMemory(tags)
    setQueryResult(r.entries)
  }

  const store = async () => {
    if (!form.content) return
    let parsed: any
    try { parsed = JSON.parse(form.content) } catch { parsed = { text: form.content } }
    const tags = form.tags.split(',').map(t => t.trim()).filter(Boolean)
    await api.storeMemory(parsed, form.layer, tags)
    setForm({ content: '', layer: 'semantic', tags: '' })
    await load()
  }

  const entries: any[] = queryResult.length > 0 ? queryResult : (layers[activeLayer] || [])

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-2">
          <Brain className="w-5 h-5 text-aura-accent2" />
          <h1 className="text-xl font-bold font-mono">Memory Fabric</h1>
        </div>
        <p className="text-sm text-aura-muted mb-6">Multi-dimensional memory: Sensory → Working → Semantic → Episodic → Causal</p>

        {/* Stats row */}
        {stats && (
          <div className="grid grid-cols-5 gap-3 mb-6">
            {LAYERS.map(l => {
              const meta = LAYER_META[l]
              const count = stats.layers?.[l] ?? 0
              return (
                <button
                  key={l}
                  onClick={() => { setActiveLayer(l); setQueryResult([]) }}
                  className={clsx(
                    'card border text-left transition-all duration-200',
                    meta.color,
                    activeLayer === l ? 'ring-1 ring-current' : 'opacity-60 hover:opacity-100'
                  )}
                >
                  <div className="text-xl font-bold font-mono">{count}</div>
                  <div className="text-[10px] uppercase tracking-widest font-mono mt-0.5">{l}</div>
                </button>
              )
            })}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: search + store */}
          <div className="space-y-4">
            {/* Search */}
            <div className="card">
              <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-2 flex items-center gap-1">
                <Search className="w-3 h-3" /> Retrieve
              </div>
              <div className="flex gap-2">
                <input
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Tags to query…"
                  className="flex-1 bg-aura-bg border border-aura-border rounded-lg px-3 py-1.5 text-sm font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50"
                  onKeyDown={e => e.key === 'Enter' && search()}
                />
                <button onClick={search} className="btn-primary py-1.5">Query</button>
              </div>
              {queryResult.length > 0 && (
                <button onClick={() => setQueryResult([])} className="mt-2 text-xs text-aura-muted hover:text-aura-text">
                  ✕ Clear ({queryResult.length} results)
                </button>
              )}
            </div>

            {/* Store */}
            <div className="card">
              <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-3 flex items-center gap-1">
                <Plus className="w-3 h-3" /> Store Memory
              </div>
              <div className="space-y-2">
                <textarea
                  value={form.content}
                  onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
                  placeholder='{"fact": "..."} or plain text'
                  rows={3}
                  className="w-full bg-aura-bg border border-aura-border rounded-lg px-3 py-2 text-xs font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50 resize-none"
                />
                <select
                  value={form.layer}
                  onChange={e => setForm(f => ({ ...f, layer: e.target.value }))}
                  className="w-full bg-aura-bg border border-aura-border rounded-lg px-3 py-1.5 text-sm font-mono text-aura-text focus:outline-none"
                >
                  {LAYERS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
                <input
                  value={form.tags}
                  onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                  placeholder="tags, comma, separated"
                  className="w-full bg-aura-bg border border-aura-border rounded-lg px-3 py-1.5 text-sm font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50"
                />
                <button onClick={store} className="btn-primary w-full justify-center">STORE</button>
              </div>
            </div>
          </div>

          {/* Right: entries */}
          <div className="lg:col-span-2 card">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs text-aura-muted font-mono uppercase tracking-widest">
                {queryResult.length > 0 ? `Query Results (${queryResult.length})` : `${activeLayer} (${entries.length})`}
              </div>
              <div className={clsx('text-[10px] font-mono', LAYER_META[activeLayer]?.color.split(' ')[0] || 'text-aura-muted')}>
                {LAYER_META[activeLayer]?.desc}
              </div>
            </div>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {entries.length === 0 && (
                <div className="text-center py-12 text-aura-muted text-sm font-mono">No entries in this layer</div>
              )}
              {entries.map((e: any) => (
                <div key={e.id} className="p-3 bg-aura-bg rounded-lg border border-aura-border hover:border-aura-accent/30 transition-colors">
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="flex gap-1.5 flex-wrap">
                      {(e.tags || []).map((t: string) => (
                        <span key={t} className="badge bg-aura-accent/10 text-aura-accent/70">{t}</span>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[10px] font-mono text-aura-muted">c:{(e.confidence * 100).toFixed(0)}%</span>
                      <span className="text-[10px] font-mono text-aura-muted">×{e.access_count}</span>
                    </div>
                  </div>
                  <div className="text-xs text-aura-text/80 font-mono break-all">
                    {JSON.stringify(e.content).slice(0, 200)}
                  </div>
                  <div className="text-[10px] text-aura-muted font-mono mt-1">{e.created_at?.slice(0, 19).replace('T', ' ')}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
