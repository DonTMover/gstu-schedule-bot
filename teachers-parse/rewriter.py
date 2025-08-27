import json
from pathlib import Path

teachers_file = Path("teachers.json")

if not teachers_file.exists():
    print("Файл teachers.json не найден")
    exit(1)

# загружаем текущий файл
with open(teachers_file, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        print("Ошибка в формате JSON")
        exit(1)

# преобразуем: grades = [0], average = 0.0
new_data = {}
for teacher in data.keys():
    new_data[teacher] = {
        "grades": [0],
        "average": 0.0
    }

# сохраняем обратно
with open(teachers_file, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"Файл teachers.json успешно обновлён для {len(new_data)} преподавателей")
