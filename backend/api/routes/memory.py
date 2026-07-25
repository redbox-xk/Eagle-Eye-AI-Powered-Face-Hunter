"""AURA-EAGLE — Memory API"""
from fastapi import APIRouter
from backend.memory.fabric import memory
from backend.memory.types import MemoryLayer

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/stats")
async def memory_stats():
    return memory.stats()


@router.get("/layers")
async def memory_layers():
    return {
        layer.value: [e.to_dict() for e in memory.get_all_by_layer(layer)]
        for layer in MemoryLayer
    }


@router.get("/layer/{layer_name}")
async def get_layer(layer_name: str):
    try:
        layer = MemoryLayer(layer_name)
    except ValueError:
        return {"error": f"Unknown layer: {layer_name}"}
    entries = memory.get_all_by_layer(layer)
    return {"layer": layer_name, "count": len(entries), "entries": [e.to_dict() for e in entries]}


@router.post("/store")
async def store_memory(body: dict):
    content = body.get("content", {})
    layer_name = body.get("layer", "semantic")
    tags = body.get("tags", [])
    confidence = float(body.get("confidence", 1.0))
    try:
        layer = MemoryLayer(layer_name)
    except ValueError:
        return {"error": f"Unknown layer: {layer_name}"}
    entry = memory.store(content=content, layer=layer, tags=tags, confidence=confidence)
    return entry.to_dict()


@router.post("/retrieve")
async def retrieve_memory(body: dict):
    tags = body.get("tags", [])
    top_k = int(body.get("top_k", 10))
    min_confidence = float(body.get("min_confidence", 0.0))
    results = memory.retrieve(tags=tags, top_k=top_k, min_confidence=min_confidence)
    return {"count": len(results), "entries": [e.to_dict() for e in results]}
