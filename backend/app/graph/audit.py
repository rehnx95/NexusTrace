import hashlib
import json
from datetime import datetime, timezone

from utils import neo4j_driver as db

GENESIS = "GENESIS"


def _compute_hash(entry: dict, previous_hash: str) -> str:
    payload = json.dumps(entry, sort_keys=True) + previous_hash
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_batch(case_id: str, action: str, details: list[dict]) -> list[dict]:
    seq_rows = db.query(
        "MATCH (a:AuditEntry {case_id: $case_id}) RETURN coalesce(max(a.seq), -1) AS max_seq",
        {"case_id": case_id},
    )
    seq = seq_rows[0]["max_seq"] + 1 if seq_rows else 0

    hash_rows = db.query(
        "MATCH (a:AuditEntry {case_id: $case_id}) "
        "RETURN a.hash AS hash ORDER BY a.seq DESC LIMIT 1",
        {"case_id": case_id},
    )
    previous_hash = hash_rows[0]["hash"] if hash_rows else GENESIS
    entries = []

    for offset, detail in enumerate(details):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": detail,
        }
        entry_hash = _compute_hash(entry, previous_hash)
        entries.append(
            {
                "case_id": case_id,
                "seq": seq + offset,
                "timestamp": entry["timestamp"],
                "action": action,
                "details": json.dumps(detail, sort_keys=True),
                "prev_hash": previous_hash,
                "hash": entry_hash,
            }
        )
        previous_hash = entry_hash

    if entries:
        db.query(
            "UNWIND $entries AS entry "
            "CREATE (a:AuditEntry {"
            "case_id: entry.case_id, seq: entry.seq, timestamp: entry.timestamp, "
            "action: entry.action, details: entry.details, prev_hash: entry.prev_hash, "
            "hash: entry.hash})",
            {"entries": entries},
        )
    return entries
