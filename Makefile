.PHONY: install test lint format typecheck demo clean all
install:   ## editable install with dev tools
	pip install -e ".[dev]"
test:      ## run tests with coverage
	pytest
lint:      ## static checks
	ruff check src tests
	ruff format --check src tests
format:    ## auto-format
	ruff format src tests
	ruff check --fix src tests
typecheck: ## strict type check
	mypy
demo:      ## run the 60-second demo
	./demo.sh
all: lint typecheck test
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov build dist *.egg-info audit.jsonl
