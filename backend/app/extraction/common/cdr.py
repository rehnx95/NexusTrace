import csv
import io

from app.extraction.contract.schemas import Edge, Entity, Mention

ALIASES = {
    "caller": {"caller", "from", "a number", "a_number", "source"},
    "called": {"called", "to", "b number", "b_number", "destination"},
    "timestamp": {"timestamp", "date", "time", "datetime"},
    "duration": {"duration", "call duration", "call_duration"},
}


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", " ").replace("_", " ")


def _find_column(headers: list[str], names: set[str]) -> int | None:
    for index, header in enumerate(headers):
        if _normalize(header) in names:
            return index
    return None


def _normalize_phone(value: str) -> str | None:
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10 or digits[0] not in "6789":
        return None
    return "+91" + digits


def parse_cdr(text: str, document_id: str) -> tuple[list[Entity], list[Edge], dict]:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return [], [], {"format": "unsupported", "valid_rows": 0, "invalid_rows": 0}

    delimiter = "\t" if "\t" in lines[0] else ","
    if delimiter == "," and lines[0].count(",") == 0:
        return [], [], {"format": "unsupported", "valid_rows": 0, "invalid_rows": 0}

    rows = list(csv.reader(io.StringIO(text.strip()), delimiter=delimiter))
    if not rows:
        return [], [], {"format": "unsupported", "valid_rows": 0, "invalid_rows": 0}

    headers = [_normalize(value) for value in rows[0]]
    caller_index = _find_column(headers, ALIASES["caller"])
    called_index = _find_column(headers, ALIASES["called"])
    if caller_index is None or called_index is None:
        return [], [], {"format": "unsupported", "valid_rows": 0, "invalid_rows": 0}

    timestamp_index = _find_column(headers, ALIASES["timestamp"])
    duration_index = _find_column(headers, ALIASES["duration"])
    entities: dict[str, Entity] = {}
    edges: dict[tuple[str, str], Edge] = {}
    invalid_rows = 0
    valid_rows = 0

    for row in rows[1:]:
        if max(caller_index, called_index) >= len(row):
            invalid_rows += 1
            continue
        caller = _normalize_phone(row[caller_index])
        called = _normalize_phone(row[called_index])
        if not caller or not called:
            invalid_rows += 1
            continue
        valid_rows += 1

        for phone in (caller, called):
            entities.setdefault(
                phone,
                Entity(
                    type="Phone",
                    id=phone,
                    properties={"number": phone},
                    mentions=(
                        Mention(
                            phone,
                            0,
                            len(phone),
                            "table",
                            1.0,
                            "CDR-PHONE",
                            document_id,
                        ),
                    ),
                ),
            )

        timestamp = (
            row[timestamp_index].strip()
            if timestamp_index is not None and timestamp_index < len(row)
            else None
        )
        duration = (
            row[duration_index].strip()
            if duration_index is not None and duration_index < len(row)
            else None
        )
        key = (caller, called)
        properties = {
            "first_seen": timestamp,
            "last_seen": timestamp,
        }
        if duration:
            properties["total_duration"] = duration
        if key in edges:
            previous = edges[key]
            properties = dict(previous.properties)
            properties["call_count"] = previous.properties.get("call_count", 1) + 1
            if timestamp:
                properties["last_seen"] = timestamp
        else:
            properties["call_count"] = 1

        edges[key] = Edge(
            source_type="Phone",
            source_id=caller,
            target_type="Phone",
            target_id=called,
            type="INTERCEPTED_CALL",
            properties=properties,
            evidence=(Mention("table-row", 0, 0, "table", 1.0, "CDR-CALL", document_id),),
            confidence=1.0,
        )

    return (
        list(entities.values()),
        list(edges.values()),
        {"format": "cdr_csv", "valid_rows": valid_rows, "invalid_rows": invalid_rows},
    )
