# Evaluation

Purpose: offline evaluation harness and result history.

Key files: `harness.py` and `runs/`.

The locked test is never passed to the harness unless an explicit phase gate records
the commit hash, configuration, and timestamp.
