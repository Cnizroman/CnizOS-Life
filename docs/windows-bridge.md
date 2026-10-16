# CnizOS Bridge — Протокол и безопасность

**Язык:** Python 3.13  
**Соединение:** исходящий WSS от Bridge к Backend  
**Сборка:** PyInstaller → `CnizOS-Bridge.exe`  
**Конфиг:** `%APPDATA%\CnizOS\bridge.json` (или рядом с exe для portable)

---

## 1. Почему исходящее соединение

- Не требует открытия портов/проброса NAT.
- Работает за любыми роутерами/файрволами.
- Сервер никогда не подключается напрямую к Windows — только отвечает на уже установленный канал.

Альтернатива (HTTP long-poll) — запасной вариант, если WSS недоступен: `GET /api/v1/bridge/commands/poll?since=...` каждые 5с.

---

## 2. Конфиг Bridge

`bridge.json` (создаётся при первом запуске `bridge.exe --setup`):
```json
{
  "server_url": "wss://cnizos.example.com/ws/bridge",
  "bridge_token": "uuid-v4-секрет",
  "device_name": "Main PC",
  "heartbeat_interval": 25,
  "allowed_apps": [
    {"id": "vscode", "label": "VS Code", "exec": "C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"},
    {"id": "discord", "label": "Discord", "exec": "C:\\Users\\User\\AppData\\Local\\Discord\\Update.exe"},
    {"id": "chrome", "label": "Chrome", "exec": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"}
  ],
  "allowed_directories": [
    "C:\\Projects",
    "D:\\Creative",
    "C:\\Users\\User\\Documents"
  ],
  "log_level": "INFO"
}
```
- `bridge_token` — показывается один раз при регистрации в веб-интерфейсе, далее хранится только хэш на сервере.
- При компрометации — ротация через веб-интерфейс.

---

## 3. Протокол WebSocket

### 3.1 Handshake

Bridge → Server:
```json
{"type": "auth", "token": "bridge_token_uuid", "version": "1.0.0", "hostname": "DESKTOP-ABC"}
```
Server → Bridge:
```json
{"type": "auth_ok", "bridge_id": "uuid", "heartbeat_interval": 25}
-- или --
{"type": "auth_error", "code": "INVALID_TOKEN", "detail": "..."}
```

### 3.2 Heartbeat

Bridge → Server каждые 25с:
```json
{
  "type": "heartbeat",
  "system_info": {
    "cpu_percent": 23.5,
    "ram_percent": 62.1,
    "disk_free_gb": 120.4,
    "volume_level": 42
  },
  "timestamp": "2026-10-12T08:00:00Z"
}
```
Server обновляет `bridge_devices.last_heartbeat_at` и `status=online`. Если нет heartbeat 75с — `offline`.

### 3.3 Команда

Server → Bridge:
```json
{
  "type": "command",
  "id": "uuid-command_id",
  "action": "app.launch",
  "params": {"app_id": "vscode"},
  "request_id": "uuid",
  "issued_at": "2026-10-12T08:01:00Z"
}
```

Bridge проверяет:
1. `action` в каталоге?
2. `params` по JSON-схеме?
3. `app_id` в `allowed_apps`? (для `folder.open` — `path` внутри `allowed_directories` через `Path.resolve()`)

Если нет — сразу результат `failed` с `error_code`.

Bridge → Server (статусы):
```json
{"type": "ack", "id": "uuid", "status": "running", "started_at": "..."}
{"type": "result", "id": "uuid", "status": "succeeded", "result": {"pid": 1234}, "finished_at": "..."}
-- или --
{"type": "result", "id": "uuid", "status": "failed", "error_code": "APP_NOT_ALLOWED", "error_message": "Приложение 'unknown' не в списке разрешённых", "finished_at": "..."}
```

**Идемпотентность:** Bridge хранит `processed_ids` (set в памяти + `shelve` на диск на 24ч). Повтор `id` — вернуть кэшированный результат, не исполнять.

### 3.4 Локальный HTTP (опционально)

Bridge слушает `127.0.0.1:17373` (только loopback) для диагностики:
- `GET /status` — `{ connected, last_heartbeat, allowed_apps }`
- `POST /test` — тест команды локально

Никакого внешнего доступа.

---

## 4. Каталог команд — реализация

### app.launch
```python
def handle_app_launch(params):
    app = find_allowed_app(params["app_id"])
    if not app: raise BridgeError("APP_NOT_ALLOWED")
    proc = subprocess.Popen([app["exec"]], creationflags=subprocess.DETACHED_PROCESS)
    return {"pid": proc.pid, "app_id": app["id"]}
```

### folder.open
```python
def handle_folder_open(params):
    path = Path(params["path"]).resolve()
    if not any(str(path).startswith(str(Path(d).resolve())) for d in allowed_directories):
        raise BridgeError("PATH_NOT_ALLOWED", f"Путь {path} вне разрешённых директорий")
    if not path.exists():
        raise BridgeError("PATH_NOT_FOUND")
    os.startfile(str(path))
    return {"path": str(path)}
```

### project.open
- Backend резолвит `project_id` → `local_path`, Bridge проверяет как `folder.open` + `app.launch` (VS Code с аргументом пути).

### system.volume.set / get
- Использует `pycaw` (Windows Core Audio) или `nircmd` fallback.
- `set`: `volume.SetMasterVolumeLevelScalar(level/100, None)`
- Валидация: `0 <= level <= 100`.

### system.status.get
- `psutil.cpu_percent()`, `virtual_memory()`, `disk_usage()`.

### profile.activate
- Алиас для сценария Automation: исполняет последовательность из `automation_steps`.

---

## 5. Безопасность

| Угроза | Защита |
|---|---|
| Подмена сервера | TLS + проверка сертификата (wss://). Для локальной сети — самоподписанный с pin. |
| Утечка токена | Хранится только на Bridge, на сервере — bcrypt hash. Ротация одним кликом. |
| Произвольный exec | Запрещён. Только allow-list. Никакого `eval`, `shell=True`. |
| Path traversal | `resolve()` + префикс-проверка. `..` не помогут. |
| Повтор команды | `command_id` уникален, Bridge кэширует результат. |
| Flood | Rate limit на `/bridge/commands` — 10/мин. Bridge игнорирует дубли. |
| Логи с секретами | `params_safe` без токенов/путей с секретами. |
| Автостарт | Bridge ставится в автозагрузку через `shell:startup` ярлык или Task Scheduler (опционально). |

---

## 6. Сборка

```bash
# windows-bridge/
pip install -r requirements.txt  # fastapi, websockets, psutil, pycaw, pyinstaller
pyinstaller --onefile --noconsole --name CnizOS-Bridge bridge/main.py
# Результат: dist/CnizOS-Bridge.exe (~15MB)
```

Первый запуск:
```bash
CnizOS-Bridge.exe --setup --server wss://cnizos.example.com/ws/bridge --token <bridge_token>
CnizOS-Bridge.exe --install-autostart
CnizOS-Bridge.exe
```

Логи: `%APPDATA%\CnizOS\bridge.log` (ротация 5MB).

---

## 7. Состояния (конечный автомат команды)

```
queued → running → succeeded
                → failed
                → cancelled (если пользователь отменил до running)
                → expired (если Bridge не ответил за 60с)
```

Фронт никогда не показывает `succeeded` до получения `result` от Bridge.

---

## 8. Тест-план Bridge

- [ ] Успешный запуск разрешённого приложения
- [ ] Отклонение неразрешённого `app_id`
- [ ] Отклонение пути вне allow-list
- [ ] Отклонение `..` traversal
- [ ] Потеря WSS → реконнект с backoff
- [ ] Повторная доставка команды (идемпотентность)
- [ ] Ошибка выполнения (несуществующий exe) → `failed`
- [ ] Heartbeat → `offline` через 75с
