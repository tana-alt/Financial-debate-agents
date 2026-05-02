UV ?= uv

.PHONY: sync lint format typecheck test check-required

sync:
	$(UV) sync --frozen --group dev

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

typecheck:
	$(UV) run mypy

test:
	$(UV) run pytest

check-required: lint typecheck test
