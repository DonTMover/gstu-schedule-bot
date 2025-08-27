import json
from pathlib import Path
from typing import Optional, Dict, List

class Database:
    def __init__(self, filename: str = "db.json", teachers_file: str = "teachers.json"):
        self.path = Path(filename)
        self.teachers_file = Path(teachers_file)
        self._data: Dict[str, str] = {}
        self._load()
        self._load_teachers()

    # --- группы ---
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

    # --- teachers ---
    def _load_teachers(self) -> None:
        if self.teachers_file.exists():
            with open(self.teachers_file, "r", encoding="utf-8") as f:
                self.teachers: Dict[str, float] = json.load(f)
        else:
            self.teachers = {}

    def _save_teachers(self) -> None:
        with open(self.teachers_file, "w", encoding="utf-8") as f:
            json.dump(self.teachers, f, ensure_ascii=False, indent=2)

    def add_teacher_rating(self, name: str, value: int) -> int:
        value = max(0, min(5, value))
        self.teachers[name] = value
        self._save_teachers()  # сохраняем после изменения
        return self.teachers[name]

    def get_teacher_rating(self, name: str) -> int:
        return self.teachers.get(name, 0)


# Создаём один экземпляр
db = Database()
