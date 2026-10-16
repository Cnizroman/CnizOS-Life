#!/usr/bin/env python3
"""Регистрирует Bridge и сохраняет bridge.json автоматически. 
Использование: python scripts/register_bridge.py --email owner@cnizos.local --password Cnizos123! --name "Main PC"
"""
import argparse, httpx, json, pathlib, os
parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--name", default="Main PC")
parser.add_argument("--url", default="http://localhost:8000")
parser.add_argument("--server", default="ws://localhost:8000/ws/bridge")
args = parser.parse_args()

# login
r = httpx.post(f"{args.url}/api/v1/auth/login", json={"email":args.email,"password":args.password})
r.raise_for_status()
token = r.json()["access_token"]
# register
r = httpx.post(f"{args.url}/api/v1/bridge/devices", headers={"Authorization": f"Bearer {token}"}, json={
    "name": args.name,
    "allowed_apps": [{"id":"vscode","label":"VS Code","exec":"C:\\Program Files\\Microsoft VS Code\\Code.exe"}],
    "allowed_directories": ["C:\\Projects","D:\\Creative"]
})
r.raise_for_status()
data = r.json()
bridge_token = data["bridge_token"]
bid = data["id"]
print(f"✅ Bridge {args.name} id={bid}")
print(f"bridge_token={bridge_token}")
# save config
if os.name=="nt":
    path = pathlib.Path(os.getenv("APPDATA")) / "CnizOS" / "bridge.json"
else:
    path = pathlib.Path.home() / ".config" / "CnizOS" / "bridge.json"
path.parent.mkdir(parents=True, exist_ok=True)
cfg = {"server_url": args.server, "bridge_token": bridge_token, "device_name": args.name, "heartbeat_interval": 25, "allowed_apps": [{"id":"vscode","label":"VS Code","exec":"C:\\Program Files\\Microsoft VS Code\\Code.exe"}], "allowed_directories": ["C:\\Projects","D:\\Creative"]}
path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"💾 Конфиг сохранён: {path}")
print("Запусти: python -m bridge.main  (в windows-bridge/) или CnizOS-Bridge.exe")
