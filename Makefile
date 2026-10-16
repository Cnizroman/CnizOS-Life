.PHONY: up down logs backend frontend build test backup

up:
	docker compose -f infra/docker-compose.yml up -d --build
	@echo "✓ http://localhost:8000/health  http://localhost:5173"

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

build:
	cd frontend && npm run build

test:
	cd backend && pytest -q
	cd frontend && npm run build

backup:
	curl -s -X POST http://localhost:8000/api/v1/settings/backup -H "Authorization: Bearer $$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"owner@cnizos.local","password":"Cnizos123!"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")" | python3 -m json.tool

install:
	bash install.sh
