import json
from pathlib import Path
from typing import Optional, Dict

class Database:
    def __init__(self, filename: str = "db.json"):
        self.path = Path(filename)
        self._data: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Загрузка базы из файла"""
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except json.JSONDecodeError:
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Сохранение базы в файл"""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def set_group(self, user_id: int, group: str) -> None:
        """Привязать группу к пользователю"""
        self._data[str(user_id)] = group
        self._save()

    def get_group(self, user_id: int) -> Optional[str]:
        """Получить группу по user_id"""
        return self._data.get(str(user_id))

    def delete_user(self, user_id: int) -> None:
        """Удалить пользователя"""
        if str(user_id) in self._data:
            del self._data[str(user_id)]
            self._save()

    def all_users(self) -> Dict[str, str]:
        """Получить весь словарь user_id -> group"""
        return dict(self._data)


# Создаём один экземпляр, чтобы импортировать его в других файлах
db = Database()
