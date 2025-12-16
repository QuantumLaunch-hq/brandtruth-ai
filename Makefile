# Makefile for BrandTruth AI

.PHONY: help install dev test test-unit test-integration test-e2e test-cov lint format run frontend clean

# Default target
help:
	@echo "BrandTruth AI - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make dev           Install dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-int      Run integration tests only"
	@echo "  make test-e2e      Run e2e tests only"
	@echo "  make test-contract Run contract/schema tests"
	@echo "  make test-pact     Run Pact consumer tests"
	@echo "  make test-cov      Run tests with coverage"
	@echo ""
	@echo "Development:"
	@echo "  make run           Start API server"
	@echo "  make frontend      Start frontend dev server"
	@echo "  make lint          Run linter"
	@echo "  make format        Format code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Clean generated files"

# Setup
install:
	pip install -r requirements.txt

dev: install
	pip install pytest-watch

# Testing
test:
	pytest -v

test-unit:
	pytest tests/unit -v

test-int:
	pytest tests/integration -v

test-e2e:
	pytest tests/e2e -v

test-contract:
	pytest tests/contract -v

test-component:
	pytest tests/component -v

test-new:
	pytest tests/unit/test_hook_generator.py tests/unit/test_landing_page_analyzer.py tests/unit/test_budget_simulator.py tests/unit/test_platform_recommender.py tests/unit/test_ab_test_planner.py tests/unit/test_audience_targeting.py tests/unit/test_iteration_assistant.py tests/unit/test_social_proof_collector.py -v

test-new-int:
	pytest tests/integration/test_hooks_api.py tests/integration/test_landing_api.py tests/integration/test_budget_api.py tests/integration/test_platforms_api.py tests/integration/test_abtest_api.py tests/integration/test_audience_api.py tests/integration/test_iterate_api.py tests/integration/test_social_api.py -v

test-new-e2e:
	pytest tests/e2e/test_new_features_e2e.py -v

test-new-all:
	@echo "Running all new feature tests (Slices 16-23)..."
	make test-new
	make test-new-int
	make test-new-e2e
	pytest tests/contract/test_new_features_contracts.py -v
	pytest tests/component/test_new_features_components.py -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

test-watch:
	pytest-watch -- -v

# Development
run:
	python api_server.py --port 8000

frontend:
	cd frontend && npm run dev

# Linting & Formatting
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

# Cleanup
clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	rm -rf output/test_* output/*.zip
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Docker (future)
docker-build:
	docker build -t brandtruth-ai .

docker-run:
	docker run -p 8000:8000 brandtruth-ai
