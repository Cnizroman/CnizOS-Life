# CnizOS — Как запустить Этап 2

## Песочница (уже запущено)
Backend: http://localhost:8000 — docs http://localhost:8000/docs
Frontend: http://localhost:5173 — Live Preview в интерфейсе Arena

Логин: owner@cnizos.local / Cnizos123!
Или удали backend/cnizos.db и открой /setup

## Локально с Docker (для дома)
cp .env.example .env  # заполни JWT_SECRET
docker compose -f infra/docker-compose.yml up -d
# postgres на :5432, backend на :8000, frontend npm run dev на :5173

## Проверка
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/auth/setup-status
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"owner@cnizos.local","password":"Cnizos123!"}'
