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

# функция для расчета среднего
def average(grades):
    return sum(grades) / len(grades) if grades else 0

# преобразуем словарь в новый формат
new_data = {}
for teacher, value in data.items():
    if isinstance(value, int) or isinstance(value, float):
        grades = [value] if value != 0 else []
    elif isinstance(value, list):
        grades = value
    else:
        grades = []
    new_data[teacher] = {
        "grades": grades,
        "average": average(grades)
    }

# сохраняем обратно
with open(teachers_file, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"Файл teachers.json успешно обновлён с {len(new_data)} преподавателями")
