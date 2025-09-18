# Repository Guidelines

## Project Structure & Module Organization
SourceAnalyzer is a staged Python pipeline: `main.py` coordinates loaders in the repo root, `util/` holds shared helpers, and `parser/` contains XML, SQL, and Java analyzers. Code to inspect lives under `projects/` (see `SampleSrc/`); generated artifacts land in `docs/`, `reports/`, and `logs/`. Configuration and logging profiles stay in `config/`, while UI assets sit in `css/` and `js/`. Use `temp/` for scratch exports and keep database DDL in `database/`.

## Build, Test, and Development Commands
Run a full ingest with `py -3 main.py --project-name SampleSrc --clear-metadb` (swap in your project). Add `--dry-run` to validate options without writes. Produce reports via `py -3 create_report.py --project-name <name>`. Before committing, sanity-check imports with `py -3 -m compileall .`.

## Coding Style & Naming Conventions
Use Python 3.10+, 4-space indentation, snake_case for modules/functions, PascalCase for classes, and UPPER_CASE for constants. Prefer pathlib utilities in `util.path_utils`. Log through `util.logger` instead of `print`, and keep configuration keys kebab-case to match `config/config.yaml`.

## Testing Guidelines
New automated tests should mirror package names under `tests/` (e.g., `tests/parser/test_xml_parser.py`) and run with `pytest -q`. When coverage depends on real projects, use fixtures from `projects/SampleSrc/`. If a scenario stays manual, document the steps and outcomes in `test_unit_result.txt` and attach generated HTML/PDF evidence to reviews.

## Commit & Pull Request Guidelines
Existing commits favor brief Korean imperatives (e.g., "시각화완성16"). Continue the style, keep messages under ~50 characters, and append a short English hint in parentheses when clarity helps. PRs should outline affected pipeline stages, list runnable commands, link relevant `docs/` specs, and include fresh report diffs or screenshots. Reference issue IDs whenever they exist.

## Configuration & Logging Tips
Update `config/config.yaml` (and matching `.bak` copy) when introducing sources or toggles. Extend `config/logging.yaml` rather than ad hoc loggers, and note that `main.py` purges log files older than 24 hours—archive diagnostics before rerunning long analyses.
