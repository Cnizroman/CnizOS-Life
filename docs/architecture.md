# CnizOS — Архитектура системы (Этап 1)

**Версия:** 1.0 — 2026-10-12  
**Статус:** Этап 1 — Проектирование  
**Автор:** Arena Agent для владельца CnizOS

---

## 1. Общая концепция

**CnizOS** — не ОС, а **персональный веб-центр управления** для одного владельца. Вся логика — в трёх процессах + интеграция:

```
[ Browser / PWA ]  ←→  [ CnizOS Backend (FastAPI + PostgreSQL) ]  ←→  [ CnizOS Bridge (Windows) ]
       ↕                              ↕
   [ TanStack Query + Zustand ]   [ Zoro (Python) via cnizos_client.py ]
```

### Ключевые принципы

1. **Single Source of Truth** — Backend единственный владелец данных. Frontend и Bridge — клиенты.
2. **Офлайн-стойкость** — PWA кэширует shell, данные — только с сервера. Офлайн-редактирование отложено до Этапа 4 (conflict resolution).
3. **Zero-trust к Bridge** — никаких `shell.exec()` из браузера. Только каталог разрешённых действий.
4. **Расширяемость** — новые модули = новая таблица + новые эндпоинты + новый роут во фронте, без переписывания ядра.
5. **Только бесплатные инструменты** — весь стек из ТЗ (React, FastAPI, PostgreSQL, APScheduler, PyInstaller) — OSS.

---

## 2. Компоненты и ответственность

### 2.1 CnizOS Web (Frontend)

- **Стек:** React 18 + TypeScript 5 + Vite 5 + Tailwind + shadcn/ui + React Router 6 + TanStack Query 5 + Zustand 4 + Lucide.
- **PWA:** VitePWA (Workbox), manifest, service worker для app-shell кэша. Push — через Web Push API, если разрешено.
- **Не делает:** прямых запросов в БД, прямых команд Windows.

**Структура `frontend/src`:**
```
app/          — провайдеры, роутер, темы
components/ui — shadcn/ui
layouts/      — SidebarLayout, MobileNav
modules/      — dashboard, projects, planner, memory, creative, zoro, pc-control, automation, settings
api/          — клиенты к /api/v1, типы
hooks/        — useAuth, useBridgeStatus, useSearch
stores/       — Zustand (theme, commandPalette, layoutDraft)
styles/       — globals.css (токены темы)
```

**Темизация:** CSS-переменные `--background`, `--accent` (приглушённый #4ADE80 → настраивается), `--card-border`. Тёмная тема по умолчанию (`#0A0A0B` фон, `#1A1A1D` карточки).

### 2.2 CnizOS Backend

- **Стек:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16, APScheduler 3.10, WebSocket, JWT + HttpOnly cookies.
- **Роль:** авторизация, CRUD, поиск (PostgreSQL FTS), планировщик напоминаний, брокер команд Bridge, логи.

**Структура `backend/app`:**
```
api/v1/        — routers: auth, projects, tasks, notes, search, devices, bridge, zoro, automation, dashboard
core/          — config, security (JWT, hash), rate_limit, errors
db/            — base, session, deps
models/        — SQLAlchemy модели
schemas/       — Pydantic схемы
services/      — бизнес-логика
integrations/  — zoro_auth
ws/            — bridge_manager, events
scheduler/     — reminders
```

**Паттерны:**
- Dependency Injection для `DBSession`, `CurrentUser`.
- Единый формат ошибок: `{ detail, code, request_id }`.
- Пагинация: `?page=1&limit=20` + заголовки `X-Total-Count`.

### 2.3 CnizOS Bridge (Windows)

- **Стек:** Python 3.13, FastAPI (локальный loopback на `127.0.0.1` для диагностики) + клиент WebSocket к backend, PyInstaller.
- **Связь:** **исходящий** WSS от Bridge → Backend (`wss://cnizos.example.com/ws/bridge`). Никаких открытых портов в интернет.
- **Безопасность:** токен устройства (`bridge_token` — UUID v4, хранится в `%APPDATA%/CnizOS/bridge.json`), проверка на сервере + на Bridge.

Жизненный цикл:
```
Bridge boot → auth (bridge_token) → heartbeat каждые 25с → ждёт команды → валидация allow-list → исполнение → результат
```

**Каталог команд (строго ограничен):**
| id | описание | параметры | подтверждение |
|---|---|---|---|
| `app.launch` | запуск приложения | `{ app_id: string }` | нет |
| `folder.open` | открыть папку | `{ path: string }` | если вне allow-list — отклонить |
| `project.open` | открыть проект | `{ project_id: uuid }` → резолвится в путь | нет |
| `system.volume.set` | громкость 0-100 | `{ level: int }` | нет |
| `system.volume.get` | получить громкость | `{}` | нет |
| `system.status.get` | CPU/RAM/disk | `{}` | нет |
| `profile.activate` | сценарий (alias) | `{ profile: string }` | по настройке |

### 2.4 Zoro Integration

- **Файл:** `integrations/zoro/cnizos_client.py` — лёгкий Python-клиент (httpx + pydantic).
- **Аутентификация:** персональный `ZORO_API_TOKEN` (Bearer) с scope `zoro`.
- **Не дублирует логику:** все запросы — к Backend.

---

## 3. Диаграмма развертывания

```
                    ┌─────────────────────┐
                    │   Пользователь      │
                    │  Browser / Phone PWA│
                    └─────────┬───────────┘
                              │ HTTPS/WSS
                              ▼
                    ┌─────────────────────┐
                    │  CnizOS Backend     │
                    │  FastAPI :8000      │
                    │  ┌───────────────┐  │
                    │  │ PostgreSQL :5432│  │
                    │  │ APScheduler   │  │
                    │  └───────────────┘  │
                    └─────────┬───────────┘
                              │ WSS (исходящий от Bridge)
                              ▼
                    ┌─────────────────────┐
                    │  CnizOS Bridge      │
                    │  Windows 10/11      │
                    │  %APPDATA%/CnizOS   │
                    └─────────────────────┘
                              ▲
                              │ httpx
                    ┌─────────┴───────────┐
                    │  Zoro Assistant     │
                    │  (отдельный процесс)│
                    └─────────────────────┘
```

---

## 4. Потоки данных

### 4.1 Создание задачи
1. Web → `POST /api/v1/tasks` (JWT)
2. Backend валидирует, пишет в `tasks`, пишет в `activity_logs`, ставит `task_reminders` в APScheduler
3. Backend → WebSocket `tasks:created` → все сессии пользователя обновляются
4. Zoro → `GET /api/v1/tasks?due=today` видит новую задачу

### 4.2 Команда Bridge
1. Web → `POST /api/v1/bridge/commands { action: "app.launch", params: {app_id:"vscode"} }`
2. Backend проверяет `command_permissions`, создаёт `bridge_commands` со статусом `queued`, command_id=uuid
3. Backend → WSS → Bridge (`command` frame)
4. Bridge повторно проверяет allow-list, исполняет, `running` → `succeeded/failed`
5. Backend обновляет статус, пишет в `activity_logs`, шлёт событие в WebSocket фронту и Zoro Hub

**Идемпотентность:** `command_id` — ключ. Повтор с тем же id — вернуть существующий статус, не исполнять повторно (таблица `bridge_commands` с уникальным id).

---

## 5. Безопасность

- **Владелец один:** эндпоинт `POST /api/v1/auth/setup` работает только когда `users` пуст. Далее — регистрация закрыта.
- **Auth:** Argon2/bcrypt для пароля, JWT access (15м) + refresh (30д, HttpOnly Secure cookie, rotation). Хранение refresh в `sessions` с `revoked_at`.
- **Rate limit:** SlowAPI — 100 req/мин на IP для API, 10 попыток входа / 15 мин.
- **CSRF:** если cookie-auth — Double Submit. Предпочтение: Bearer + HttpOnly refresh.
- **Bridge токены:** отдельные `bridge_devices.token_hash` (bcrypt), ротация через `POST /api/v1/bridge/devices/{id}/rotate`.
- **Валидация путей Windows:** `Path.resolve()` + проверка префикса по `allowed_directories` (на сервере и на Bridge).
- **Логи:** без секретов, с `request_id` (uuid) для трассировки.
- **Backup:** `pg_dump` по cron + ручной экспорт `/api/v1/settings/backup`.

---

## 6. Масштабирование и риски

| Риск | Митигация |
|---|---|
| Bridge офлайн | UI показывает красный статус + `last_heartbeat_at`, команды — `expired` через 60с |
| Потеря WSS | экспоненциальный backoff 1s→30s, очередь команд в БД |
| Конфликт редактирования | Last-Write-Wins с `updated_at` + `If-Match` (ETag), в UI — предупреждение |
| PWA Push не поддерживается | fallback в in-app колокольчик + лог `undelivered` |
| Большие файлы в Creative | хранить в `storage/` (volume) или S3-совместимом, в БД — только мета |

---

## 7. Выбор технологий — обоснование

- **PostgreSQL FTS вместо вектора** — достаточно для первого этапа, бесплатно, без внешней зависимости. Переход на pgvector — миграция без смены БД.
- **APScheduler вместо Celery** — нет нужды в Redis для одного пользователя; проще деплой. При росте — замена на Celery не ломает API.
- **Zustand вместо Redux** — минимум бойлерплейта для локального UI-состояния; серверное — в TanStack Query.
- **WebSocket вместо polling** — мгновенный статус Bridge, единый канал для событий.

---

## 8. Что исключено в v1

- Векторный поиск
- Произвольный код в Automation (только фиксированные шаги)
- Офлайн-редактирование с CRDT
- Многопользовательские роли/организации
