import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.extraction.pretrained.extractor import PretrainedFirstExtractor


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def score_set(records: list[dict]) -> dict:
    expected_entities = {
        (record["id"], entity["type"], entity["id"])
        for record in records
        for entity in record["entities"]
    }
    expected_relations = {
        (
            record["id"],
            relation["source_type"],
            relation["source_id"],
            relation["type"],
            relation["target_type"],
            relation["target_id"],
        )
        for record in records
        for relation in record["relations"]
    }

    extractor = PretrainedFirstExtractor()
    predicted_entities = set()
    predicted_relations = set()
    for record in records:
        result = extractor.extract([{"filename": record["id"] + ".txt", "text": record["text"]}])
        for entity in result.entities:
            predicted_entities.add((record["id"], entity.type, entity.id))
        for relation in result.edges:
            predicted_relations.add(
                (
                    record["id"],
                    relation.source_type,
                    relation.source_id,
                    relation.type,
                    relation.target_type,
                    relation.target_id,
                )
            )

    def prf(expected: set, predicted: set):
        true_positive = len(expected & predicted)
        precision = true_positive / len(predicted) if predicted else 0.0
        recall = true_positive / len(expected) if expected else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    return {
        "entity": prf(expected_entities, predicted_entities),
        "relation": prf(expected_relations, predicted_relations),
        "counts": {
            "expected_entities": len(expected_entities),
            "predicted_entities": len(predicted_entities),
            "expected_relations": len(expected_relations),
            "predicted_relations": len(predicted_relations),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = load_jsonl(args.dev / "reports.jsonl")
    metrics = score_set(records)
    result = {
        "phase": 2,
        "records": len(records),
        "metrics": metrics,
        "inputs": {
            "dev": str(args.dev),
        },
        "digest": hashlib.sha256(
            json.dumps(records, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / "phase2-dev.json"
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
