#!/bin/bash
set -e
echo "🚀 CnizOS — One-Click Install"
echo "=============================="

# 1. .env
if [ ! -f .env ]; then
  echo "→ Генерирую .env с секретами..."
  python3 scripts/generate_env.py
else
  echo "✓ .env уже есть"
fi

# 2. Docker (если есть)
if command -v docker >/dev/null 2>&1; then
  echo "→ Запускаю PostgreSQL + Backend (docker compose)..."
  docker compose -f infra/docker-compose.yml up -d --build
  echo "  Жду postgres..."
  sleep 6
  echo "✓ Docker запущен: http://localhost:8000/health"
else
  echo "⚠ Docker не найден — запускаю SQLite режим (как в песочнице)"
  echo "  Для дома поставь Docker Desktop: https://docs.docker.com/get-docker/"
  echo "  Сейчас запущу backend на SQLite:"
  (cd backend && pip install -q -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/cnizos-backend.log 2>&1 &)
  sleep 3
  curl -s http://localhost:8000/health | head -c 100; echo
fi

# 3. Frontend deps + build
if [ -d frontend ]; then
  echo "→ Ставлю frontend зависимости..."
  (cd frontend && npm install --silent && npm run build --silent)
  echo "✓ Frontend собран: frontend/dist/"
fi

# 4. Создаю владельца если нужно
echo "→ Проверяю владельца..."
SETUP=$(curl -s http://localhost:8000/api/v1/auth/setup-status || echo '{"setup_required":true}')
if echo "$SETUP" | grep -q "true"; then
  echo "  Нет владельца — создаю демо:"
  echo "  email: owner@cnizos.local / pass: Cnizos123!"
  curl -s -X POST http://localhost:8000/api/v1/auth/setup -H "Content-Type: application/json" -d '{"email":"owner@cnizos.local","password":"Cnizos123!","display_name":"Owner"}' | python3 -m json.tool | head -n 10
else
  echo "✓ Владелец уже есть"
fi

# 5. Сид демо-данных
echo "→ Заполняю демо-проект/задачи..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"owner@cnizos.local","password":"Cnizos123!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
if [ -n "$TOKEN" ]; then
  curl -s -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/projects -H "Content-Type: application/json" -d '{"title":"PHANTASMAGORIA","description":"Демо творческий проект","category":"creative","status":"active"}' > /dev/null || true
  echo "✓ Демо-данные готовы"
fi

echo ""
echo "✅ ГОТОВО!"
echo "Frontend: http://localhost:5173  (npm run dev) или открой frontend/dist через Caddy"
echo "Backend:  http://localhost:8000/docs"
echo "Логин:    owner@cnizos.local / Cnizos123!  (смени в Settings)"
echo "Bridge:   смотри PC Control в браузере → скопируй токен → на Windows: windows-bridge/install.bat"
echo "Зоро:     integrations/zoro/cnizos_client.py уже готов — смотри integrations/zoro/README.md"
echo ""
