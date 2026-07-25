"""AURA-EAGLE — Memory type definitions"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


class MemoryLayer(str, Enum):
    SENSORY = "sensory"      # Raw, ephemeral (TTL: 30s)
    WORKING = "working"      # Active reasoning context
    SEMANTIC = "semantic"    # Facts, concepts
    EPISODIC = "episodic"    # Past events
    CAUSAL = "causal"        # Why-relationships


@dataclass
class MemoryEntry:
    content: dict[str, Any]
    layer: MemoryLayer
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    ttl_seconds: int | None = None

    def touch(self):
        self.access_count += 1
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "layer": self.layer.value,
            "content": self.content,
            "tags": self.tags,
            "confidence": self.confidence,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
