import os
import asyncpg
from dotenv import load_dotenv
from typing import Optional, Tuple, List, Dict

load_dotenv("app/.env")
DATABASE_URL = os.getenv("DATABASE_URL")

class Database: # Класс бд для работы с студентами и преподавателями и их оцценками
    def __init__(self):
        self.pool = None

    async def init(self):
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL не найден в .env")
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    # --- users ---
    async def set_group(self, user_id: int, group: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, group_name)
                VALUES ($1, $2)
                ON CONFLICT (id) DO UPDATE
                    SET group_name = EXCLUDED.group_name
                """,
                user_id, group
            )

    async def get_group(self, user_id: int) -> Optional[str]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT group_name FROM users WHERE id = $1",
                user_id
            )
            return row["group_name"] if row else None

    async def delete_user(self, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)

    async def all_users(self) -> Dict[str, str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, group_name FROM users")
            return {str(row["id"]): row["group_name"] for row in rows}

    async def ensure_user(self, user_id: int, group: str = None) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, group_name)
                VALUES ($1, $2)
                ON CONFLICT (id) DO NOTHING
                """,
                user_id, group
            )

    async def user_exists(self, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT 1 FROM users WHERE id = $1", user_id)
            return row is not None
        
    async def set_subgroup(self, user_id: int, subgroup) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET subgroup = $2 WHERE id = $1",
                user_id, int(subgroup)
            )

    async def get_subgroup(self, user_id: int) -> Optional[int]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT subgroup FROM users WHERE id = $1", user_id)
            return row["subgroup"] if row else None


    # --- teachers ---
    async def add_teacher_rating(self, full_name: str, grade: int, user_id: int) -> Tuple[float, int]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                teacher = await conn.fetchrow("SELECT id FROM teachers WHERE full_name = $1", full_name)
                if not teacher:
                    teacher_id = await conn.fetchval(
                        "INSERT INTO teachers (full_name, slug, hash) VALUES ($1, '', '') RETURNING id",
                        full_name
                    )
                else:
                    teacher_id = teacher["id"]

                await conn.execute(
                    """
                    INSERT INTO grades (teacher_id, user_id, grade)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (teacher_id, user_id) DO UPDATE SET grade = EXCLUDED.grade
                    """,
                    teacher_id, user_id, grade
                )

                stats = await conn.fetchrow(
                    "SELECT AVG(grade) AS avg, COUNT(grade) AS count FROM grades WHERE teacher_id = $1",
                    teacher_id
                )
                avg = float(stats["avg"] or 0)
                count = int(stats["count"] or 0)
                return avg, count

    async def get_teacher_rating(self, full_name: str) -> Tuple[float, int]:
        async with self.pool.acquire() as conn:
            teacher = await conn.fetchrow("SELECT id FROM teachers WHERE full_name = $1", full_name)
            if not teacher:
                return 0.0, 0
            teacher_id = teacher["id"]
            stats = await conn.fetchrow(
                "SELECT AVG(grade) AS avg, COUNT(grade) AS count FROM grades WHERE teacher_id = $1",
                teacher_id
            )
            return float(stats["avg"] or 0), int(stats["count"] or 0)

    async def search_teachers(self, search: str) -> List[Dict]:
        pattern = f"{search.lower()}%"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT full_name, slug, hash FROM teachers WHERE LOWER(full_name) LIKE $1 LIMIT 50",
                pattern
            )
            return [dict(row) for row in rows]

    async def get_teacher_name_by_hash(self, hash_id: str) -> Optional[str]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT full_name FROM teachers WHERE hash = $1", hash_id)
            return row["full_name"] if row else None
        
    async def get_teacher_by_hash(self, hash_id: str) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, full_name, slug, hash FROM teachers WHERE hash = $1",
                hash_id
            )
            return dict(row) if row else None
        
    async def get_teacher_by_name(self, fullname: str) -> str | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT slug FROM teachers WHERE full_name = $1", fullname)
            return row["slug"] if row else None




# Экземпляр для использования
db = Database()
