#!/usr/bin/env python3
import asyncio, json, sys, argparse, pathlib, os, time, logging, uuid, hashlib
from datetime import datetime, timezone
import websockets

from .config import load_config, save_config, get_config_path, DEFAULT_CONFIG
from .commands import execute_action, BridgeError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("cnizos-bridge")

HEARTBEAT_INTERVAL = 25
RECONNECT_BASE = 1

processed_ids = set()

async def get_system_info():
    try:
        import psutil
        import shutil
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        free_gb = shutil.disk_usage("C:\\" if os.name=="nt" else "/").free / (1024**3)
        # try volume
        vol = None
        try:
            if os.name=="nt":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                vol = int(volume.GetMasterVolumeLevelScalar()*100)
        except: vol=None
        return {"cpu_percent": cpu, "ram_percent": ram, "disk_free_gb": round(free_gb,1), "volume_level": vol}
    except:
        return {}

async def bridge_loop(cfg, mock=False):
    server_url = cfg["server_url"]
    token = cfg["bridge_token"]
    if not token:
        log.error("bridge_token пуст — выполни --setup")
        return
    delay = RECONNECT_BASE
    while True:
        try:
            log.info(f"Подключение к {server_url} ...")
            async with websockets.connect(server_url) as ws:
                log.info("WSS подключён")
                await ws.send(json.dumps({"type":"auth","token":token,"version":"1.0.0","hostname": os.getenv("COMPUTERNAME","unknown")}))
                resp = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(resp)
                if msg.get("type") != "auth_ok":
                    log.error(f"Auth failed: {msg}")
                    await asyncio.sleep(10)
                    continue
                bridge_id = msg.get("bridge_id")
                log.info(f"Auth ok bridge_id={bridge_id}")
                delay = RECONNECT_BASE

                # heartbeat task
                async def heartbeat():
                    while True:
                        await asyncio.sleep(cfg.get("heartbeat_interval", HEARTBEAT_INTERVAL))
                        info = await get_system_info()
                        await ws.send(json.dumps({"type":"heartbeat","system_info": info, "timestamp": datetime.now(tz=timezone.utc).isoformat()}))
                hb = asyncio.create_task(heartbeat())

                try:
                    async for raw in ws:
                        msg = json.loads(raw)
                        if msg.get("type") == "command":
                            cid = msg["id"]
                            action = msg["action"]
                            params = msg.get("params",{})
                            if cid in processed_ids:
                                log.info(f"Повтор команды {cid} — игнор")
                                # send cached? just ack
                                continue
                            log.info(f"Команда {cid}: {action} {params}")
                            # ack running
                            await ws.send(json.dumps({"type":"ack","id": cid, "status":"running","started_at": datetime.now(tz=timezone.utc).isoformat()}))
                            try:
                                result = execute_action(action, params, cfg["allowed_apps"], cfg["allowed_directories"], mock=mock)
                                await ws.send(json.dumps({"type":"result","id": cid, "status":"succeeded","result": result, "finished_at": datetime.now(tz=timezone.utc).isoformat()}))
                                processed_ids.add(cid)
                                log.info(f"Команда {cid} succeeded: {result}")
                            except BridgeError as be:
                                await ws.send(json.dumps({"type":"result","id": cid, "status":"failed","error_code": be.code, "error_message": be.message, "finished_at": datetime.now(tz=timezone.utc).isoformat()}))
                                processed_ids.add(cid)
                                log.warning(f"Команда {cid} failed: {be.code} {be.message}")
                            except Exception as e:
                                await ws.send(json.dumps({"type":"result","id": cid, "status":"failed","error_code":"INTERNAL","error_message": str(e), "finished_at": datetime.now(tz=timezone.utc).isoformat()}))
                                processed_ids.add(cid)
                        elif msg.get("type") == "ping":
                            await ws.send(json.dumps({"type":"pong"}))
                finally:
                    hb.cancel()
        except Exception as e:
            log.error(f"Соединение потеряно: {e} — переподключение через {delay}s")
            await asyncio.sleep(delay)
            delay = min(delay*2, 30)

def main():
    parser = argparse.ArgumentParser(description="CnizOS Bridge")
    parser.add_argument("--setup", action="store_true", help="Настроить токен")
    parser.add_argument("--server", help="WSS URL")
    parser.add_argument("--token", help="Bridge token")
    parser.add_argument("--mock", action="store_true", help="Мок-режим (без реального запуска)")
    parser.add_argument("--install-autostart", action="store_true", help="Установить в автозагрузку")
    args = parser.parse_args()

    if args.setup:
        cfg = load_config()
        if args.server:
            cfg["server_url"] = args.server
        if args.token:
            cfg["bridge_token"] = args.token
        else:
            # ask
            if not cfg["bridge_token"]:
                print("Вставь bridge_token из веб-интерфейса (PC Control → Register):")
                cfg["bridge_token"] = input().strip()
        save_config(cfg)
        print(f"Конфиг сохранён: {get_config_path()}")
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return

    if args.install_autostart:
        if os.name == "nt":
            import pathlib
            startup = pathlib.Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            startup.mkdir(parents=True, exist_ok=True)
            exe = pathlib.Path(sys.executable).resolve()
            bat = startup / "CnizOS-Bridge.bat"
            bat.write_text(f'@echo off\n"{exe}" --mock\n', encoding="utf-8")
            print(f"Автозагрузка: {bat}")
        else:
            print("Автозагрузка только для Windows")
        return

    cfg = load_config()
    if args.server:
        cfg["server_url"] = args.server
    if args.token:
        cfg["bridge_token"] = args.token
    mock = args.mock or cfg.get("mock", False)
    if mock:
        print(">>> МОК-РЕЖИМ: команды не запускают реальные приложения")
    # also allow env override
    if os.getenv("CNIZOS_MOCK"):
        mock = True
    asyncio.run(bridge_loop(cfg, mock=mock))

if __name__ == "__main__":
    main()
