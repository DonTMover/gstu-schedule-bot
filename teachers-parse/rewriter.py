import json
from pathlib import Path

# путь к вашему teachers.json
teachers_file = Path("teachers.json")

if not teachers_file.exists():
    print("Файл teachers.json не найден")
    exit(1)

# загружаем текущий файл
with open(teachers_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# если это список, преобразуем в словарь с рейтингом 0
if isinstance(data, list):
    teachers_dict = {name: 0 for name in data}
    with open(teachers_file, "w", encoding="utf-8") as f:
        json.dump(teachers_dict, f, ensure_ascii=False, indent=2)
    print(f"Файл teachers.json успешно преобразован в словарь с рейтингами {len(teachers_dict)} преподавателей")
else:
    print("Файл уже в формате словаря, преобразование не требуется")
