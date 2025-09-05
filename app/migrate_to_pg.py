import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from pathlib import Path

# --- Загрузка переменных окружения ---
load_dotenv("app/.env")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env")

# --- Пути к файлам ---
teachers_file = Path("teachers.json")
users_file = Path("db.json")

# --- Подключение к PostgreSQL ---
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# --- Создание таблиц с уникальными ограничениями ---
cur.execute("""
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    group_name TEXT,
    subgroup INT DEFAULT 1
);

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

# --- Добавление недостающей колонки subgroup (если её нет) ---
cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'subgroup'
    ) THEN
        ALTER TABLE users ADD COLUMN subgroup INT DEFAULT 1;
        UPDATE users SET subgroup = 1; -- выставляем всем существующим
    END IF;
END$$;
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

    users_data = [(int(uid), group, 1) for uid, group in users.items()]

    execute_values(
        cur,
        """
        INSERT INTO users (id, group_name, subgroup)
        VALUES %s
        ON CONFLICT (id) DO UPDATE 
        SET group_name = EXCLUDED.group_name,
            subgroup = COALESCE(users.subgroup, EXCLUDED.subgroup)
        """,
        users_data
    )
    print(f"✅ Залито {len(users_data)} пользователей")
else:
    print("⚠ db.json не найден")

conn.commit()
cur.close()
conn.close()

print("🎉 Миграция завершена")
