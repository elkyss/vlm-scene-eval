.PHONY: install test lint run run-mock run-frames eval gate all docker-build docker-test docker-run docker-all

CONFIG ?= configs/scenes/qwen2vl_guided.yaml
RUN_DIR ?= outputs/scenes/qwen2vl_guided
COMPOSE = docker compose run --rm

install:            ## local dev install
	pip install -e ".[vlm,similarity,dev]"

test:               ## unit + e2e tests (real-data tests skip if data/ is missing)
	pytest -q

lint:
	ruff check src tests && ruff format --check src tests && mypy

run:                ## one scene-level run (main result), e.g. make run CONFIG=configs/scenes/smolvlm_open.yaml
	vlm-eval run-scenes -c $(CONFIG)

run-mock:           ## scene pipeline with the oracle: claims supported must be 100%
	vlm-eval run-scenes -c configs/scenes/mock_oracle.yaml

run-frames:         ## frame-level diagnostic run, e.g. make run-frames CONFIG=configs/qwen2vl_v3.yaml
	vlm-eval run -c $(CONFIG)

eval:               ## re-score a saved scene run (no inference)
	vlm-eval evaluate-scenes $(RUN_DIR)

gate:               ## release gate on a scene run (exit 1 on failure)
	vlm-eval gate $(RUN_DIR)

all:                ## every run, comparison, leaderboard and the results store
	./scripts/run_all.sh

docker-build:
	docker compose build

docker-test:
	$(COMPOSE) --entrypoint make app test

docker-run:         ## e.g. make docker-run CONFIG=configs/scenes/mock_oracle.yaml
	$(COMPOSE) app run-scenes -c $(CONFIG)

docker-all:
	$(COMPOSE) --entrypoint ./scripts/run_all.sh app
