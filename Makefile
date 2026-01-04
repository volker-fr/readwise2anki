# Via http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Common flags for development
DEV_FLAGS = --use-cache --verbose

.PHONY: install
install: ## Install dependencies with uv
	uv sync

.PHONY: run
run: sync ## Run the CLI tool (alias for sync)

.PHONY: run-dev
run-dev: ## Run the CLI tool with local cache
	uv run readwise2anki sync $(DEV_FLAGS)

.PHONY: test
test: ## Run tests
	uv run pytest

.PHONY: clean
clean: ## Clean build artifacts and cache
	rm -rf .venv
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: lint
lint: ## Run linters
	uv run ruff check .

.PHONY: format
format: ## Format code
	uv run ruff format .

.PHONY: list-highlights
list-highlights: ## List highlights from Readwise
	echo "Not implemented"
	#uv run readwise2anki --action list-highlights

.PHONY: sync
sync: ## Sync highlights to Anki
	uv run readwise2anki sync

.PHONY: show-orphaned
show-orphaned: ## Show orphaned notes (in Anki but not in Readwise)
	uv run readwise2anki show-orphaned

.PHONY: show-orphaned-dev
show-orphaned-dev: ## Show orphaned notes using local cache
	uv run readwise2anki show-orphaned $(DEV_FLAGS)

.PHONY: delete-orphaned
delete-orphaned: ## Delete orphaned notes (in Anki but not in Readwise)
	uv run readwise2anki delete-orphaned

.PHONY: delete-orphaned-dev
delete-orphaned-dev: ## Delete orphaned notes using local cache
	uv run readwise2anki delete-orphaned $(DEV_FLAGS)

.DEFAULT_GOAL := help
