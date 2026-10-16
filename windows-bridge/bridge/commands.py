import subprocess, os, sys
from pathlib import Path
from .security import is_path_allowed, is_app_allowed, get_app_exec

class BridgeError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

def handle_app_launch(params, allowed_apps, mock=False):
    app_id = params.get("app_id")
    if not is_app_allowed(app_id, allowed_apps):
        raise BridgeError("APP_NOT_ALLOWED", f"Приложение '{app_id}' не в списке разрешённых")
    exec_path = get_app_exec(app_id, allowed_apps)
    if mock:
        return {"pid": 1234, "app_id": app_id, "mock": True, "exec": exec_path}
    if not exec_path or not Path(exec_path).exists():
        # try to launch via start
        raise BridgeError("APP_NOT_FOUND", f"Исполняемый файл не найден: {exec_path}")
    try:
        if os.name == "nt":
            proc = subprocess.Popen([exec_path], creationflags=subprocess.DETACHED_PROCESS)
        else:
            proc = subprocess.Popen([exec_path])
        return {"pid": proc.pid, "app_id": app_id}
    except Exception as e:
        raise BridgeError("LAUNCH_FAILED", str(e))

def handle_folder_open(params, allowed_dirs, mock=False):
    path = params.get("path")
    if not path:
        raise BridgeError("MISSING_PARAM", "path required")
    if not is_path_allowed(path, allowed_dirs):
        raise BridgeError("PATH_NOT_ALLOWED", f"Путь {path} вне разрешённых директорий")
    p = Path(path)
    if not p.exists() and not mock:
        raise BridgeError("PATH_NOT_FOUND", f"Путь не найден: {path}")
    if mock:
        return {"path": str(p), "mock": True}
    try:
        if os.name == "nt":
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
        return {"path": str(p)}
    except Exception as e:
        raise BridgeError("OPEN_FAILED", str(e))

def handle_system_volume_set(params, mock=False):
    level = params.get("level")
    if not isinstance(level, int) or not (0 <= level <= 100):
        raise BridgeError("INVALID_PARAM", "level must be int 0-100")
    if mock:
        return {"level": level, "mock": True}
    try:
        if os.name == "nt":
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return {"level": level}
        else:
            return {"level": level, "mock": True, "note": "volume only on Windows"}
    except Exception as e:
        raise BridgeError("VOLUME_FAILED", str(e))

def handle_system_volume_get(params, mock=False):
    if mock:
        return {"level": 42, "mock": True}
    try:
        if os.name == "nt":
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level = int(volume.GetMasterVolumeLevelScalar() * 100)
            return {"level": level}
        else:
            return {"level": 42, "mock": True}
    except Exception as e:
        raise BridgeError("VOLUME_GET_FAILED", str(e))

def handle_system_status_get(params, mock=False):
    import psutil
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent
        import shutil
        free_gb = shutil.disk_usage("/").free / (1024**3) if os.name != "nt" else shutil.disk_usage("C:\\").free / (1024**3)
        return {"cpu_percent": cpu, "ram_percent": ram, "disk_percent": disk, "disk_free_gb": round(free_gb,1)}
    except Exception as e:
        raise BridgeError("STATUS_FAILED", str(e))

DISPATCH = {
    "app.launch": handle_app_launch,
    "folder.open": handle_folder_open,
    "system.volume.set": handle_system_volume_set,
    "system.volume.get": handle_system_volume_get,
    "system.status.get": handle_system_status_get,
}

def execute_action(action: str, params: dict, allowed_apps, allowed_dirs, mock=False):
    if action not in DISPATCH:
        raise BridgeError("UNKNOWN_ACTION", f"Unknown action {action}")
    h = DISPATCH[action]
    # dispatch with correct args
    if action == "app.launch":
        return h(params, allowed_apps, mock=mock)
    elif action == "folder.open":
        return h(params, allowed_dirs, mock=mock)
    elif action in ("system.volume.set", "system.volume.get", "system.status.get"):
        return h(params, mock=mock)
    else:
        return h(params, mock=mock)
