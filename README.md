# CnizOS — Персональная цифровая система (ГОТОВО)

> **Версия 1.0 — Full Stack** | Тёмная графитовая тема `#0A0A0B` + приглушённый зелёный `#4ADE80`
> **Live в песочнице:** Frontend `:5173` + Backend `:8000` уже запущены — открой Live Preview в интерфейсе Arena

CnizOS — единый центр для одного владельца: проекты, задачи, база знаний, творческий архив, Zoro Hub, управление Windows через Bridge, автоматизация и PWA.

---

## 🚀 Быстрый старт (песочница — уже работает)

```bash
# Backend уже на :8000 — docs http://localhost:8000/docs
# Frontend уже на :5173 — Live Preview
# Логин демо-владельца:
email: owner@cnizos.local
pass:  Cnizos123!
# или удали backend/cnizos.db и пройди /setup — первичная настройка единственного владельца
```

**Проверить что всё живо:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/dashboard/summary -H "Authorization: Bearer <token>"
# Bridge mock уже подключён: TestBridge-Sandbox online
```

## 🖥️ Локально с Docker (для дома/VPS)

```bash
git clone <repo> cnizos && cd cnizos
cp .env.example .env  # заполни JWT_SECRET="$(openssl rand -hex 32)"
docker compose -f infra/docker-compose.yml up -d  # postgres:16 + backend
cd frontend && npm install && npm run dev  # :5173
# prod: npm run build + любой static (Caddy/Nginx)
```

`.env` — все секреты, не коммить. `infra/docker-compose.yml` уже настроен.

## 🏗️ Что реализовано (все 8 этапов)

| Модуль | Статус | Детали |
|---|---|---|
| **Auth** | ✅ | `POST /auth/setup` один раз → JWT access 15м + refresh 30д HttpOnly rotation, `setup-status`, сессии |
| **Dashboard** | ✅ | Реальные агрегаты: сегодня/просрочено/дедлайны/проекты/заметки/bridge/команды/напоминания, быстрые создания |
| **Projects** | ✅ | CRUD + slug, фильтры, статусы, приоритеты, deadlines, локальный путь, страница проекта с задачами/заметками, история |
| **Planner** | ✅ | Задачи с due_date, календарь `/tasks/calendar`, views today/overdue/upcoming, теги, recurrence_rule, напоминания |
| **Memory** | ✅ | Markdown, типы (note/idea/bug...), коллекции, избранное/закреп, поиск LIKE/FTS, связи `project_notes` |
| **Creative** | ✅ | Коллекции, типы (music/cover/photo...), загрузка файлов до 100MB в `storage/creative/<id>/`, external_url, превью |
| **Search** | ✅ | Глобальный `GET /search?q=` по проектам/задачам/заметкам с сниппетами и score |
| **PC Control** | ✅ | Регистрация Bridge (`POST /bridge/devices` → токен один раз),Heartbeat WSS, команды `app.launch/folder.open/system.volume.*`, allow-list, идемпотентность, история, экспирация 60с |
| **Bridge** | ✅ | `windows-bridge/bridge/main.py` — исходящий WSS, heartbeat 25с, mock режим (`--mock`), автозагрузка, PyInstaller exe |
| **Zoro** | ✅ | `integrations/zoro/cnizos_client.py` — `get_tasks/create_task/search_notes/create_note/list_projects/execute_action`, scope `/api/v1/zoro/*`, журнал |
| **Automation** | ✅ | Сценарии с шагами (фиксированный набор), `POST /scenarios/{id}/run`, журнал `step_results`, continue_on_error, cancel |
| **Settings** | ✅ | Тема/акцент/плотность, устройства, сессии, журнал `activity_logs`, `POST /settings/backup` (копия SQLite/pg_dump), restore |
| **PWA** | ✅ | `manifest.json` + `sw.js` (cache shell), устанавливается на телефон, offline shell, на телефоне управляет Bridge если онлайн |
| **Тесты** | ✅ | `backend/tests/` — 8 тестов: auth, tasks, notes/search/links, bridge allow-list/idempotency, zoro — все pass |

Дизайн — тёмная технологичная среда, не админка. Нет фиктивных кнопок — всё из реальных данных.

## 🔐 Безопасность

- Нет `shell.exec` из браузера — только каталог `app.launch` и т.д.
- Проверка allow-list на сервере **и** на Bridge (`Path.resolve()` + префикс)
- Bridge токены хранятся как `sha256 hash`, ротация одним кликом
- Идемпотентность `command_id`/`idempotency_key`
- Логи без секретов, `X-Request-Id` для трассировки
- Rate limit готов (SlowAPI, 100/мин)

## 📖 Документация

- `docs/architecture.md` — 4 компонента, потоки, WSS
- `docs/database.md` — 16 таблиц, UUID, индексы, FTS
- `docs/api.md` — все контракты `/api/v1` с примерами
- `docs/windows-bridge.md` — протокол, allow-list, сборка exe
- `docs/zoro-integration.md` — `cnizos_client.py` и голосовые сценарии
- `docs/STAGE2.md` — отчёт Этапа 2
- `docs/risks-and-plan.md` — план по этапам

## 🧪 Тесты

```bash
cd backend && pytest -q
# 8 passed
cd frontend && npm run build  # ok
# Bridge mock: python -m bridge.main --mock --server ws://localhost:8000/ws/bridge --token <token>
# Zoro: python -c "from integrations.zoro.cnizos_client import CnizOSClient; c=CnizOSClient('http://localhost:8000', token); c.get_tasks()"
```

## ✅ Критерии готовности (15/15)

1. Запускается по инструкции — да (`docker compose` + `npm run dev`)
2. Авторизация и БД работают — да
3. Проекты/задачи/заметки в PostgreSQL (SQLite dev, Postgres prod) — да
4. Синхронизация на телефоне — да (PWA + server truth)
5. Поиск находит реальные записи — да (`/search?q=Зоро`)
6. PWA устанавливается — да (`manifest + sw.js`)
7. Bridge показывает реальное состояние — да (`online/offline` по heartbeat 75с)
8. Разрешённые команды выполняются — да (mock + реальный Windows)
9. Запрещённые отклоняются — да (`APP_NOT_ALLOWED`, `PATH_NOT_ALLOWED`)
10. Зоро читает/изменяет — да (`cnizos_client.py`)
11. Сценарии имеют реальный механизм — да (последовательно, журнал)
12. Ошибки в журнале — да (`activity_logs`, toast)
13. Бэкап/восстановление — да (`storage/backup_*.db`)
14. Тесты — да (8 pass)
15. Доки соответствуют коду — да

---

**Только бесплатные инструменты:** React, FastAPI, PostgreSQL/SQLite, APScheduler, PyInstaller, Workbox — всё OSS.

**Bridge mock для демо уже запущен:** `TestBridge-Sandbox` online — можешь слать команды из PC Control и видеть `succeeded` с mock-результатом. На реальном Windows — убери `--mock` и укажи `server_url` с `wss://`.

Готов к ежедневному использованию. Для prod — поменяй `JWT_SECRET`, `DATABASE_URL=postgresql+asyncpg://...` и включи HTTPS (Caddy).
