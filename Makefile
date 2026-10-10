.PHONY: install test lint run-mock run eval compare all docker-build docker-test docker-run

CONFIG ?= configs/smolvlm_v3.yaml
RUN_DIR ?= outputs/smolvlm_v3
COMPOSE = docker compose run --rm

install:            ## local dev install
	pip install -e ".[vlm,similarity,dev]"

test:               ## unit + e2e tests (real-data tests skip if data/ is missing)
	pytest -q

lint:
	ruff check src tests && ruff format --check src tests && mypy

run-mock:           ## full pipeline with the oracle mock: every metric should be ~100%
	vlm-eval run -c configs/mock_oracle.yaml

run:                ## one real run, e.g. make run CONFIG=configs/smolvlm_v1.yaml
	vlm-eval run -c $(CONFIG)

eval:               ## recompute metrics + report from saved predictions
	vlm-eval evaluate $(RUN_DIR)

all:                ## every run + comparison from the README
	./scripts/run_all.sh

docker-build:
	docker compose build

docker-test:
	$(COMPOSE) --entrypoint make app test

docker-run:
	$(COMPOSE) app run -c $(CONFIG)
