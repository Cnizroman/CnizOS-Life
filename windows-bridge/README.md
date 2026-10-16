# CnizOS Bridge — Windows

Подключается к backend по WSS (исходящее), выполняет только разрешённые команды.

## Установка

```bash
pip install -r requirements.txt
python -m bridge.main --setup --server wss://твой-домен/ws/bridge --token <bridge_token>
python -m bridge.main --mock  # тест без Windows
python -m bridge.main --install-autostart  # автозагрузка
```

Сборка exe:
```bash
pyinstaller --onefile --noconsole --name CnizOS-Bridge bridge/main.py
```

## Команды
- app.launch, folder.open, project.open, system.volume.set/get, system.status.get, profile.activate
