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

# преобразуем: grades = {}, average = 0.0
new_data = {}
for teacher in data.keys():
    value = data[teacher]
    if isinstance(value, list):
        grades_dict = {str(i): v for i, v in enumerate(value)}  # временные ключи для старых оценок
    else:
        grades_dict = {}
    new_data[teacher] = {
        "grades": grades_dict,
        "average": sum(grades_dict.values())/len(grades_dict) if grades_dict else 0.0
    }

# сохраняем обратно
with open(teachers_file, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"Файл teachers.json успешно обновлён для {len(new_data)} преподавателей")
