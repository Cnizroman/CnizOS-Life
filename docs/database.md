# CnizOS — Схема базы данных (PostgreSQL 16)

> Все времена — `timestamptz` в UTC. Отображение — в таймзоне пользователя (`settings.timezone`, по умолчанию `Europe/Tallinn`).  
> Все PK — `uuid` (pgcrypto `gen_random_uuid()`).  
> `created_at`/`updated_at` — триггер `set_updated_at()`.

## ER-диаграмма (текстовая)

```
users 1──* sessions
users 1──* devices
users 1──* projects 1──* tasks
users 1──* notes *──* tags (note_tags)
projects *──* notes (project_notes)
projects 1──* assets
users 1──* dashboard_layouts 1──* dashboard_widgets
users 1──* bridge_devices 1──* bridge_commands
bridge_commands *──1 automation_runs (опционально)
users 1──* automation_scenarios 1──* automation_steps 1──* automation_runs
users 1──* activity_logs
users 1──1 integration_settings
```

---

## 1. users — единственный владелец (+ задел на будущее)

```sql
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL CHECK (email ~* '^[^@]+@[^@]+\.[^@]+$'),
  password_hash TEXT NOT NULL,
  display_name TEXT NOT NULL DEFAULT 'Owner',
  timezone TEXT NOT NULL DEFAULT 'Europe/Tallinn',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
-- Изначально 1 запись. Регистрация закрывается после setup.
```

## 2. sessions — refresh-сессии

```sql
CREATE TABLE sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  refresh_token_hash TEXT NOT NULL UNIQUE,
  user_agent TEXT,
  ip INET,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  last_active_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_sessions_user ON sessions(user_id);
```

## 3. devices — браузеры/телефоны (для PWA tracking)

```sql
CREATE TABLE devices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL, -- "Chrome on Windows", "iPhone Safari"
  platform TEXT, -- 'web' | 'pwa' | 'mobile'
  push_subscription JSONB, -- Web Push keys (если есть)
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now()
);
```

## 4. projects

```sql
CREATE TYPE project_status AS ENUM ('idea','active','paused','done','archived');
CREATE TYPE project_priority AS ENUM ('low','medium','high','critical');
CREATE TYPE project_category AS ENUM ('site','app','creative','tool','study','other');

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL CHECK (char_length(title) BETWEEN 2 AND 200),
  slug TEXT NOT NULL UNIQUE, -- генерируется из title
  description TEXT,
  category project_category NOT NULL DEFAULT 'other',
  status project_status NOT NULL DEFAULT 'idea',
  priority project_priority NOT NULL DEFAULT 'medium',
  links JSONB NOT NULL DEFAULT '[]', -- [{label, url}]
  local_path TEXT, -- C:\Projects\X, проверяется Bridge
  github_url TEXT,
  demo_url TEXT,
  started_at DATE,
  deadline DATE,
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_projects_user_status ON projects(user_id, status);
CREATE INDEX ix_projects_deadline ON projects(deadline) WHERE deadline IS NOT NULL;
```

## 5. tasks

```sql
CREATE TYPE task_status AS ENUM ('todo','in_progress','done','cancelled');
CREATE TYPE task_priority AS ENUM ('low','medium','high','urgent');

CREATE TABLE tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 300),
  description TEXT,
  status task_status NOT NULL DEFAULT 'todo',
  priority task_priority NOT NULL DEFAULT 'medium',
  category TEXT, -- свободная строка
  due_date timestamptz,
  completed_at timestamptz,
  recurrence_rule TEXT, -- RRULE (iCal) или NULL
  tags TEXT[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_tasks_user_status ON tasks(user_id, status);
CREATE INDEX ix_tasks_due ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX ix_tasks_project ON tasks(project_id) WHERE project_id IS NOT NULL;
```

## 6. task_reminders

```sql
CREATE TABLE task_reminders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  remind_at timestamptz NOT NULL,
  channel TEXT NOT NULL DEFAULT 'in_app', -- 'in_app' | 'bridge' | 'push'
  delivered_at timestamptz,
  delivery_status TEXT NOT NULL DEFAULT 'pending', -- pending/sent/failed/ack
  attempts INT NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_reminders_remind ON task_reminders(remind_at) WHERE delivery_status='pending';
```

## 7. notes (Memory)

```sql
CREATE TYPE note_type AS ENUM ('note','idea','link','summary','draft','instruction','tech','bug','archive');

CREATE TABLE notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL CHECK (char_length(title) BETWEEN 1 AND 300),
  body TEXT NOT NULL, -- Markdown
  body_tsv tsvector, -- генерируется триггером: to_tsvector('russian', title||' '||body)
  type note_type NOT NULL DEFAULT 'note',
  collection TEXT, -- папка/коллекция
  is_pinned BOOLEAN NOT NULL DEFAULT false,
  is_favorite BOOLEAN NOT NULL DEFAULT false,
  is_archived BOOLEAN NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_notes_tsv ON notes USING GIN(body_tsv);
CREATE INDEX ix_notes_user_type ON notes(user_id, type);
-- Триггер:
-- body_tsv := to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(body,''));
```

## 8. tags & связи

```sql
CREATE TABLE tags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  color TEXT,
  UNIQUE(user_id, name)
);

CREATE TABLE note_tags (
  note_id uuid NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (note_id, tag_id)
);

CREATE TABLE project_notes (
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  note_id uuid NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, note_id)
);
```

## 9. assets (Creative)

```sql
CREATE TYPE asset_type AS ENUM ('music','cover','text','photo','design','video','other');

CREATE TABLE assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  collection TEXT,
  title TEXT NOT NULL,
  description TEXT,
  type asset_type NOT NULL DEFAULT 'other',
  file_path TEXT, -- локальный путь (только для Bridge)
  storage_key TEXT, -- путь в volume/s3: storage/creative/uuid.ext
  external_url TEXT,
  preview_key TEXT, -- превью
  tags TEXT[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_assets_project ON assets(project_id);
```

## 10. dashboard_layouts & widgets

```sql
CREATE TABLE dashboard_layouts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT 'Default',
  is_default BOOLEAN NOT NULL DEFAULT false,
  device_type TEXT NOT NULL DEFAULT 'desktop', -- 'desktop'|'mobile'
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id, name, device_type)
);

CREATE TABLE dashboard_widgets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  layout_id uuid NOT NULL REFERENCES dashboard_layouts(id) ON DELETE CASCADE,
  type TEXT NOT NULL, -- 'clock'|'today_tasks'|'overdue'|'deadlines'|'active_projects'|'recent_notes'|'quick_links'|'zoro_fav'|'bridge_status'|'recent_commands'|'reminders'
  position INT NOT NULL, -- порядок
  config JSONB NOT NULL DEFAULT '{}', -- {w:2,h:1, collapsed:false}
  created_at timestamptz NOT NULL DEFAULT now()
);
```

## 11. bridge_devices

```sql
CREATE TABLE bridge_devices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL, -- "Main PC"
  token_hash TEXT NOT NULL UNIQUE, -- bcrypt
  status TEXT NOT NULL DEFAULT 'offline', -- offline/online
  last_heartbeat_at timestamptz,
  allowed_apps JSONB NOT NULL DEFAULT '[]', -- [{id, label, exec}]
  allowed_directories TEXT[] NOT NULL DEFAULT '{}', -- ['C:\Projects','D:\Creative']
  system_info JSONB, -- последний status.get
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
```

## 12. bridge_commands

```sql
CREATE TYPE command_status AS ENUM ('queued','running','succeeded','failed','cancelled','expired');

CREATE TABLE bridge_commands (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), -- command_id
  bridge_id uuid NOT NULL REFERENCES bridge_devices(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action TEXT NOT NULL, -- app.launch и т.д.
  params JSONB NOT NULL DEFAULT '{}',
  params_safe JSONB, -- для логов (без секретов)
  status command_status NOT NULL DEFAULT 'queued',
  result JSONB,
  error_code TEXT,
  error_message TEXT,
  requested_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz,
  idempotency_key TEXT UNIQUE -- для защиты от повтора, = id по умолчанию
);
CREATE INDEX ix_commands_bridge_status ON bridge_commands(bridge_id, status);
CREATE INDEX ix_commands_user ON bridge_commands(user_id, requested_at DESC);
```

## 13. command_permissions

```sql
CREATE TABLE command_permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bridge_id uuid NOT NULL REFERENCES bridge_devices(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  requires_confirmation BOOLEAN NOT NULL DEFAULT false,
  is_enabled BOOLEAN NOT NULL DEFAULT true,
  UNIQUE(bridge_id, action)
);
```

## 14. automation_scenarios / steps / runs

```sql
CREATE TABLE automation_scenarios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  trigger_type TEXT NOT NULL DEFAULT 'manual', -- manual/schedule/event
  trigger_config JSONB NOT NULL DEFAULT '{}', -- {cron:"0 9 * * *"}
  is_enabled BOOLEAN NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE automation_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id uuid NOT NULL REFERENCES automation_scenarios(id) ON DELETE CASCADE,
  position INT NOT NULL,
  action TEXT NOT NULL, -- app.launch | system.volume.set | ...
  params JSONB NOT NULL DEFAULT '{}',
  continue_on_error BOOLEAN NOT NULL DEFAULT false,
  UNIQUE(scenario_id, position)
);

CREATE TABLE automation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id uuid NOT NULL REFERENCES automation_scenarios(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'running', -- running/succeeded/failed/cancelled
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  error TEXT,
  step_results JSONB NOT NULL DEFAULT '[]' -- [{step_id, status, result}]
);
CREATE INDEX ix_runs_scenario ON automation_runs(scenario_id, started_at DESC);
```

## 15. activity_logs

```sql
CREATE TABLE activity_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL, -- 'project.create' | 'bridge.command'
  entity_type TEXT,
  entity_id uuid,
  meta JSONB NOT NULL DEFAULT '{}', -- без секретов!
  ip INET,
  request_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_logs_user_time ON activity_logs(user_id, created_at DESC);
```

## 16. integration_settings

```sql
CREATE TABLE integration_settings (
  user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  zoro_enabled BOOLEAN NOT NULL DEFAULT true,
  zoro_token_hash TEXT, -- hash токена Zoro
  bridge_auto_connect BOOLEAN NOT NULL DEFAULT true,
  theme TEXT NOT NULL DEFAULT 'dark', -- dark/light
  accent TEXT NOT NULL DEFAULT '#4ADE80',
  density TEXT NOT NULL DEFAULT 'comfortable',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
```

---

## Миграции

- Alembic, одна ветка `head`.
- Начальная миграция — все таблицы выше + `pgcrypto` + `btree_gin`.
- Сид: дефолтный `dashboard_layouts` (desktop/mobile) с 6 виджетами.

## Конфликты и удаление

- **Мягкое удаление:** `archived_at` / `is_archived` вместо DELETE для проектов/заметок. Жёсткое удаление — только через `DELETE ...` с подтверждением.
- **Конфликт:** `updated_at` + `If-Match`. Если клиент шлёт `If-Match: <etag>` и он не совпал — `409 Conflict` с текущим объектом.
