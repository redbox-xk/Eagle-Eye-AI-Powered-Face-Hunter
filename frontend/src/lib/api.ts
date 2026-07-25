const BASE = '/api'

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!r.ok) throw new Error(`API ${path}: ${r.status}`)
  return r.json()
}

export const api = {
  // Health
  health: () => req<{ status: string; system: string; version: string }>('/health'),

  // Metrics
  overview: () => req<any>('/metrics/overview'),
  systemMetrics: () => req<any>('/metrics/system'),
  auraScore: () => req<any>('/metrics/aura'),

  // Agents
  listAgents: () => req<{ agents: any[] }>('/agents/'),
  runAgent: (id: string, task: string, context?: any) =>
    req<any>(`/agents/${id}/run`, {
      method: 'POST',
      body: JSON.stringify({ task, context }),
    }),

  // Reasoning
  runPipeline: (task: string, context?: any) =>
    req<any>('/reasoning/run', {
      method: 'POST',
      body: JSON.stringify({ task, context }),
    }),
  pipelineHistory: (limit = 10) => req<any>(`/reasoning/history?limit=${limit}`),
  simulate: (task: string) =>
    req<any>('/reasoning/simulate', { method: 'POST', body: JSON.stringify({ task }) }),
  decisions: () => req<any>('/reasoning/decisions'),
  evaluateEthics: (action: string) =>
    req<any>('/reasoning/ethics/evaluate', { method: 'POST', body: JSON.stringify({ action }) }),

  // Memory
  memoryStats: () => req<any>('/memory/stats'),
  memoryLayers: () => req<any>('/memory/layers'),
  storeMemory: (content: any, layer: string, tags: string[]) =>
    req<any>('/memory/store', {
      method: 'POST',
      body: JSON.stringify({ content, layer, tags }),
    }),
  retrieveMemory: (tags: string[]) =>
    req<any>('/memory/retrieve', { method: 'POST', body: JSON.stringify({ tags }) }),

  // Knowledge Graph
  graphData: () => req<any>('/knowledge/graph'),
  graphStats: () => req<any>('/knowledge/stats'),
  addNode: (entity: string, attributes?: any) =>
    req<any>('/knowledge/node', { method: 'POST', body: JSON.stringify({ entity, attributes }) }),
  addEdge: (source_id: string, target_id: string, relation: string, probability?: number) =>
    req<any>('/knowledge/edge', {
      method: 'POST',
      body: JSON.stringify({ source_id, target_id, relation, probability }),
    }),
}
