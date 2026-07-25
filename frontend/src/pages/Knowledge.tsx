import { useEffect, useState, useRef } from 'react'
import { api } from '../lib/api'
import MetricsBar from '../components/MetricsBar'
import { Network, Plus, Search } from 'lucide-react'

export default function Knowledge() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] })
  const [stats, setStats] = useState<any>(null)
  const [selected, setSelected] = useState<any>(null)
  const [newNode, setNewNode] = useState('')
  const [search, setSearch] = useState('')
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const load = async () => {
    try {
      const [g, s] = await Promise.all([api.graphData(), api.graphStats()])
      setGraphData(g); setStats(s)
    } catch {}
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    drawGraph()
  }, [graphData])

  const drawGraph = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const W = canvas.width, H = canvas.height
    ctx.clearRect(0, 0, W, H)

    const nodes = graphData.nodes
    const edges = graphData.edges
    if (!nodes.length) return

    // Layout: circular
    const positions: Record<string, { x: number; y: number }> = {}
    const cx = W / 2, cy = H / 2
    const r = Math.min(W, H) * 0.35

    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * Math.PI * 2 - Math.PI / 2
      positions[n.id] = {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      }
    })

    // Draw edges
    ctx.strokeStyle = 'rgba(26,39,68,0.8)'
    ctx.lineWidth = 1
    edges.forEach(e => {
      const src = positions[e.source]
      const tgt = positions[e.target]
      if (!src || !tgt) return
      const alpha = Math.max(0.2, e.probability || 0.5)
      ctx.globalAlpha = alpha
      ctx.beginPath()
      ctx.moveTo(src.x, src.y)
      ctx.lineTo(tgt.x, tgt.y)
      ctx.strokeStyle = `rgba(0, 212, 255, ${alpha * 0.5})`
      ctx.stroke()

      // Arrow
      const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x)
      const ax = tgt.x - Math.cos(angle) * 14
      const ay = tgt.y - Math.sin(angle) * 14
      ctx.beginPath()
      ctx.moveTo(ax, ay)
      ctx.lineTo(ax - 6 * Math.cos(angle - 0.4), ay - 6 * Math.sin(angle - 0.4))
      ctx.lineTo(ax - 6 * Math.cos(angle + 0.4), ay - 6 * Math.sin(angle + 0.4))
      ctx.closePath()
      ctx.fillStyle = `rgba(0, 212, 255, ${alpha * 0.5})`
      ctx.fill()
    })
    ctx.globalAlpha = 1

    // Draw nodes
    nodes.forEach(n => {
      const pos = positions[n.id]
      if (!pos) return
      const isAgent = n.attributes?.type === 'agent'
      const isSystem = n.entity === 'AURA-EAGLE'
      const radius = isSystem ? 16 : isAgent ? 10 : 8

      ctx.beginPath()
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2)
      ctx.fillStyle = isSystem ? '#7c3aed' : isAgent ? '#00d4ff' : '#1a2744'
      ctx.fill()
      ctx.strokeStyle = isSystem ? '#a855f7' : isAgent ? '#00d4ff' : '#1a2744'
      ctx.lineWidth = isSystem ? 2 : 1.5
      ctx.stroke()

      // Label
      ctx.fillStyle = '#e2e8f0'
      ctx.font = `${isSystem ? '11' : '9'}px JetBrains Mono, monospace`
      ctx.textAlign = 'center'
      ctx.fillText(n.entity, pos.x, pos.y + radius + 12)
    })
  }

  const addNode = async () => {
    if (!newNode.trim()) return
    await api.addNode(newNode.trim())
    setNewNode('')
    await load()
  }

  const filtered = graphData.nodes.filter(n =>
    !search || n.entity.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-2">
          <Network className="w-5 h-5 text-aura-accent2" />
          <h1 className="text-xl font-bold font-mono">Knowledge Graph</h1>
        </div>
        <p className="text-sm text-aura-muted mb-6">Entity nodes, probabilistic edges, and relationship reasoning</p>

        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            { label: 'Nodes', value: stats?.node_count ?? '—' },
            { label: 'Edges', value: stats?.edge_count ?? '—' },
            { label: 'Density', value: stats ? (stats.density * 100).toFixed(2) + '%' : '—' },
          ].map(m => (
            <div key={m.label} className="card">
              <div className="metric-value">{m.value}</div>
              <div className="metric-label">{m.label}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Canvas */}
          <div className="lg:col-span-2 card p-2">
            <div className="text-xs text-aura-muted font-mono mb-2 px-2 uppercase tracking-widest">Graph Visualizer</div>
            <canvas
              ref={canvasRef}
              width={700}
              height={400}
              className="w-full rounded-lg bg-aura-bg"
              onClick={(e) => {
                const rect = canvasRef.current!.getBoundingClientRect()
                const scaleX = 700 / rect.width
                const scaleY = 400 / rect.height
                const mx = (e.clientX - rect.left) * scaleX
                const my = (e.clientY - rect.top) * scaleY
                // find clicked node
                const nodes = graphData.nodes
                const cx = 350, cy = 200, r = Math.min(700, 400) * 0.35
                nodes.forEach((n, i) => {
                  const angle = (i / nodes.length) * Math.PI * 2 - Math.PI / 2
                  const x = cx + r * Math.cos(angle)
                  const y = cy + r * Math.sin(angle)
                  if (Math.sqrt((mx - x) ** 2 + (my - y) ** 2) < 16) {
                    setSelected(n)
                  }
                })
              }}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <div className="card">
              <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-2 flex items-center gap-1">
                <Plus className="w-3 h-3" /> Add Node
              </div>
              <div className="flex gap-2">
                <input
                  value={newNode}
                  onChange={e => setNewNode(e.target.value)}
                  placeholder="Entity name…"
                  className="flex-1 bg-aura-bg border border-aura-border rounded-lg px-3 py-1.5 text-sm font-mono text-aura-text placeholder-aura-muted focus:outline-none focus:border-aura-accent/50"
                  onKeyDown={e => e.key === 'Enter' && addNode()}
                />
                <button onClick={addNode} className="btn-primary py-1.5">Add</button>
              </div>
            </div>

            {selected && (
              <div className="card border border-aura-accent/20">
                <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-2">Selected Node</div>
                <div className="font-mono font-bold text-aura-accent text-sm">{selected.entity}</div>
                <div className="text-[10px] text-aura-muted mt-1">ID: {selected.id}</div>
                <div className="text-[10px] text-aura-muted">Confidence: {(selected.confidence * 100).toFixed(0)}%</div>
                {Object.entries(selected.attributes || {}).map(([k, v]) => (
                  <div key={k} className="text-[10px] text-aura-text/70">{k}: {String(v)}</div>
                ))}
              </div>
            )}

            <div className="card">
              <div className="text-xs text-aura-muted font-mono uppercase tracking-widest mb-2 flex items-center gap-1">
                <Search className="w-3 h-3" /> Nodes
              </div>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Filter…"
                className="w-full bg-aura-bg border border-aura-border rounded-lg px-3 py-1.5 text-xs font-mono text-aura-text placeholder-aura-muted focus:outline-none mb-2"
              />
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {filtered.map(n => (
                  <button
                    key={n.id}
                    onClick={() => setSelected(n)}
                    className="w-full text-left px-2 py-1 rounded text-xs font-mono text-aura-text/80 hover:bg-aura-accent/10 hover:text-aura-accent transition-colors"
                  >
                    {n.entity}
                    <span className="text-aura-muted ml-1">({(n.confidence * 100).toFixed(0)}%)</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
