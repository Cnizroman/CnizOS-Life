# Этап 2 — Основа приложения (ГОТОВ к проверке)

**Дата:** 2026-10-12
**Статус:** ✅ Запускается, реальный backend + frontend + auth

---

## Что собрано

### Frontend (port 5173)
- Vite + React 18 + TypeScript + Tailwind 3 (dark graphite #0A0A0B + #4ADE80)
- React Router 6 — 9 разделов + защита роутов
- TanStack Query + Zustand (auth, theme)
- shadcn/ui компоненты (Button, Card, Input, Badge)
- AppShell: боковая панель (сворачивается) + мобильная навигация + bottom nav
- Header: глобальный поиск ⌘K + реальный статус Bridge (из /api/v1/bridge/status) + индикация пользователя
- Pages:
  - `/setup` — первичная настройка владельца (работает только когда users пуст)
  - `/login` — вход
  - `/` — Dashboard с виджетами от реального `/dashboard/summary`
  - `/projects`, `/planner`, `/memory` — реальные запросы к backend (пустые состояния из БД, без фиктивных данных)
  - `/creative`, `/zoro`, `/pc`, `/automation`, `/settings` — заглушки с бейджем "Этап" и описанием (дизайн готов)
  - `/search?q=...` — заглушка FTS (подключится в Этапе 3)
- PWA manifest (`/manifest.json`) — устанавливается на телефон
- Proxy `/api` → `http://localhost:8000` для dev

### Backend (port 8000)
- FastAPI + SQLAlchemy 2 async + SQLite (dev) / PostgreSQL (prod via DATABASE_URL)
- JWT access (15м) + refresh (30д, rotation, HttpOnly cookie)
- Модели: `users`, `sessions` (остальные — Этап 3, но Base.metadata уже создаёт)
- Endpoints:
  - `GET /health`, `GET /api/health`
  - `GET /api/v1/auth/setup-status`
  - `POST /api/v1/auth/setup` — один раз, потом 403
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
  - `GET /api/v1/auth/sessions`
  - `GET /api/v1/dashboard/summary` — реальный, пока нули
  - `GET /api/v1/projects`, `POST /api/v1/projects` (stub)
  - `GET /api/v1/tasks`, `GET /api/v1/notes`, `GET /api/v1/search`, `GET /api/v1/creative/assets`, `GET /api/v1/automation/scenarios` — stubs для навигации
  - `GET /api/v1/bridge/status`, `GET /api/v1/bridge/devices`, `GET /api/v1/bridge/actions`
- CORS, X-Request-Id, единый формат ошибок
- Auto-create tables на старте (lifespan)

### Инфра
- `infra/docker-compose.yml` — postgres:16 + backend
- `.env.example` — все секреты
- `backend/requirements.txt` — только бесплатные пакеты

---

## Как запустить в песочнице (уже запущено)

```bash
# Backend уже на :8000
cd /home/user/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend уже на :5173
cd /home/user/frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

**Live Preview:**
- Web: https://5173-i2llwdzm7vngf5ctk066y.e2b.app
- Backend docs: https://8000-i2llwdzm7vngf5ctk066y.e2b.app/docs

**Демо-аккаунт (создан автоматически для теста):**
```
email: owner@cnizos.local
pass:  Cnizos123!
```
Или удали `backend/cnizos.db` и пройди `/setup` как единственный владелец.

---

## Проверка Этапа 2 (критерии готовности)

- [x] `GET /api/v1/auth/setup-status` → `{"setup_required":false}` после первого setup
- [x] `POST /api/v1/auth/setup` второй раз → 403
- [x] Login выдает JWT, `/auth/me` возвращает пользователя
- [x] Frontend `/setup` → `/login` → `/` работает, токен в localStorage
- [x] Dashboard показывает реальные цифры из `/dashboard/summary` (пока 0 — честно, без фиктивных)
- [x] Навигация 9 разделов работает, мобильная — тоже
- [x] Header показывает Bridge offline честно (пока нет Bridge)
- [x] PWA manifest доступен
- [x] `npm run build` проходит, `curl /api/v1/health` OK

---

## Что дальше — Этап 3 (Основные данные)

- Миграции для `projects`, `tasks`, `notes`, `tags`, `project_notes`
- Полный CRUD Projects (страница проекта, статусы, дедлайны, local_path)
- Planner: задачи с due_date, recurrence, напоминания (APScheduler)
- Memory: Markdown, FTS (`body_tsv`), связи
- Dashboard агрегаты от реальных таблиц
- Поиск `/search` по всем типам
- Activity logs

После Этапа 3 системой можно пользоваться без Windows.

---

## Известные ограничения Этапа 2

- БД — SQLite в песочнице (для прод — PostgreSQL, переключи DATABASE_URL)
- Alembic пока stub, таблицы создаются via `create_all`
- Проекты/задачи/заметки — только чтение пустого списка, создание — Этап 3
- Bridge — только статус, без реальных команд (Этап 5)
- Zoro — заглушка (Этап 6, client уже спроектирован)

