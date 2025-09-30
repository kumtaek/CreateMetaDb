# Repository Guidelines

## Project Structure & Module Organization
- Source loaders: `file_loading.py`, `java_loading.py`, `xml_loading.py`, `frontend_loading.py`
- Parsers: `parser/` (SQL, Spring, JSP, front-end)
- Utilities: `util/` (DB, paths, hashing, API naming, logging)
- Relationship builder: `relationship_builder.py`
- Reports: `reports/` (ERD, call chain, sequence)
- Database DDL: `database/` (metadata and SQL content DB scripts)
- Sample project: `projects/SampleSrc`

## Build, Test, and Development Commands
- Run analyzer: `python main.py --project-name SampleSrc --force`
- Generate reports: `python create_report.py --project-name SampleSrc`
- Run tests (pytest): `pytest -q`
- Clean DBs: delete `projects/SampleSrc/metadata.db` and `projects/SampleSrc/SqlContent.db`

## Coding Style & Naming Conventions
- Python 3.11+: 4‑space indentation, UTF‑8 (no BOM), type hints when helpful.
- API_URL names: `GET:selectUser` format via `util/api_naming.py`.
- Files table: `file_path` stores directory only; `file_name` stores the basename.
- Use `util.safe_logger` wrappers (`info`, `warning`, `error`, `debug`).
- Keep functions small; avoid unrelated refactors in a single change.

## Testing Guidelines
- Unit tests live at repo root as `test_*.py` (pytest).
- Prefer deterministic fixtures under `projects/SampleSrc`.
- For SQL parsing, add edge cases to `parser/sql_parser.py` tests and validate table extraction.
- Target coverage for modified modules: add at least one focused test per change.

## Commit & Pull Request Guidelines
- Commits: imperative mood, scoped prefix when possible (e.g., `analyzer:`, `parser:`, `util:`).
- PRs: include purpose, key changes, testing notes, and screenshots/paths to generated reports when relevant.
- Link issues and describe migration notes (e.g., schema changes, file_path semantics).

## Security & Configuration Tips
- Avoid executing untrusted project code during parsing; treat sources as data.
- Validate paths using `util.path_utils` to prevent traversal issues.
- Large runs: enable `--force` cautiously; re-create DBs after schema changes.

## Agent-Specific Instructions
- Respect API naming helpers in `util/api_naming.py` across loaders.
- When reading files, reconstruct full path: project root + `file_path` + `file_name`.
- Relationship building should load from DB when input isn’t pre-populated.
