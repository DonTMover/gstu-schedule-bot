import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from typing import Optional, Tuple, List, Dict

load_dotenv("app/.env")
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL не найден в .env")
        self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)

    # --- users ---
    def set_group(self, user_id: int, group: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, group_name)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE 
                    SET group_name = EXCLUDED.group_name
                """,
                (user_id, group)
            )
        self.conn.commit()


    def get_group(self, user_id: int) -> Optional[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT group_name FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return row["group_name"] if row else None

    def delete_user(self, user_id: int) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        self.conn.commit()

    def all_users(self) -> Dict[str, str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, group_name FROM users")
            return {str(row["id"]): row["group_name"] for row in cur.fetchall()}
        
    def ensure_user(self, user_id: int, group: str = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, group_name)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (user_id, group)
            )
        self.conn.commit()

    def user_exists(self, user_id: int) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
            return cur.fetchone() is not None



    # --- teachers ---
    def add_teacher_rating(self, full_name: str, grade: int, user_id: int) -> Tuple[float, int]:
        with self.conn.cursor() as cur:
            # ищем teacher_id или создаём преподавателя с пустым slug/hash
            cur.execute("SELECT id FROM teachers WHERE full_name = %s", (full_name,))
            teacher = cur.fetchone()
            if not teacher:
                cur.execute(
                    "INSERT INTO teachers (full_name, slug, hash) VALUES (%s, '', '') RETURNING id",
                    (full_name,)
                )
                teacher_id = cur.fetchone()["id"]
            else:
                teacher_id = teacher["id"]

            # вставляем или обновляем оценку
            cur.execute(
                """
                INSERT INTO grades (teacher_id, user_id, grade)
                VALUES (%s, %s, %s)
                ON CONFLICT (teacher_id, user_id) DO UPDATE SET grade = EXCLUDED.grade
                """,
                (teacher_id, user_id, grade)
            )

            # пересчёт среднего
            cur.execute(
                "SELECT AVG(grade) AS avg, COUNT(grade) AS count FROM grades WHERE teacher_id = %s",
                (teacher_id,)
            )
            stats = cur.fetchone()
            avg = float(stats["avg"] or 0)
            count = int(stats["count"] or 0)

        self.conn.commit()
        return avg, count

    def get_teacher_rating(self, full_name: str) -> Tuple[float, int]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM teachers WHERE full_name = %s", (full_name,))
            teacher = cur.fetchone()
            if not teacher:
                return 0.0, 0
            teacher_id = teacher["id"]
            cur.execute(
                "SELECT AVG(grade) AS avg, COUNT(grade) AS count FROM grades WHERE teacher_id = %s",
                (teacher_id,)
            )
            stats = cur.fetchone()
            return float(stats["avg"] or 0), int(stats["count"] or 0)

    def search_teachers(self, search: str) -> List[Dict]:
        """Ищет преподавателей по началу ФИО (LIKE 'search%')"""
        pattern = f"{search.lower()}%"
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT full_name, slug, hash FROM teachers WHERE LOWER(full_name) LIKE %s LIMIT 50",
                (pattern,)
            )
            return [dict(row) for row in cur.fetchall()]
        
    def get_teacher_name_by_hash(self, hash_id: str) -> Optional[str]:
        """
        Возвращает имя преподавателя по hash.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT full_name FROM teachers WHERE hash = %s",
                (hash_id,)
            )
            row = cur.fetchone()
            return row["full_name"] if row else None

# Экземпляр для использования
db = Database()
