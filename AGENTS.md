# Repository Guidelines

## Project Structure & Module Organization
The analyzer core lives in parser/, with dedicated analyzers for JSP, Spring, SQL, and XML sources that feed metadata into the database layer. Shared helpers (configuration loaders, path utilities, logging, relationship analysers) sit in util/. Inspect database/ for generated SQLite artifacts and migrations, and projects/SampleSrc for the canonical sample project used in tests. Reference material and solution playbooks are under docs/, while interim logs and cached inspection output land in logs/ and 	emp/.

## Build, Test, and Development Commands
Run python create_report.py --project-name SampleSrc --report-type erd to materialize ERD and call-chain reports from the sample dataset. Validate schema integrity with python consistency_validator.py SampleSrc (fails fast on uniqueness and linkage issues). Execute the full automated suite via python -m pytest -q, which targets the repository-level 	est_*.py modules. For ad-hoc DB sanity checks, python check_test_files.py prints currently registered test assets from the metadata store.

## Coding Style & Naming Conventions
Use 4-space indentation and keep modules, functions, and files in snake_case.py. Classes and dataclasses should remain PascalCase (BackendEntryInfo, ConsistencyValidator). Prefer explicit type hints and targeted imports from 	yping, mirroring existing analyzers. Preserve Korean-language docstrings and comments in UTF-8; when adding English context, keep it concise and developer-focused.

## Testing Guidelines
Add new tests alongside the existing root-level files (	est_jsp_main_integration.py, 	est_frontend_relationship.py, etc.), naming them 	est_<feature>_<scenario>.py. Structure fixtures to reuse projects/SampleSrc assets, or document any additional sample data under projects/. Every parser enhancement must assert both positive extraction results and failure modes. Run python -m pytest -q before submitting and capture any new golden outputs in the relevant fixtures.

## Commit & Pull Request Guidelines
Recent history favors brief, imperative Korean subjects (조인개선3, 중복제거전5). Follow that pattern: a single descriptive chunk, no trailing punctuation, optional numeric suffix when iterating. Pull requests should include: a short summary of the analyzer or utility touched, linked issue IDs or TODO references where applicable, validation notes (tests, scripts, report generation), and screenshots or attached reports whenever UI or documentation artefacts change.

## Configuration & Data Safety
Local credentials and environment paths belong in config/config.yaml; keep overrides untracked or checked into config/parser/ templates with anonymized values. Review logging.yaml before enabling verbose modes—the default channels write to logs/ and can grow quickly. Sensitive project dumps should remain outside the repository unless scrubbed; share sanitized extracts via the projects/ directory and document provenance in accompanying README snippets.
