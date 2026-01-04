# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-01-03

### Changed
- **Code quality**: DRY refactoring - extracted helpers to eliminate duplication, flattened nesting, removed unnecessary `else` statements
- **Constants**: Extracted magic strings (`DEFAULT_CACHE_PATH`, `DEFAULT_DECK_NAME`, `TEXT_PREVIEW_LENGTH`)
- **Consistency**: Fixed logger usage, simplified None checks, removed duplicate validation
- **Error handling**: Better Anki connection errors; verbose details only with `--verbose`

## [0.1.3] - 2026-01-03

### Added
- **Subcommand-based CLI**: Restructured CLI to use argparse subcommands
  - `sync` - Sync Readwise highlights to Anki (replaces default behavior)
  - `show-orphaned` - Show orphaned notes (notes in Anki but not in Readwise)
  - `delete-orphaned` - Delete orphaned notes permanently
- **Orphaned notes management**: New feature to detect and manage orphaned notes
  - Shows detailed information (title, text preview) for each orphaned note
  - Optional deletion with confirmation details
  - Added `notes_deleted` to statistics tracking
- **New Makefile targets**:
  - `make sync` - Sync highlights to Anki
  - `make show-orphaned` - Show orphaned notes
  - `make show-orphaned-dev` - Show orphaned notes using local cache
  - `make delete-orphaned` - Delete orphaned notes
  - `make delete-orphaned-dev` - Delete orphaned notes using local cache
  - `make run` now aliases to `make sync`
- **Flexible argument parsing**: Common flags (`--verbose`, `--use-cache`, etc.) can now be specified either before or after the subcommand

### Changed
- **BREAKING**: CLI now requires a subcommand. Running `readwise2anki` without arguments shows help instead of syncing
  - Old: `readwise2anki --use-cache`
  - New: `readwise2anki sync --use-cache`
- Renamed internal method `sync_states()` to `handle_orphaned_notes()` for clarity
- Refactored CLI into smaller functions: `configure_logging()`, `load_readwise_highlights()`
- Normal sync no longer detects or reports orphaned notes (use dedicated commands instead)

### Fixed
- Version inconsistency between `pyproject.toml` and `__init__.py`

## [0.1.2] - 2026-01-03

### Added
- Option to change the deck via `--deck` flag

## [0.1.1] - 2025-12-25

### Changed
- Refactored model handling: DRY, validation, and logging improvements
- Don't unsuspend cards that might have been suspended in Anki

### Added
- Create links for books

## [0.1.0] - Initial Release

### Added
- Initial release with basic Readwise to Anki synchronization
- Support for syncing highlights from Readwise to Anki
- AnkiConnect integration
- Cache support for development
