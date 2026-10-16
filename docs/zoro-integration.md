# CnizOS — Интеграция голосового помощника Зоро

**Статус окружения:** Исходный код Зоро в текущем workspace **не обнаружен** (пустой `/home/user`). Поэтому интеграция проектируется как **неразрушающее расширение** через отдельный модуль.

---

## 1. Принцип интеграции

> Не переписывать Зоро, а дать ему **память и руки** через CnizOS.

Зоро остаётся своим процессом (распознавание речи, TTS, локальные команды). Новый файл `cnizos_client.py` — его **единственная точка контакта** с CnizOS.

```
[Микрофон] → [Zoro STT] → [Intent Parser] → [cnizos_client.py] → [CnizOS Backend /api/v1/zoro/*]
                                           → [локальные действия Зоро (без изменений)]
```

**Преимущества:**
- Зоро работает и без CnizOS (деградация).
- Вся бизнес-логика — на сервере, Зоро — тонкий клиент.
- Легко тестировать: мок `cnizos_client.py`.

---

## 2. Модуль `integrations/zoro/cnizos_client.py`

### Конфиг (`zoro_config.json` рядом с Зоро):
```json
{
  "cnizos_url": "https://cnizos.example.com",
  "zoro_token": "Bearer_токен_из_Settings_в_CnizOS",
  "timeout": 5,
  "confirm_dangerous": true
}
```

### API клиента (сигнатуры соответствуют реальному Backend):

```python
from cnizos_client import CnizOSClient

client = CnizOSClient(base_url="https://cnizos.example.com", token="...")

# Задачи
tasks = client.get_tasks(view="today")  # GET /api/v1/zoro/tasks
task = client.create_task(title="Исправить сайт", due_date="2026-10-13T09:00:00Z", priority="high")
client.update_task(task_id, status="done")
client.get_task(task_id)

# Заметки
notes = client.search_notes(q="управление музыкой", limit=5)  # FTS
note = client.create_note(title="Проверить дизайн", body="...", type="idea", project_ids=[...])
note = client.get_note(note_id)

# Проекты
projects = client.list_projects(q="Зоро")
project = client.get_project(project_id) # или slug

# Bridge / действия
status = client.get_bridge_status()  # {connected, devices}
result = client.execute_action(action="app.launch", params={"app_id":"vscode"})  # POST /api/v1/zoro/actions/execute
history = client.get_history(limit=20)

# Поиск глобальный
results = client.search(q="ошибка Зоро")
```

**Обработка ошибок:**
- `CnizOSError` базовый, подтипы `AuthError`, `NotFound`, `BridgeOffline`, `ServerUnavailable`.
- При недоступности — Зоро отвечает голосом: «CnizOS сейчас недоступен, я записал задачу локально и синхронизирую позже» (локальная очередь в `zoro_pending.json`).

---

## 3. Голосовые сценарии

| Фраза пользователя | Intent | Вызов клиента | Ответ Зоро |
|---|---|---|---|
| «Зоро, сохрани заметку: проверить новый дизайн» | `create_note` | `create_note(title="Проверить новый дизайн", type="note")` | «Сохранил заметку „Проверить новый дизайн“» |
| «Зоро, добавь задачу на завтра — исправить сайт» | `create_task` | `create_task(title="Исправить сайт", due_date=tomorrow_09:00, priority="medium")` | «Добавил задачу „Исправить сайт“ на завтра, 9 утра» |
| «Зоро, какие задачи у меня на сегодня?» | `get_tasks` | `get_tasks(view="today")` | Перечисляет 3 задачи + просроченные |
| «Зоро, открой проект Зоро» | `open_project` | `list_projects(q="Зоро")` → `execute_action("project.open", {project_id})` | «Открываю проект Зоро в VS Code» |
| «Зоро, найди заметку про управление музыкой» | `search_notes` | `search_notes(q="управление музыкой")` | Читает топ-2 сниппета |
| «Зоро, запусти режим разработки» | `run_scenario` | `execute_action("profile.activate", {profile:"dev"})` | «Запускаю режим разработки: VS Code, проект, громкость 40» |

**Неоднозначность:**
- Если найдено 3 проекта «Зоро» — «Нашёл 3 проекта: Зоро-ассистент, Зоро-сайт, Зоро-тест. Какой открыть?»
- Если команда опасная (`system.volume.set` на 100% в 2 ночи?) — «Подтверди, установить громкость на 100?»

---

## 4. Расширение существующего кода Зоро (минимальное)

Предполагаемая структура Зоро (на основе типовых ассистентов):
```
zoro/
  main.py — цикл listen → recognize → handle
  intents.py — парсинг фраз
  actions.py — локальные действия
  config.py
```

**Шаг интеграции (без переписывания):**

1. Скопировать `integrations/zoro/cnizos_client.py` в папку Зоро.
2. В `intents.py` добавить новые интенты:
```python
INTENTS = [
  # ... существующие
  {"pattern": r"сохрани заметку[: ](.+)", "handler": handle_cnizos_note},
  {"pattern": r"добавь задачу (.+)", "handler": handle_cnizos_task},
  {"pattern": r"какие задачи.*", "handler": handle_cnizos_today},
  {"pattern": r"открой проект (.+)", "handler": handle_cnizos_open_project},
  {"pattern": r"найди заметку (.+)", "handler": handle_cnizos_search},
  {"pattern": r"запусти режим (.+)", "handler": handle_cnizos_profile},
]
```
3. В `actions.py` добавить хэндлеры, каждый — `try: client.xxx() except ServerUnavailable: fallback`.

4. В `main.py` — инициализация `client = CnizOSClient(...)` при старте, проверка `client.get_bridge_status()` в фоне.

**Если Зоро использует другой язык/архитектуру** — план адаптируется после изучения реального кода (см. риски).

---

## 5. Состояния в Zoro Hub (веб)

Фронт показывает реальные статусы (из `/api/v1/zoro/...` и `/bridge/status`):

- `zoro_connected` — Зоро делал запрос за последние 2 мин?
- `bridge_connected` — heartbeat?
- `last_command` — `{ action, status, finished_at }`
- `errors` — последние 20 из `activity_logs` где `action like 'zoro.%' and status=failed`

Никогда не показываем «Зоро работает», если нет данных.

---

## 6. Тест-план интеграции

- [ ] `get_tasks()` — возвращает реальные задачи
- [ ] `create_note()` — заметка появляется в Memory и на странице проекта
- [ ] `search_notes()` — FTS находит
- [ ] `execute_action()` — запускает VS Code через Bridge
- [ ] `BridgeOffline` — корректный голосовой ответ
- [ ] Неоднозначный запрос — уточнение
- [ ] Опасное действие — запрос подтверждения
- [ ] Старые команды Зоро — не сломаны (регресс)
