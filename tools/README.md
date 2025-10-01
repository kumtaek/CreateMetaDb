# Tools

- `tools/compare_with_answer_key.py`
  - Connects to `projects/SampleSrc/metadata.db` and `SqlContent.db` and prints key metrics as JSON:
    - files, classes, components
    - relationships_total and per-type counts (CALL_METHOD, CALL_QUERY, USE_TABLE, JOIN_*, USE_COLUMN)
    - component counts (API_URL, METHOD, TABLE, COLUMN)
    - sql_total (from SqlContent DB)
  - Usage:
    - `python tools/compare_with_answer_key.py > projects/SampleSrc/report_metrics.json`
  - Compare the JSON against your answer key/baseline to validate thresholds.

