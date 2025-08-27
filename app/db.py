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

    def delete_user(self, user_id: int) -> None:
        if str(user_id) in self._data:
            del self._data[str(user_id)]
            self._save()

    def all_users(self) -> Dict[str, str]:
        return dict(self._data)
    # --- end группы ---

    # --- teachers ---
    def _load_teachers(self) -> None:
        if self.teachers_file.exists():
            try:
                with open(self.teachers_file, "r", encoding="utf-8") as f:
                    self.teachers: Dict[str, Dict] = json.load(f)
            except json.JSONDecodeError:
                self.teachers = {}
        else:
            self.teachers = {}

        # на случай старого формата grades = [int]
        for k, v in list(self.teachers.items()):
            if isinstance(v, list):
                self.teachers[k] = {"grades": {}, "average": sum(v)/len(v) if v else 0.0}

    def _save_teachers(self) -> None:
        with open(self.teachers_file, "w", encoding="utf-8") as f:
            json.dump(self.teachers, f, ensure_ascii=False, indent=2)

    def add_teacher_rating(self, name: str, value: int, user_id: int):
        if name not in self.teachers:
            self.teachers[name] = {"grades": {}, "average": 0.0}

        # ставим или заменяем оценку пользователя
        self.teachers[name]["grades"][str(user_id)] = value

        # пересчёт среднего
        grades = list(self.teachers[name]["grades"].values())
        avg = sum(grades) / len(grades)
        self.teachers[name]["average"] = avg

        self._save_teachers()
        return avg, len(grades)

    def get_teacher_rating(self, name):
        teacher = self.teachers.get(name)
        if not teacher:
            return 0.0, 0
        grades = list(teacher.get("grades", {}).values())
        if not grades:
            return 0.0, 0
        avg = sum(grades) / len(grades)
        count = len(grades)
        return avg, count

# Создаём один экземпляр
db = Database()
