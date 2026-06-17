# urisys-node Makefile

PYTHON ?= python
PORT ?= 8790

.PHONY: help install test serve health app-chat-smoke

help:
	@echo "urisys-node targets:"
	@echo "  install   pip install -e ."
	@echo "  test      pytest"
	@echo "  serve     urisys-node on PORT=$(PORT)"
	@echo "  health    curl /health"
	@echo "  app-chat-smoke  curl /app/chat endpoints"

install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m pytest -q

serve:
	URISYS_NODE_SKIP_PAIRING=1 urisys-node serve --host 0.0.0.0 --port $(PORT)

health:
	@curl -fsS "http://127.0.0.1:$(PORT)/health" | $(PYTHON) -m json.tool | head -15

app-chat-smoke:
	@curl -fsS -X POST "http://127.0.0.1:$(PORT)/app/chat/messages" \
		-H 'Content-Type: application/json' \
		-d '{"channel_id":"smoke","role":"user","text":"ping"}' | $(PYTHON) -m json.tool
	@curl -fsS "http://127.0.0.1:$(PORT)/app/chat/messages?channel_id=smoke" | $(PYTHON) -m json.tool
