#!/usr/bin/env python3
"""Настраивает Зоро автоматически. Копирует cnizos_client.py к Зоро и пишет zoro_config.json"""
import argparse, pathlib, shutil, json
parser = argparse.ArgumentParser()
parser.add_argument("--zoro-dir", required=True, help="Путь к папке Зоро где лежит main.py")
parser.add_argument("--url", default="http://localhost:8000")
parser.add_argument("--token", required=True, help="JWT из /login")
args = parser.parse_args()
src = pathlib.Path("integrations/zoro/cnizos_client.py")
dst = pathlib.Path(args.zoro_dir) / "cnizos_client.py"
shutil.copy(src, dst)
print(f"✅ Скопирован {src} → {dst}")
cfg_path = pathlib.Path(args.zoro_dir) / "zoro_config.json"
cfg = {"cnizos_url": args.url, "zoro_token": args.token, "timeout": 5}
cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
print(f"💾 Конфиг Зоро: {cfg_path}")
print("Добавь в intents.py Зоро обработчики из docs/zoro-integration.md §4 и перезапусти Зоро")
