# Repository Guidelines

## Project Structure & Module Organization
- Loaders: `file_loading.py`, `java_loading.py`, `xml_loading.py`, `frontend_loading.py` (ingest sources → components)
- Parsers: `parser/` (SQL, Spring annotations, JSP/front, String.format SQL)
- Relationships: `relationship_builder.py` (Frontend→Method→Query→Table builders)
- Utilities: `util/` (DB, path, hashing, API naming, mapper indexer, logging)
- Reports: `reports/` (ERD, call-chain, architecture)
- Database DDL: `database/` (metadata and SqlContent schemas)

## Build, Test, and Development Commands
- Run analyzer: `python main.py --project-name SampleSrc --force` (rebuild metadata + SqlContent)
- Generate reports: `python create_report.py --project-name SampleSrc`
- Run tests: `pytest -q`
- Clean DBs: delete `projects/SampleSrc/metadata.db` and `projects/SampleSrc/SqlContent.db`

## Coding Style & Naming Conventions
- Python 3.11+, 4 spaces, UTF-8 (no BOM)
- API_URL naming: `GET:selectUser` via `util/api_naming.py` (front/back unified)
- Files table: directory in `files.file_path`, basename in `files.file_name`
- Paths: use `util/path_utils.py`; normalize to forward slashes (`/`)
- Keep changes minimal and focused per module/PR

## Testing Guidelines
- Tests: `test_*.py` at repo root (pytest)
- Fixtures: use `projects/SampleSrc` for reproducible inputs
- Validate main flow counts: API_URL→METHOD, METHOD→SQL, SQL→TABLE
- Add SQL edge cases in `parser/sql_parser.py` and assert extracted tables

## Commit & Pull Request Guidelines
- Commits: imperative with scope (e.g., `parser:`, `util:`, `loader:`)
- PRs: purpose, key changes, reproduction steps, and sample report paths/screenshots
- Call out schema changes or resets required (e.g., file_path semantics)

## Agent-Specific Instructions
- Always use `util/api_naming.py` for API_URL names and identity hashes
- Reconstruct full paths as: project root + `files.file_path` + `files.file_name`
- Relationship building: prefer precise sources (`controller_api_map`, `mapper_map`) before fallbacks; use INSERT OR IGNORE for idempotency

