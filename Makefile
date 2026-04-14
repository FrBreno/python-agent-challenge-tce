.PHONY: up down test logs rebuild

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

rebuild:
	docker compose down
	docker compose up -d --build

test:
	pytest -q
