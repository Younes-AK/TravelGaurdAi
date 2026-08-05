SHELL := /bin/bash

PYTHON ?= .venv/bin/python
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest
UVICORN ?= $(PYTHON) -m uvicorn
PYTHONPATH ?= src
PYTHONPYCACHEPREFIX ?= /tmp/travelguard-pycache

APP := travelguard_ai.api.app:app
HOST ?= 127.0.0.1
PORT ?= 8000
IMAGE ?= travelguard-ai

.PHONY: help venv install install-dev test compile run dev health ready docs demo docker-build docker-run clean

help:
	@echo "TravelGuard AI commands"
	@echo ""
	@echo "  make venv          Create .venv with python3.12"
	@echo "  make install       Install runtime dependencies"
	@echo "  make install-dev   Install test/development dependencies"
	@echo "  make test          Run all tests"
	@echo "  make compile       Compile Python files"
	@echo "  make run           Run FastAPI on $(HOST):$(PORT)"
	@echo "  make dev           Run FastAPI with reload"
	@echo "  make health        Check /health"
	@echo "  make ready         Check /ready"
	@echo "  make docs          Print Swagger UI URL"
	@echo "  make demo          Send example decision request"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-run    Run Docker image on $(PORT)"
	@echo "  make clean         Remove local caches"

venv:
	python3.12 -m venv .venv
	$(PIP) install --upgrade pip

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt

test:
	PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) $(PYTEST) -q

compile:
	PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) $(PYTHON) -m compileall src tests

run:
	PYTHONPATH=$(PYTHONPATH) PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) $(UVICORN) $(APP) --host $(HOST) --port $(PORT)

dev:
	PYTHONPATH=$(PYTHONPATH) PYTHONPYCACHEPREFIX=$(PYTHONPYCACHEPREFIX) $(UVICORN) $(APP) --host $(HOST) --port $(PORT) --reload

health:
	curl -sS http://$(HOST):$(PORT)/health
	@echo ""

ready:
	curl -sS http://$(HOST):$(PORT)/ready
	@echo ""

docs:
	@echo "Swagger UI: http://$(HOST):$(PORT)/docs"
	@echo "OpenAPI JSON: http://$(HOST):$(PORT)/openapi.json"

demo:
	curl -sS -X POST http://$(HOST):$(PORT)/v1/decision \
		-H 'content-type: application/json' \
		-H 'x-request-id: demo-request-1' \
		-d '{"transaction":{"transaction_id":"tx-2026-0001","amount":725.5,"currency":"USD","merchant_country":"MA","timestamp":"2026-08-05T12:30:00Z","device_id":"device-123","ip_address":"203.0.113.10"},"customer_profile":{"customer_id":"cust-001","home_country":"US","trusted_devices":["device-123"],"last_sim_swap_days":180,"travel_frequency":4,"avg_transaction_amount":110.0,"phone_number":"+15555550123"},"signals":{"location":{"provider":"bank-cache","confidence":0.92,"country":"MA","verified":true}}}'
	@echo ""

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p $(PORT):8000 $(IMAGE)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
