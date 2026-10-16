import json, os, pathlib

DEFAULT_CONFIG = {
    "server_url": "wss://cnizos.example.com/ws/bridge",
    "bridge_token": "",
    "device_name": "Main PC",
    "heartbeat_interval": 25,
    "allowed_apps": [
        {"id": "vscode", "label": "VS Code", "exec": "C:\\Program Files\\Microsoft VS Code\\Code.exe"},
        {"id": "discord", "label": "Discord", "exec": "C:\\AppData\\Local\\Discord\\Update.exe"},
        {"id": "chrome", "label": "Chrome", "exec": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"}
    ],
    "allowed_directories": ["C:\\Projects", "D:\\Creative", "C:\\Users\\User\\Documents"],
    "log_level": "INFO"
}

def get_config_path():
    if os.name == "nt":
        base = os.getenv("APPDATA") or str(pathlib.Path.home())
        return pathlib.Path(base) / "CnizOS" / "bridge.json"
    else:
        return pathlib.Path.home() / ".config" / "CnizOS" / "bridge.json"

def load_config():
    p = get_config_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    p = get_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return p
