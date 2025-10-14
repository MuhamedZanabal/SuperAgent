.PHONY: help install dev test lint format clean docker-build docker-run

help:
	@echo "SuperAgent Development Commands"
	@echo "================================"
	@echo "install      - Install production dependencies"
	@echo "dev          - Install development dependencies"
	@echo "test         - Run test suite"
	@echo "test-cov     - Run tests with coverage"
	@echo "lint         - Run linters"
	@echo "format       - Format code"
	@echo "clean        - Clean build artifacts"
	@echo "docker-build - Build Docker image"
	@echo "docker-run   - Run Docker container"
	@echo "docs         - Build documentation"

install:
	pip install -e .

dev:
	pip install -e '.[dev]'
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=superagent --cov-report=html --cov-report=term

lint:
	ruff check superagent/ tests/
	black --check superagent/ tests/
	mypy superagent/

format:
	black superagent/ tests/
	ruff check --fix superagent/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t superagent:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docs:
	@echo "Documentation available in docs/"
	@echo "- INSTALLATION.md"
	@echo "- ARCHITECTURE.md"
	@echo "- CLI_USAGE.md"
	@echo "- DEPLOYMENT.md"
	@echo "- API_REFERENCE.md"
