
restart:
	@make stop
	@make start

start:
	@docker compose -f docker/docker-compose.yaml up -d
	@make load-fixtures
	@make setup-dev-cluster

api-migrate:
	@docker compose -f docker/docker-compose.yaml run --rm api sh -c 'alembic revision --autogenerate'

api-migration:
	@docker compose -f docker/docker-compose.yaml run --rm api sh -c 'alembic upgrade head'

api-test:
	@docker compose -f docker/docker-compose.yaml run --rm api-test

portal-test:
	@docker compose -f docker/docker-compose.yaml run --rm portal-test

test:
	@echo "========================================="
	@echo "Running API tests..."
	@echo "========================================="
	@make api-test
	@echo ""
	@echo "========================================="
	@echo "Running Portal tests..."
	@echo "========================================="
	@make portal-test
	@echo ""
	@echo "========================================="
	@echo "All tests completed!"
	@echo "========================================="

build:
	@docker compose -f docker/docker-compose.yaml build

stop:
	@docker compose -f docker/docker-compose.yaml down -v --remove-orphans

logs:
	@docker compose -f docker/docker-compose.yaml logs -f

status:
	@docker compose -f docker/docker-compose.yaml ps

setup-dev-cluster:
	@./scripts/setup-k3s-cluster.sh

load-fixtures:
	@docker compose -f docker/docker-compose.yaml run --rm api sh -c 'python scripts/load_initial_templates.py'
	@docker compose -f docker/docker-compose.yaml run --rm api sh -c 'python scripts/load_initial_user.py'

reset-migrations:
	@docker compose -f docker/docker-compose.yaml run --rm api sh -c 'python scripts/reset_alembic_history.py'
