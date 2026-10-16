# CnizOS — API Контракты (v1)

**Base URL:** `https://cnizos.example.com/api/v1` (локально `http://localhost:8000/api/v1`)  
**Auth:** `Authorization: Bearer <access_token>` + `refresh_token` в HttpOnly cookie  
**Формат ошибок:**
```json
{
  "detail": "Человеко-читаемое сообщение",
  "code": "VALIDATION_ERROR",
  "request_id": "uuid"
}
```
**Пагинация:** `?page=1&limit=20` (max 100), ответ включает `X-Total-Count` и `meta: {page, limit, total}`

---

## 1. Auth

### POST /api/v1/auth/setup — первичная настройка владельца
- Работает только если `users` пуста, иначе 403.
- Body: `{ email, password (min 8), display_name? }`
- Res 201: `{ user, access_token }` + Set-Cookie refresh

### POST /api/v1/auth/login
- Body: `{ email, password }`
- Res 200: `{ access_token, user }`

### POST /api/v1/auth/refresh
- Cookie: `refresh_token`
- Res 200: `{ access_token }` (ротация refresh)

### POST /api/v1/auth/logout
- Инвалидирует refresh

### GET /api/v1/auth/sessions
- Список активных сессий

### DELETE /api/v1/auth/sessions/{id}
- Отзыв сессии

---

## 2. Projects

### GET /api/v1/projects
- Query: `?status=active&category=app&priority=high&q=phanta&page=1&limit=20&archived=false`
- Res: `{ data: Project[], meta }`
- Project:
```json
{
  "id": "uuid",
  "title": "PHANTASMAGORIA",
  "slug": "phantasmagoria",
  "description": "...",
  "category": "creative",
  "status": "active",
  "priority": "high",
  "links": [{"label":"GitHub","url":"https://..."}],
  "local_path": "C:\\Projects\\PHANTASMAGORIA",
  "github_url": "https://...",
  "deadline": "2026-12-01",
  "created_at": "2026-10-12T00:00:00Z",
  "updated_at": "..."
}
```

### POST /api/v1/projects
- Body: `{ title, description?, category?, status?, priority?, links?, local_path?, github_url?, deadline? }`
- Валидация `local_path` — только префикс из `allowed_directories` (если указан)

### GET /api/v1/projects/{id}
### PATCH /api/v1/projects/{id}
- Partial, с `If-Match` для конфликтов

### DELETE /api/v1/projects/{id}
- Мягкое: ставит `archived_at`. Query `?hard=true` — жёсткое (требует подтверждение)

### GET /api/v1/projects/{id}/tasks
### GET /api/v1/projects/{id}/notes

---

## 3. Tasks (Planner)

### GET /api/v1/tasks
- Query: `?status=todo&priority=high&project_id=uuid&due_before=2026-10-20&due_after=2026-10-10&tags=urgent&q=исправить&overdue=true&page=1`
- Спец-фильтры: `?view=today|overdue|upcoming|done`

### POST /api/v1/tasks
```json
{
  "title": "Исправить сайт",
  "description": "...",
  "status": "todo",
  "priority": "high",
  "project_id": "uuid?",
  "due_date": "2026-10-13T09:00:00Z",
  "tags": ["site"],
  "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO",
  "reminders": [{"remind_at":"2026-10-12T08:00:00Z","channel":"in_app"}]
}
```

### GET /api/v1/tasks/{id}
### PATCH /api/v1/tasks/{id}
### DELETE /api/v1/tasks/{id}

### POST /api/v1/tasks/{id}/reminders
### GET /api/v1/tasks/calendar?from=2026-10-01&to=2026-10-31 — для календаря

---

## 4. Notes (Memory)

### GET /api/v1/notes
- Query: `?type=tech&collection=Zoro&is_pinned=true&tag=ошибка&archived=false&q=музыка&page=1`

### POST /api/v1/notes
```json
{
  "title": "Ошибка Зоро — не слышит",
  "body": "## Симптомы\n...",
  "type": "bug",
  "collection": "Zoro",
  "is_pinned": false,
  "tag_ids": ["uuid"],
  "project_ids": ["uuid"]
}
```

### GET /api/v1/notes/{id}
### PATCH /api/v1/notes/{id}
### DELETE /api/v1/notes/{id}
- Мягкое архивирование

### GET /api/v1/notes/{id}/history — история изменений (из activity_logs)

---

## 5. Search (глобальный)

### GET /api/v1/search?q=проверить%20дизайн&types=notes,projects,tasks&limit=20
- Использует `ts_rank` по `notes.body_tsv` + ILIKE по titles
- Res:
```json
{
  "query": "проверить дизайн",
  "results": [
    {"type":"note","id":"uuid","title":"...","snippet":"...проверить <mark>дизайн</mark>...","url":"/memory/uuid","score":0.9},
    {"type":"project","id":"uuid","title":"PHANTASMAGORIA","snippet":"...","url":"/projects/slug","score":0.7}
  ]
}
```

---

## 6. Dashboard

### GET /api/v1/dashboard/layouts
### POST /api/v1/dashboard/layouts
### GET /api/v1/dashboard/layouts/{id}
### PATCH /api/v1/dashboard/layouts/{id}
### POST /api/v1/dashboard/layouts/{id}/widgets — массовое сохранение
```json
{
  "widgets": [
    {"type":"today_tasks","position":0,"config":{"w":2,"h":1}},
    {"type":"bridge_status","position":1,"config":{}}
  ]
}
```

### GET /api/v1/dashboard/summary — агрегаты для виджетов
```json
{
  "today_tasks": 3,
  "overdue_tasks": 1,
  "upcoming_deadlines": [{"title":"...","date":"..."}],
  "active_projects": 5,
  "recent_notes": [...],
  "bridge_status": "online",
  "recent_commands": [...],
  "reminders": [...]
}
```

---

## 7. Devices

### POST /api/v1/devices/register
- Body: `{ name, platform, push_subscription? }`
### GET /api/v1/devices
### DELETE /api/v1/devices/{id}

---

## 8. Bridge

### GET /api/v1/bridge/devices — список Bridge
### POST /api/v1/bridge/devices — регистрация нового (возвращает `bridge_token` один раз)
```json
{
  "name": "Main PC",
  "allowed_apps": [{"id":"vscode","label":"VS Code","exec":"C:\\...\\Code.exe"}],
  "allowed_directories": ["C:\\Projects","D:\\Creative"]
}
```
### GET /api/v1/bridge/devices/{id}
### PATCH /api/v1/bridge/devices/{id} — обновить allow-lists
### POST /api/v1/bridge/devices/{id}/rotate — ротация токена
### GET /api/v1/bridge/status — общий статус (для header)
```json
{"connected": true, "devices": [{"id":"uuid","name":"Main PC","status":"online","last_heartbeat_at":"..."}]}
```

### GET /api/v1/bridge/actions — каталог действий
```json
[
  {"id":"app.launch","description":"Запуск приложения","params_schema":{"app_id":"string"},"requires_confirmation":false},
  {"id":"system.volume.set","params_schema":{"level":"int 0-100"}}
]
```

### POST /api/v1/bridge/commands
```json
{"bridge_id":"uuid","action":"app.launch","params":{"app_id":"vscode"},"idempotency_key":"uuid?"}
```
- Res 202: `{ command_id, status:"queued" }`

### GET /api/v1/bridge/commands — история
- Query: `?bridge_id=uuid&status=succeeded&limit=20`

### GET /api/v1/bridge/commands/{id} — статус

### WebSocket /ws/bridge
- Bridge → Server: `{"type":"auth","token":"..."}`
- Server → Bridge: `{"type":"command","id":"...","action":"...","params":{}}`
- Bridge → Server: `{"type":"result","id":"...","status":"succeeded","result":{}}` + `{"type":"heartbeat","system_info":{}}`
- Фронт WebSocket `/ws/events` (JWT): события `command:update`, `task:created` и т.д.

---

## 9. Zoro (scope: zoro)

- Аутентификация: `Authorization: Bearer <zoro_token>` (отдельный от user JWT)
- Все эндпоинты проксируют основную логику, но с ограниченным scope

### GET /api/v1/zoro/tasks?view=today
### POST /api/v1/zoro/tasks
### PATCH /api/v1/zoro/tasks/{id}
### GET /api/v1/zoro/notes/search?q=...
### POST /api/v1/zoro/notes
### GET /api/v1/zoro/projects?q=...
### GET /api/v1/zoro/projects/{id}
### POST /api/v1/zoro/actions/execute
```json
{"action":"app.launch","params":{"app_id":"vscode"},"confirm":true}
```
### GET /api/v1/zoro/bridge/status
### GET /api/v1/zoro/history — последние команды/ошибки

---

## 10. Creative

### GET /api/v1/creative/assets?type=music&collection=album1&project_id=uuid&q=...
### POST /api/v1/creative/assets — multipart/form-data или JSON с external_url
### GET /api/v1/creative/assets/{id}
### PATCH /api/v1/creative/assets/{id}
### DELETE /api/v1/creative/assets/{id}
### POST /api/v1/creative/collections

### POST /api/v1/creative/assets/{id}/upload — загрузка файла
- Хранится в `storage/creative/{id}/{filename}` (volume), не в БД
- Ограничение: 100MB, проверка MIME

---

## 11. Automation

### GET /api/v1/automation/scenarios
### POST /api/v1/automation/scenarios
```json
{
  "name":"Режим разработки",
  "trigger_type":"manual",
  "steps":[
    {"action":"app.launch","params":{"app_id":"vscode"},"position":0},
    {"action":"folder.open","params":{"path":"C:\\Projects\\PHANTASMAGORIA"},"position":1},
    {"action":"system.volume.set","params":{"level":40},"position":2}
  ]
}
```
### GET /api/v1/automation/scenarios/{id}
### PATCH /api/v1/automation/scenarios/{id}
### DELETE /api/v1/automation/scenarios/{id}
### POST /api/v1/automation/scenarios/{id}/run — запуск, Res 202 `{ run_id }`
### GET /api/v1/automation/runs?scenario_id=uuid
### GET /api/v1/automation/runs/{id}
### POST /api/v1/automation/runs/{id}/cancel

---

## 12. Settings

### GET /api/v1/settings
### PATCH /api/v1/settings — тема, акцент, плотность
### GET /api/v1/settings/activity?limit=50
### POST /api/v1/settings/backup — создаёт dump
### POST /api/v1/settings/restore — загрузка dump (требует подтверждение)

---

## Коды ошибок

- `AUTH_REQUIRED` 401
- `FORBIDDEN` 403
- `NOT_FOUND` 404
- `VALIDATION_ERROR` 422
- `CONFLICT` 409 (If-Match)
- `RATE_LIMITED` 429
- `BRIDGE_OFFLINE` 502
- `COMMAND_EXPIRED` 504

Все ответы — JSON, `Content-Type: application/json`, `X-Request-Id` header.
