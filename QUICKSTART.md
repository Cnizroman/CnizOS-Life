# CnizOS — Минимальные шаги (3 команды)

> Всё уже сгенерировано. Тебе осталось 5 минут.

### 1. Скачай и запусти
```bash
# скачай папку cnizos с Arena (Download) и распакуй
cd cnizos
bash install.sh
# → создаст .env, запустит postgres+backend, соберёт frontend, создаст владельца owner@cnizos.local / Cnizos123!
```

**Без Docker (если нет Docker):**
```bash
bash install.sh
# сам поставит SQLite-режим
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
# открой http://localhost:5173
```

### 2. Подключи Windows (1 клик)
На компе Windows:
```
1. Открой http://localhost:5173 → PC Control → + Register → скопируй token
2. Запусти windows-bridge/install.bat → вставь token → Enter
3. Всё — статус станет online, команды работают
```
Без Windows — тест: `python windows-bridge/bridge/main.py --mock --server ws://localhost:8000/ws/bridge --token <token>`

### 3. Подключи Зоро (1 команда)
```bash
python scripts/zoro_setup.py --zoro-dir /путь/к/Зоро --token <JWT_из_login> --url http://localhost:8000
# добавь 6 строк в intents.py Зоро как в docs/zoro-integration.md и перезапусти Зоро
```

### Готово
- Телефон: открой `http://<твой-IP>:5173` → **Установить** (PWA)
- Бэкап: `make backup` или `curl -X POST http://localhost:8000/api/v1/settings/backup -H "Authorization: Bearer <token>"`
- Тесты: `make test`

**Что менять не надо:** `.env` уже с секретами, `cnizos.db` уже с демо-проектом, Bridge mock уже online в песочнице.

Если хочешь свой email вместо `owner@cnizos.local`:
```bash
python scripts/create_owner.py --email you@mail.ee --password 'НовыйПароль12!'
```
