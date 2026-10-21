import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone

# Хрень сгенереная чатом гпт, работает и слава богу


# --- Загрузка переменных окружения ---
load_dotenv("app/.env")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env")

# --- Пути к файлам ---
teachers_file = Path("teachers.json")
users_file = Path("db.json")
backup_dir = Path(os.getenv("BACKUP_DIR", "backups"))

def backup_tables(conn, label):
    """Save all application tables before and after migration."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = backup_dir / f"postgres-{label}-{timestamp}.json"
    tables = {}
    with conn.cursor() as backup_cur:
        for table in ("users", "teachers", "grades"):
            backup_cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                (table,)
            )
            if not backup_cur.fetchone()[0]:
                continue
            backup_cur.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in backup_cur.description]
            tables[table] = [
                dict(zip(columns, row, strict=True)) for row in backup_cur.fetchall()
            ]
    path.write_text(json.dumps(tables, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    print(f"✅ Бэкап {label}: {path}")

# --- Подключение к PostgreSQL ---
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
backup_tables(conn, "before")

# --- Создание таблиц с уникальными ограничениями ---
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    group_name TEXT,
    interface TEXT NOT NULL DEFAULT 'classic'
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS subgroup INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS interface TEXT NOT NULL DEFAULT 'classic';

-- Таблица преподавателей
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    hash CHAR(32) NOT NULL,
    average REAL DEFAULT 0.0
);

-- Таблица оценок
CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    teacher_id INT NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    grade INT NOT NULL,
    CONSTRAINT grades_teacher_user_unique UNIQUE (teacher_id, user_id)
);
""")

# --- Загрузка teachers.json ---
if teachers_file.exists():
    with open(teachers_file, "r", encoding="utf-8") as f:
        teachers = json.load(f)

    teachers_data = [
        (name, data["slug"], data["hash"], data.get("average", 0.0))
        for name, data in teachers.items()
    ]

    execute_values(
        cur,
        """
        INSERT INTO teachers (full_name, slug, hash, average)
        VALUES %s
        ON CONFLICT (slug) DO NOTHING
        """,
        teachers_data
    )
    print(f"✅ Залито {len(teachers_data)} преподавателей")
else:
    print("⚠ teachers.json не найден")

# --- Загрузка db.json ---
if users_file.exists():
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)

    users_data = [(int(uid), group) for uid, group in users.items()]

    execute_values(
        cur,
        """
        INSERT INTO users (id, group_name)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET group_name = EXCLUDED.group_name
        """,
        users_data
    )
    print(f"✅ Залито {len(users_data)} пользователей")
else:
    print("⚠ db.json не найден")

conn.commit()
cur.close()
conn.close()

conn = psycopg2.connect(DATABASE_URL)
backup_tables(conn, "after")
conn.close()
print("🎉 Миграция завершена")
