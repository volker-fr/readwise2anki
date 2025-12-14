# Via http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install dependencies with uv
	uv sync

.PHONY: run
run: ## Run the CLI tool
	uv run readwise2anki

.PHONY: run-dev
run-dev: ## Run the CLI tool with local cache
	uv run readwise2anki --use-cache --verbose

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
	echo "Not implemented"
	#uv run readwise2anki --action sync

.DEFAULT_GOAL := help
