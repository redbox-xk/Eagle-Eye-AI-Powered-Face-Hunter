"""AURA-EAGLE — Multi-Dimensional Memory Fabric

Implements five memory layers:
  Sensory  → ephemeral raw data (TTL 30s)
  Working  → active reasoning window (capped size)
  Semantic → long-term facts / concepts
  Episodic → event history
  Causal   → why-relationships

Mathematical model: Retrieval relevance = Similarity × Recency × Confidence
"""
from __future__ import annotations
import asyncio
import math
from collections import deque
from datetime import datetime
from typing import Any
import structlog

from .types import MemoryEntry, MemoryLayer
from backend.core.config import settings

log = structlog.get_logger()


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x ** 2 for x in a))
    nb = math.sqrt(sum(x ** 2 for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _keyword_sim(content: dict, tags: list[str]) -> float:
    if not tags:
        return 0.0
    text = " ".join(str(v) for v in content.values()).lower()
    hits = sum(1 for t in tags if t.lower() in text)
    return hits / len(tags)


def _recency_score(entry: MemoryEntry) -> float:
    age_s = (datetime.utcnow() - entry.updated_at).total_seconds()
    return math.exp(-age_s / 3600)  # decay over 1h


class MemoryFabric:
    """In-process multi-layer memory store with relevance-ranked retrieval."""

    def __init__(self):
        # Sensory: dict[id, entry] with TTL eviction
        self._sensory: dict[str, MemoryEntry] = {}
        # Working: bounded deque
        self._working: deque[MemoryEntry] = deque(maxlen=settings.working_memory_size)
        # Semantic / Episodic / Causal: dict[id, entry]
        self._semantic: dict[str, MemoryEntry] = {}
        self._episodic: dict[str, MemoryEntry] = {}
        self._causal: dict[str, MemoryEntry] = {}
        self._stats = {
            "total_stored": 0,
            "total_retrieved": 0,
            "evictions": 0,
        }

    # ── Store ─────────────────────────────────────────────────────────────────

    def store(
        self,
        content: dict[str, Any],
        layer: MemoryLayer,
        tags: list[str] | None = None,
        confidence: float = 1.0,
    ) -> MemoryEntry:
        ttl = settings.sensory_ttl_seconds if layer == MemoryLayer.SENSORY else None
        entry = MemoryEntry(
            content=content,
            layer=layer,
            tags=tags or [],
            confidence=confidence,
            ttl_seconds=ttl,
        )
        self._put(entry)
        self._stats["total_stored"] += 1
        log.debug("memory.stored", layer=layer.value, id=entry.id)
        return entry

    def _put(self, entry: MemoryEntry):
        store = self._layer_store(entry.layer)
        if isinstance(store, deque):
            store.append(entry)
        else:
            store[entry.id] = entry

    def _layer_store(self, layer: MemoryLayer) -> dict | deque:
        return {
            MemoryLayer.SENSORY: self._sensory,
            MemoryLayer.WORKING: self._working,
            MemoryLayer.SEMANTIC: self._semantic,
            MemoryLayer.EPISODIC: self._episodic,
            MemoryLayer.CAUSAL: self._causal,
        }[layer]

    # ── Retrieve ──────────────────────────────────────────────────────────────

    def retrieve(
        self,
        tags: list[str],
        layer: MemoryLayer | None = None,
        top_k: int = 10,
        min_confidence: float = 0.0,
    ) -> list[MemoryEntry]:
        self._evict_sensory()
        candidates: list[MemoryEntry] = []

        layers = [layer] if layer else list(MemoryLayer)
        for lyr in layers:
            store = self._layer_store(lyr)
            items = list(store) if isinstance(store, deque) else list(store.values())
            candidates.extend(items)

        scored = []
        for e in candidates:
            if e.confidence < min_confidence:
                continue
            if e.is_expired():
                continue
            sim = _keyword_sim(e.content, tags)
            rec = _recency_score(e)
            score = sim * rec * e.confidence
            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [e for _, e in scored[:top_k]]
        for e in results:
            e.touch()
        self._stats["total_retrieved"] += len(results)
        return results

    def retrieve_working(self) -> list[MemoryEntry]:
        self._evict_sensory()
        return list(self._working)

    def get_all_by_layer(self, layer: MemoryLayer) -> list[MemoryEntry]:
        self._evict_sensory()
        store = self._layer_store(layer)
        items = list(store) if isinstance(store, deque) else list(store.values())
        return [e for e in items if not e.is_expired()]

    def count_by_layer(self) -> dict[str, int]:
        self._evict_sensory()
        return {
            MemoryLayer.SENSORY.value: len([e for e in self._sensory.values() if not e.is_expired()]),
            MemoryLayer.WORKING.value: len(self._working),
            MemoryLayer.SEMANTIC.value: len(self._semantic),
            MemoryLayer.EPISODIC.value: len(self._episodic),
            MemoryLayer.CAUSAL.value: len(self._causal),
        }

    def stats(self) -> dict:
        return {**self._stats, "layers": self.count_by_layer()}

    # ── Eviction ─────────────────────────────────────────────────────────────

    def _evict_sensory(self):
        expired = [k for k, v in self._sensory.items() if v.is_expired()]
        for k in expired:
            del self._sensory[k]
        if expired:
            self._stats["evictions"] += len(expired)


# Singleton
memory = MemoryFabric()
