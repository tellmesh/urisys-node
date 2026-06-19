# urisys-node Makefile

PYTHON ?= .venv/bin/python
PORT ?= 8790

.PHONY: help install test test-all test-integration test-coverage test-watch serve health app-chat-smoke

help:
	@echo "urisys-node targets:"
	@echo "  install             pip install -e ."
	@echo "  test                pytest (quick)"
	@echo "  test-all            pytest -v (all tests verbose)"
	@echo "  test-integration    integration tests only"
	@echo "  test-coverage       pytest with coverage report"
	@echo "  test-watch          watch mode (ptw)"
	@echo "  serve               urisys-node on PORT=$(PORT)"
	@echo "  health              curl /health"
	@echo "  app-chat-smoke      curl /app/chat endpoints"

install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m pytest -q

test-all:
	$(PYTHON) -m pytest -v

test-integration:
	$(PYTHON) -m pytest tests/integration/ -v

test-coverage:
	@.venv/bin/pip install -q pytest-cov > /dev/null 2>&1 || true
	$(PYTHON) -m pytest --cov=urisysnode --cov-report=term-missing -v

test-watch:
	@.venv/bin/pip install -q pytest-watch > /dev/null 2>&1 || true
	$(PYTHON) -m ptw tests/ --pattern "test_*.py" --ignore "tests/integration/"

serve:
	URISYS_NODE_SKIP_PAIRING=1 urisys-node serve --host 0.0.0.0 --port $(PORT)

health:
	@curl -fsS "http://127.0.0.1:$(PORT)/health" | $(PYTHON) -m json.tool | head -15

app-chat-smoke:
	@curl -fsS -X POST "http://127.0.0.1:$(PORT)/app/chat/messages" \
		-H 'Content-Type: application/json' \
		-d '{"channel_id":"smoke","role":"user","text":"ping"}' | $(PYTHON) -m json.tool
	@curl -fsS "http://127.0.0.1:$(PORT)/app/chat/messages?channel_id=smoke" | $(PYTHON) -m json.tool


# Release helpers
publish:
	@echo "📦 Publishing to PyPI..."
	@command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)
	rm -rf dist/ build/ *.egg-info/
	.venv/bin/python -m build
	.venv/bin/twine check dist/*
	@echo "🚀 Uploading to PyPI..."
	.venv/bin/twine upload dist/*


publish-test:
	@echo "📦 Publishing to TestPyPI..."
	@command -v .venv/bin/twine > /dev/null 2>&1 || (.venv/bin/pip install --upgrade twine build)
	rm -rf dist/ build/ *.egg-info/
	.venv/bin/python -m build
	.venv/bin/twine upload --repository testpypi dist/*

version:
	@echo "📦 Version information..."
	@cat VERSION
	@.venv/bin/python -c "from importlib.metadata import version; print(f'Installed version: {version(\"sumd\")}')"
