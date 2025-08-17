.PHONY: build up down logs shell test lint fmt migrate createsuperuser clean

# Docker commands
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec web python manage.py shell

# Django commands
migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

createsuperuser:
	docker compose exec web python manage.py createsuperuser

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

# Quality commands
test:
	docker compose exec web pytest -v --cov=apps --cov-report=term-missing --cov-report=html

lint:
	docker compose exec web ruff check .
	docker compose exec web mypy apps/

fmt:
	docker compose exec web black .
	docker compose exec web isort .
	docker compose exec web ruff check --fix .

# Utility commands
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

restart: down up

rebuild: down build up

# Development helpers
dev-data:
	docker compose exec web python manage.py loaddata fixtures/dev_data.json

shell-plus:
	docker compose exec web python manage.py shell_plus --ipython

dbshell:
	docker compose exec db psql -U postgres -d app

# Show this help
help:
	@echo "Available commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up            - Start containers"
	@echo "  make down          - Stop containers"
	@echo "  make logs          - Show logs"
	@echo "  make shell         - Django shell"
	@echo "  make migrate       - Run migrations"
	@echo "  make makemigrations - Create migrations"
	@echo "  make createsuperuser - Create superuser"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make fmt           - Format code"
	@echo "  make clean         - Clean cache files"
	@echo "  make restart       - Restart containers"
	@echo "  make rebuild       - Rebuild and restart"