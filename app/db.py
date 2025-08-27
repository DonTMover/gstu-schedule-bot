import json
from pathlib import Path
from typing import Optional, Dict, List

class Database:
    def __init__(self, filename: str = "db.json", teachers_file: str = "teachers.json"):
        self.path = Path(filename)
        self._data: Dict[str, str] = {}
        self._load()
        self.teachers_file = Path(teachers_file)
        self._load_teachers()

    def _load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except json.JSONDecodeError:
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def set_group(self, user_id: int, group: str) -> None:
        self._data[str(user_id)] = group
        self._save()

    def get_group(self, user_id: int) -> Optional[str]:
        return self._data.get(str(user_id))

    def delete_user(self, user_id: int) -> None:
        if str(user_id) in self._data:
            del self._data[str(user_id)]
            self._save()

    def all_users(self) -> Dict[str, str]:
        return dict(self._data)

    # --- Teachers ---
    def _load_teachers(self) -> None:
        if self.teachers_file.exists():
            with open(self.teachers_file, "r", encoding="utf-8") as f:
                # Изначально рейтинг 0 для всех
                self.teachers: Dict[str, float] = {t: 0.0 for t in json.load(f)}
        else:
            self.teachers = {}

    def get_teacher_rating(self, name: str) -> float:
        return self.teachers.get(name, 0.0)

    def add_teacher_rating(self, name: str, value: float) -> float:
        """Добавить рейтинг и вернуть новый средний"""
        if name not in self.teachers:
            self.teachers[name] = 0.0
        self.teachers[name] += value
        # Можно делить на количество оценок для среднего, если нужно
        return self.teachers[name]

# Создаём один экземпляр
db = Database()
