def test_empty_ingestion_returns_baseline_error():
    from services.ingest import run_ingestion

    result = run_ingestion("baseline-case", "", "", False)

    assert result["ok"] is False
    assert result["error"]
