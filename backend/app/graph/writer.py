from app.extraction.contract.schemas import Edge, Entity
from app.graph.registry import validate_edge, validate_entity
from app.graph.store import GraphStore


class GraphWriter:
    def __init__(self, store: GraphStore, audit=None):
        self.store = store
        self.audit = audit

    def write(self, case_id: str, entities: list[Entity], edges: list[Edge], replace: bool = False):
        if replace:
            self.store.clear_case(case_id)

        valid_entities = [entity for entity in entities if validate_entity(entity.type)]
        valid_edges = [
            edge for edge in edges if validate_edge(edge.source_type, edge.type, edge.target_type)
        ]

        entity_count = self.store.write_entities(case_id, valid_entities)
        edge_count = self.store.write_edges(case_id, valid_edges)
        if self.audit:
            self.audit(
                case_id,
                "INGESTION_RUN",
                [
                    {"type": entity.type, "id": entity.id, "method": "pretrained-first"}
                    for entity in valid_entities
                ]
                + [
                    {
                        "type": edge.type,
                        "from": edge.source_id,
                        "to": edge.target_id,
                        "confidence": edge.confidence,
                    }
                    for edge in valid_edges
                ],
            )
        return {
            "entity_count": entity_count,
            "edge_count": edge_count,
            "entities_written": len(valid_entities),
            "edges_written": len(valid_edges),
            "rejected_entities": len(entities) - len(valid_entities),
            "rejected_edges": len(edges) - len(valid_edges),
        }
