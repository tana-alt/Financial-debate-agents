UV ?= uv

.PHONY: help sync lint format format-check typecheck test test-fast check check-required

help:
	@printf '%s\n' \
		'Targets:' \
		'  make sync                  Install locked dev dependencies' \
		'  make lint                  Run Ruff lint checks' \
		'  make format                Format supported files with Ruff' \
		'  make format-check          Verify Ruff formatting without mutating files' \
		'  make typecheck             Run mypy' \
		'  make test                  Run the product pytest suite' \
		'  make test-fast             Run focused smoke tests' \
		'  make check                 Run the submission gate' \
		'  make check-required        Alias for make check'

sync:
	$(UV) sync --frozen --group dev

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

format-check:
	$(UV) run ruff format --check .

typecheck:
	$(UV) run mypy

test:
	$(UV) run pytest

test-fast:
	$(UV) run pytest -q \
		tests/test_api_smoke.py \
		tests/test_cli_smoke.py \
		tests/test_workflow_e2e.py

check: format-check lint typecheck test

check-required: check
