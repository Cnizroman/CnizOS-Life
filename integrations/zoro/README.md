# Zoro ↔ CnizOS Integration

1. Скопируй `cnizos_client.py` в папку Зоро (`pip install httpx` если нет).
2. В `zoro_config.json` добавь:
```json
{
  "cnizos_url": "https://cnizos.example.com",
  "zoro_token": "Bearer_токен_из_CnizOS_Settings"
}
```
Токен возьми из Settings → Интеграции (хэшируется, показывается один раз как bridge_token).

3. В `main.py` Зоро:
```python
from cnizos_client import CnizOSClient, ServerUnavailable
client = CnizOSClient(base_url=config["cnizos_url"], token=config["zoro_token"])

# интенты
INTENTS = [
  {"pattern": r"сохрани заметку[: ](.+)", "handler": lambda m: client.create_note(title=m.group(1))},
  {"pattern": r"добавь задачу (.+)", "handler": lambda m: client.create_task(title=m.group(1))},
]
```

См. `docs/zoro-integration.md` для всех сценариев.

## Тест без Зоро
```bash
python -c "from cnizos_client import CnizOSClient; c=CnizOSClient('http://localhost:8000','<user_token>'); print(c.get_tasks())"
```
Используй user JWT как zoro_token для теста (scope пока общий).
