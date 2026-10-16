# Установка CnizOS (черновик для Этапа 8)

Пока — план. Реальная инструкция будет проверена на чистой машине.

## Локально (разработка)

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d
cd backend && pip install -r requirements.txt && alembic upgrade head
uvicorn app.main:app --reload  # :8000
cd ../frontend && npm install && npm run dev  # :5173
```

## Продакшн (VPS)

- HTTPS через Caddy/Nginx + Let's Encrypt
- `DATABASE_URL` на внешний Postgres
- `JWT_SECRET` сгенерировать: `openssl rand -hex 32`
- Бэкап: `pg_dump | gzip > backup.sql.gz` + cron
