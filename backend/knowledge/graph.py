"""AURA-EAGLE — Knowledge Graph Engine

Mathematical model:
  Node: (Entity, Attributes, Confidence)
  Edge: (Source, Relation, Target, Probability)
  Reasoning: P(Result | Evidence) via path traversal
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Any
import networkx as nx
import structlog

log = structlog.get_logger()


@dataclass
class KNode:
    entity: str
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity": self.entity,
            "attributes": self.attributes,
            "confidence": self.confidence,
        }


@dataclass
class KEdge:
    source_id: str
    target_id: str
    relation: str
    probability: float = 1.0

    @property
    def id(self) -> str:
        return f"{self.source_id}:{self.relation}:{self.target_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation,
            "probability": self.probability,
        }


class KnowledgeGraph:
    """
    In-memory knowledge graph backed by NetworkX DiGraph.
    Supports probabilistic relationship reasoning.
    """

    def __init__(self):
        self._g: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, KNode] = {}
        self._edges: dict[str, KEdge] = {}
        self._seed_defaults()

    # ── Nodes ─────────────────────────────────────────────────────────────────

    def add_node(self, entity: str, attributes: dict | None = None, confidence: float = 1.0) -> KNode:
        node = KNode(entity=entity, attributes=attributes or {}, confidence=confidence)
        self._nodes[node.id] = node
        self._g.add_node(node.id, label=entity, confidence=confidence, **node.attributes)
        log.debug("kg.node_added", entity=entity, id=node.id)
        return node

    def find_node(self, entity: str) -> KNode | None:
        for n in self._nodes.values():
            if n.entity.lower() == entity.lower():
                return n
        return None

    def get_or_create(self, entity: str, **attrs) -> KNode:
        existing = self.find_node(entity)
        if existing:
            return existing
        return self.add_node(entity, attributes=attrs)

    # ── Edges ─────────────────────────────────────────────────────────────────

    def add_edge(self, source_id: str, target_id: str, relation: str, probability: float = 1.0) -> KEdge:
        edge = KEdge(source_id=source_id, target_id=target_id, relation=relation, probability=probability)
        self._edges[edge.id] = edge
        self._g.add_edge(source_id, target_id, relation=relation, probability=probability)
        log.debug("kg.edge_added", edge_id=edge.id)
        return edge

    # ── Reasoning ─────────────────────────────────────────────────────────────

    def connected(self, source_id: str, target_id: str) -> float:
        """Estimate connection probability via shortest path product."""
        if not self._g.has_node(source_id) or not self._g.has_node(target_id):
            return 0.0
        try:
            path = nx.shortest_path(self._g, source_id, target_id)
        except nx.NetworkXNoPath:
            return 0.0
        prob = 1.0
        for i in range(len(path) - 1):
            edge_data = self._g.edges[path[i], path[i + 1]]
            prob *= edge_data.get("probability", 1.0)
        return prob

    def neighbors(self, node_id: str, relation: str | None = None) -> list[KNode]:
        result = []
        for _, target in self._g.out_edges(node_id):
            edge_data = self._g.edges[node_id, target]
            if relation is None or edge_data.get("relation") == relation:
                if target in self._nodes:
                    result.append(self._nodes[target])
        return result

    def subgraph_for_entity(self, entity: str, depth: int = 2) -> dict:
        node = self.find_node(entity)
        if not node:
            return {"nodes": [], "edges": []}
        ego = nx.ego_graph(self._g, node.id, radius=depth)
        nodes = [self._nodes[n].to_dict() for n in ego.nodes() if n in self._nodes]
        edges = []
        for s, t in ego.edges():
            eid = f"{s}:*:{t}"
            for edge in self._edges.values():
                if edge.source_id == s and edge.target_id == t:
                    edges.append(edge.to_dict())
        return {"nodes": nodes, "edges": edges}

    def stats(self) -> dict:
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "density": nx.density(self._g),
            "is_dag": nx.is_directed_acyclic_graph(self._g),
        }

    def all_nodes(self) -> list[dict]:
        return [n.to_dict() for n in self._nodes.values()]

    def all_edges(self) -> list[dict]:
        return [e.to_dict() for e in self._edges.values()]

    # ── Seeding ───────────────────────────────────────────────────────────────

    def _seed_defaults(self):
        """Bootstrap the graph with AURA-EAGLE core concepts."""
        concepts = [
            ("AURA-EAGLE", {"type": "system", "domain": "AI"}),
            ("Perception Engine", {"type": "subsystem"}),
            ("Memory Fabric", {"type": "subsystem"}),
            ("Cognitive Engine", {"type": "subsystem"}),
            ("Reasoning Pipeline", {"type": "subsystem"}),
            ("Decision Engine", {"type": "subsystem"}),
            ("Governance", {"type": "subsystem"}),
            ("ORION", {"type": "agent", "role": "supervisor"}),
            ("NYX", {"type": "agent", "role": "architecture"}),
            ("SOL", {"type": "agent", "role": "research"}),
            ("KADE", {"type": "agent", "role": "engineering"}),
            ("MIRA", {"type": "agent", "role": "communication"}),
            ("VEX", {"type": "agent", "role": "creative"}),
        ]
        ids: dict[str, str] = {}
        for name, attrs in concepts:
            n = self.add_node(name, attributes=attrs)
            ids[name] = n.id

        relations = [
            ("AURA-EAGLE", "CONTAINS", "Perception Engine", 1.0),
            ("AURA-EAGLE", "CONTAINS", "Memory Fabric", 1.0),
            ("AURA-EAGLE", "CONTAINS", "Cognitive Engine", 1.0),
            ("AURA-EAGLE", "CONTAINS", "Reasoning Pipeline", 1.0),
            ("AURA-EAGLE", "CONTAINS", "Decision Engine", 1.0),
            ("AURA-EAGLE", "CONTAINS", "Governance", 1.0),
            ("Cognitive Engine", "MANAGED_BY", "ORION", 0.98),
            ("ORION", "COORDINATES", "NYX", 0.95),
            ("ORION", "COORDINATES", "SOL", 0.95),
            ("ORION", "COORDINATES", "KADE", 0.95),
            ("ORION", "COORDINATES", "MIRA", 0.95),
            ("ORION", "COORDINATES", "VEX", 0.95),
            ("Reasoning Pipeline", "FEEDS", "Decision Engine", 0.92),
            ("Decision Engine", "GOVERNED_BY", "Governance", 0.99),
            ("Memory Fabric", "SUPPORTS", "Reasoning Pipeline", 0.90),
            ("Perception Engine", "FEEDS", "Memory Fabric", 0.88),
        ]
        for src, rel, tgt, prob in relations:
            if src in ids and tgt in ids:
                self.add_edge(ids[src], ids[tgt], rel, prob)


# Singleton
knowledge_graph = KnowledgeGraph()
