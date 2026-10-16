#!/usr/bin/env python3
import secrets, pathlib
env_example = pathlib.Path(".env.example").read_text()
env_path = pathlib.Path(".env")
if env_path.exists():
    print(".env уже существует — не перезаписываю. Удали его чтобы сгенерировать заново.")
    exit(0)
jwt = secrets.token_hex(32)
pg_pass = secrets.token_hex(16)
zoro = secrets.token_hex(16)
content = env_example.replace("change_me_to_random_64_chars", jwt).replace("change_me_32_bytes_base64", secrets.token_urlsafe(32)).replace("cnizos_secret", pg_pass).replace("change_me_zoro_token", zoro)
# ensure values
content = content.replace("POSTGRES_PASSWORD=cnizos_secret", f"POSTGRES_PASSWORD={pg_pass}")
# write
env_path.write_text(content)
print(f"✅ .env создан")
print(f"JWT_SECRET={jwt[:12]}...")
print(f"POSTGRES_PASSWORD={pg_pass[:8]}...")
print(f"ZORO_TOKEN={zoro[:8]}...")
