"""AURA-EAGLE — Knowledge Graph API"""
from fastapi import APIRouter
from backend.knowledge.graph import knowledge_graph

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/stats")
async def graph_stats():
    return knowledge_graph.stats()


@router.get("/graph")
async def full_graph():
    return {
        "nodes": knowledge_graph.all_nodes(),
        "edges": knowledge_graph.all_edges(),
        "stats": knowledge_graph.stats(),
    }


@router.get("/entity/{entity}")
async def entity_subgraph(entity: str, depth: int = 2):
    return knowledge_graph.subgraph_for_entity(entity, depth=depth)


@router.post("/node")
async def add_node(body: dict):
    entity = body.get("entity", "")
    attributes = body.get("attributes", {})
    confidence = float(body.get("confidence", 1.0))
    node = knowledge_graph.add_node(entity, attributes=attributes, confidence=confidence)
    return node.to_dict()


@router.post("/edge")
async def add_edge(body: dict):
    source_id = body.get("source_id", "")
    target_id = body.get("target_id", "")
    relation = body.get("relation", "RELATED_TO")
    probability = float(body.get("probability", 1.0))
    edge = knowledge_graph.add_edge(source_id, target_id, relation, probability)
    return edge.to_dict()


@router.get("/connected/{source}/{target}")
async def check_connection(source: str, target: str):
    src_node = knowledge_graph.find_node(source)
    tgt_node = knowledge_graph.find_node(target)
    if not src_node or not tgt_node:
        return {"connected": False, "probability": 0.0, "error": "Node not found"}
    prob = knowledge_graph.connected(src_node.id, tgt_node.id)
    return {"connected": prob > 0, "probability": round(prob, 4)}
