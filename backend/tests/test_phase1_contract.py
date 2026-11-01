from app.extraction.common.cdr import parse_cdr
from app.extraction.common.phone import extract_phones
from app.extraction.common.plate import extract_plates
from app.extraction.pretrained.extractor import PretrainedFirstExtractor
from app.graph.store import InMemoryGraphStore
from app.graph.writer import GraphWriter


def test_phone_extraction_normalizes_indian_numbers_and_rejects_short_numbers():
    entities, _ = extract_phones("Call +91 98765 43210 or 1234567890.", "doc-1")

    assert [entity["id"] for entity in entities] == ["+919876543210"]


def test_plate_extraction_normalizes_spaces_and_rejects_bare_numbers():
    entities, _ = extract_plates("Vehicle KA 05 MH 1234 was parked near 123456.", "doc-1")

    assert [entity["id"] for entity in entities] == ["KA05MH1234"]


def test_cdr_parser_extracts_phones_and_aggregates_calls():
    text = (
        "caller,called,timestamp,duration\n"
        "9876543210,9123456789,2025-01-01 10:00,30\n"
        "9876543210,9123456789,2025-01-01 10:05,45\n"
        "invalid,9123456789,2025-01-01,10\n"
    )
    entities, edges, diagnostics = parse_cdr(text, "doc-2")

    assert {entity.id for entity in entities} == {"+919876543210", "+919123456789"}
    assert len(edges) == 1
    assert edges[0].properties["call_count"] == 2
    assert diagnostics["valid_rows"] == 2
    assert diagnostics["invalid_rows"] == 1


def test_phase1_walking_skeleton_writes_to_in_memory_store():
    store = InMemoryGraphStore()
    writer = GraphWriter(store)
    result = PretrainedFirstExtractor().extract(
        [
            {
                "filename": "report.txt",
                "text": "Vehicle KA05MH1234 used phone 9876543210.",
            }
        ]
    )

    summary = writer.write("case-1", result.entities, result.edges, replace=True)

    assert summary["entities_written"] == 2
    assert summary["rejected_entities"] == 0
    assert len(store.entities["case-1"]) == 2
