#!/usr/bin/env python3
"""Создаёт владельца без браузера. Использование: python scripts/create_owner.py --email you@mail.ee --password 'Pass123!'"""
import argparse, httpx, sys
parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--name", default="Owner")
parser.add_argument("--url", default="http://localhost:8000")
args = parser.parse_args()
try:
    r = httpx.post(f"{args.url}/api/v1/auth/setup", json={"email":args.email,"password":args.password,"display_name":args.name}, timeout=5)
    print(r.status_code, r.text)
    if r.status_code in (200,201):
        print(f"✅ Владелец {args.email} создан")
    elif r.status_code==403:
        print("⚠ Владелец уже есть — используй /login")
    sys.exit(0 if r.status_code in (200,201,403) else 1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)
