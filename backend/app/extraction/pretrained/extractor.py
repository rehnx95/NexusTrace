import hashlib
from pathlib import PurePath

from app.extraction.common.cdr import parse_cdr
from app.extraction.common.phone import extract_phones
from app.extraction.common.plate import extract_plates
from app.extraction.contract.extractor import Extractor
from app.extraction.contract.schemas import Entity, ExtractionResult


class PretrainedFirstExtractor(Extractor):
    def extract(self, documents: list[dict]) -> ExtractionResult:
        entities: dict[tuple[str, str], Entity] = {}
        edges = []
        diagnostics = {"documents": [], "phones": 0, "plates": 0, "cdr_valid_rows": 0}

        for document in documents:
            filename = document["filename"]
            text = document["text"]
            document_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
            extension = PurePath(filename).suffix.lower()
            diagnostics["documents"].append(
                {
                    "filename": filename,
                    "document_id": document_id,
                    "extension": extension,
                }
            )

            if extension in {".csv", ".tsv"}:
                cdr_entities, cdr_edges, cdr_diagnostics = parse_cdr(text, document_id)
                for entity in cdr_entities:
                    entities[(entity.type, entity.id)] = entity
                edges.extend(cdr_edges)
                diagnostics["cdr_valid_rows"] += cdr_diagnostics["valid_rows"]
                diagnostics["cdr_" + document_id] = cdr_diagnostics
                continue

            phone_entities, phone_mentions = extract_phones(text, document_id)
            plate_entities, plate_mentions = extract_plates(text, document_id)
            for entity_dict in phone_entities:
                mention = next(item for item in phone_mentions if item.text == entity_dict["id"])
                entity = Entity(
                    type=entity_dict["type"],
                    id=entity_dict["id"],
                    properties=entity_dict["properties"],
                    mentions=(mention,),
                )
                entities[(entity.type, entity.id)] = entity
            diagnostics["phones"] += len(phone_entities)

            for entity_dict in plate_entities:
                mention = next(
                    item
                    for item in plate_mentions
                    if "".join(character for character in item.text.upper() if character.isalnum())
                    == entity_dict["id"]
                )
                entity = Entity(
                    type=entity_dict["type"],
                    id=entity_dict["id"],
                    properties=entity_dict["properties"],
                    mentions=(mention,),
                )
                entities[(entity.type, entity.id)] = entity
            diagnostics["plates"] += len(plate_entities)

        return ExtractionResult(
            entities=list(entities.values()),
            edges=edges,
            diagnostics=diagnostics,
        )
