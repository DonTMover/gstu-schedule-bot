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

    # --- teachers ---
    def _load_teachers(self) -> None:
        if self.teachers_file.exists():
            try:
                with open(self.teachers_file, "r", encoding="utf-8") as f:
                    self.teachers: Dict[str, List[int]] = json.load(f)
            except json.JSONDecodeError:
                self.teachers = {}
        else:
            self.teachers = {}

        # на случай старого формата с числами
        for k, v in list(self.teachers.items()):
            if isinstance(v, int):
                self.teachers[k] = [v]


    def _save_teachers(self) -> None:
        with open(self.teachers_file, "w", encoding="utf-8") as f:
            json.dump(self.teachers, f, ensure_ascii=False, indent=2)

    def add_teacher_rating(self, name: str, value: int):
        """Добавляет оценку преподавателю и возвращает средний рейтинг + количество оценок"""
        value = max(0, min(5, value))
        if name not in self.teachers:
            self.teachers[name] = []
        self.teachers[name].append(value)
        self._save_teachers()
        avg = sum(self.teachers[name]) / len(self.teachers[name])
        return avg, len(self.teachers[name])


    def get_teacher_rating(self, name: str):
        """Возвращает средний рейтинг и количество оценок"""
        grades = self.teachers.get(name, [])
        if not grades:
            return 0.0, 0
        avg = sum(grades) / len(grades)
        return avg, len(grades)



# Создаём один экземпляр
db = Database()
