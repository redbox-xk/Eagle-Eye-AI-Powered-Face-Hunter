# PROJECT AURA-EAGLE
## Autonomous Unified Reasoning Architecture · Enhanced Adaptive Graph Learning Engine

A full-stack enterprise cognitive AI platform implementing multi-agent reasoning, multi-dimensional memory, probabilistic knowledge graphs, decision scoring, ethical governance, and real-time observability.

## Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.12) + Uvicorn |
| Frontend | React 18 + TypeScript + Tailwind CSS + Vite |
| Database | PostgreSQL (Replit managed) |
| Real-time | WebSockets |
| Graphs | NetworkX |
| Observability | psutil + structlog |

## Architecture

```
AURA-EAGLE
├── Perception Engine          — Converts input to structured observations
├── Memory Fabric              — 5-layer memory (sensory/working/semantic/episodic/causal)
├── Knowledge Graph            — Probabilistic entity-relationship reasoning (NetworkX)
├── Cognitive Engine           — Multi-agent system
│   ├── ORION (Supervisor)     — Task decomposition + coordination
│   ├── NYX (Architecture)     — Systems reasoning
│   ├── SOL (Research)         — Analytical synthesis
│   ├── KADE (Engineering)     — Debugging + optimization
│   ├── MIRA (Communication)   — Human factors + explanation
│   └── VEX (Creative)         — Hypothesis generation
├── Reasoning Pipeline         — 11-stage cognitive loop
├── Decision Engine            — D = (Value + Confidence + Evidence) − (Risk + Cost + Uncertainty)
├── Simulation Engine          — Monte Carlo scenario evaluation
├── Governance Engine          — E = Benefit − Harm + Transparency + Accountability
└── API Platform               — FastAPI REST + WebSocket
```

## Running

```
# Backend: port 8000
cd / && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend: port 5000 (dev) or served from backend after build
cd frontend && npm install && npm run dev -- --port 5000
```

Or use the configured workflows.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | System health |
| GET | `/api/metrics/aura` | AURA score |
| GET | `/api/metrics/overview` | System overview |
| GET | `/api/agents/` | List all agents |
| POST | `/api/agents/{id}/run` | Run specific agent |
| POST | `/api/reasoning/run` | Execute full pipeline |
| GET | `/api/reasoning/history` | Pipeline history |
| POST | `/api/reasoning/simulate` | Run simulation |
| GET | `/api/memory/stats` | Memory stats |
| POST | `/api/memory/store` | Store memory entry |
| GET | `/api/knowledge/graph` | Full knowledge graph |
| WS | `/ws` | Real-time event stream |

## User Preferences
- Dark theme only (aura-bg: #050a12)
- Monospace font for all data/metrics
- Real-time updates preferred over polling
- Keep code modular and strictly typed
