import aiohttp
import asyncio
from collections import defaultdict
from groupes import groups
import uuid
from cache import cache
import random
from os import getenv
from dotenv import load_dotenv
from datetime import datetime, date, timedelta

BASE_URL = "https://sc.gstu.by/api/schedules/group"

#OLD HEADERS - remove later
# COMMON_HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
#     "Accept": "application/json, text/plain, */*",
#     "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
#     "Accept-Encoding": "gzip, deflate",
#     "DNT": "1",
#     "Connection": "keep-alive",
#     "Sec-Fetch-Dest": "empty",
#     "Sec-Fetch-Mode": "cors",
#     "Sec-Fetch-Site": "same-origin",
#     "Sec-GPC": "1",
# }


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
]


async def fetch_schedule(group_name: str) -> dict: # тут запрашиваем
    # генерируем новый tid для каждого запроса
    tid = uuid.uuid4().hex
    headers = get_headers()
    headers["X-Id"] = tid
    headers["Cookie"] = f"_tid={tid}"
    headers["Referer"] = f"https://sc.gstu.by/group/{groups[group_name]}"

    load_dotenv()
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{BASE_URL}/{groups[group_name]}", 
                               timeout=15,
                                proxy=getenv('PROXY') # get proxy from env
                               ) as resp:
            resp.raise_for_status()
            return await resp.json()
        
async def fetch_schedule_cached(group_name: str) -> dict: # Снаачало проверяем есть ли в кеше, потом уже запрашиваем
    key = f"schedule:{group_name}"
    data = await cache.get_json(key)
    
    if data:
        return data
    
    try:
        fresh = await fetch_schedule(group_name)
        await cache.set_json(key, fresh, expire=60 * 60 * 24 * 2) 
        return fresh
    except HTTPStatusError as e:
        if data and e.responce.status_code == 403:
            return data
        raise 


def get_headers(): # Рандомизируем хедерсы
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": random.choice(["ru-RU,ru;q=0.9", "ru,en;q=0.8", "en-US,en;q=0.7"]),
        "Connection": "keep-alive",
    }

def get_human_readable_schedule(data):
    days_map = {
        "MONDAY": "Понедельник",
        "TUESDAY": "Вторник",
        "WEDNESDAY": "Среда",
        "THURSDAY": "Четверг",
        "FRIDAY": "Пятница",
        "SATURDAY": "Суббота"
    }

    today = date.today()

    # Границы текущей недели
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Даты этой недели по ключу dayOfWeek
    week_day_dates = {
        "MONDAY": monday,
        "TUESDAY": monday + timedelta(days=1),
        "WEDNESDAY": monday + timedelta(days=2),
        "THURSDAY": monday + timedelta(days=3),
        "FRIDAY": monday + timedelta(days=4),
        "SATURDAY": monday + timedelta(days=5),
        "SUNDAY": monday + timedelta(days=6),
    }

    # Чётность недели
    week_type = "EVEN" if today.isocalendar().week % 2 == 0 else "ODD"

    schedule_by_day = {name: [] for name in days_map.values()}

    for item in data.get('data', {}).get('scheduleItems', []):
        day_key = item.get('dayOfWeek')
        day_ru = days_map.get(day_key)
        if not day_ru:
            continue

        # проверяем, что startDate в пределах текущей недели
        start_date_str = item.get('startDate')
        if not start_date_str:
            continue
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if not (monday <= start_date <= sunday):
            continue

        lesson_date = week_day_dates.get(day_key)
        if not lesson_date:
            continue

        subject = item.get('subject', {})
        lesson = {
            "lessonNumber": item.get('lessonNumber'),
            "startTime": item.get('startTime'),
            "endTime": item.get('endTime'),
            "startDate": start_date_str,
            "date": lesson_date.isoformat(),
            "weekType": week_type,
            "subject": subject.get('name'),
            "subjectShort": subject.get('shortName'),
            "teachers": ", ".join(t.get('fullName') for t in item.get('teachers', []) if t.get('fullName')) or None,
            "classrooms": ", ".join(c.get('roomNumber') for c in item.get('classrooms', []) if c.get('roomNumber')) or None,
            "groups": ", ".join(g.get('name') for g in item.get('groups', []) if g.get('name')) or None
        }
        schedule_by_day[day_ru].append(lesson)

    # сортировка по времени
    for lessons in schedule_by_day.values():
        lessons.sort(key=lambda x: x['startTime'] or "")

    return schedule_by_day

# def get_human_readable_schedule(data): #Форматирование расписания под более читаемый вариант
#     days_map = {
#         "MONDAY": "Понедельник",
#         "TUESDAY": "Вторник",
#         "WEDNESDAY": "Среда",
#         "THURSDAY": "Четверг",
#         "FRIDAY": "Пятница",
#         "SATURDAY": "Суббота"
#     }
    
#     schedule_by_day = {name: [] for name in days_map.values()}
    
#     for item in data['data']['scheduleItems']:
#         day = days_map.get(item['dayOfWeek'])
#         if day:
#             lesson = {
#                 "lessonNumber": item['lessonNumber'],
#                 "startTime": item['startTime'],
#                 "endTime": item['endTime'],
#                 "startDate": item['startDate'],
#                 "subject": item['subject']['name'],
#                 "subjectShort": item['subject'].get('shortName'),
#                 "teachers": ", ".join(t['fullName'] for t in item.get('teachers', [])) or None,
#                 "classrooms": ", ".join(c['roomNumber'] for c in item.get('classrooms', [])) or None,
#                 "groups": ", ".join(g['name'] for g in item.get('groups', [])) or None
#             }
#             schedule_by_day[day].append(lesson)
    
#     # сортировка по времени
#     for lessons in schedule_by_day.values():
#         lessons.sort(key=lambda x: x['startTime'])
    
#     return schedule_by_day

def pretty_schedule_str(data: dict) -> str: # Тестовое форматирования для cli режима
    entity = data.get("data", {}).get("entity", {}) if isinstance(data, dict) else {}
    items = data.get("data", {}).get("scheduleItems", []) if isinstance(data, dict) else []
    order = {"MONDAY":0,"TUESDAY":1,"WEDNESDAY":2,"THURSDAY":3,"FRIDAY":4,"SATURDAY":5,"SUNDAY":6}
    ru = {"MONDAY":"Понедельник","TUESDAY":"Вторник","WEDNESDAY":"Среда",
          "THURSDAY":"Четверг","FRIDAY":"Пятница","SATURDAY":"Суббота","SUNDAY":"Воскресенье"}

    lines = []
    lines.append(f"{entity.get('facultyShort','')} — {entity.get('faculty','')}")
    lines.append(f"Группа: {entity.get('name','—')} | Курс: {entity.get('course','—')}")
    spec = entity.get('specialty') or {}
    lines.append(f"Специальность: {spec.get('code','—')} {spec.get('name','—')}")
    lines.append("="*80)

    by_day = defaultdict(list)
    for it in items:
        by_day[it.get("dayOfWeek","UNKNOWN")].append(it)

    for day in sorted(by_day.keys(), key=lambda k: order.get(k, 99)):
        lines.append(f"\n--- {ru.get(day, day)} ---")
        for it in sorted(by_day[day], key=lambda x: x.get("startTime","")):
            st = (it.get("startTime","")[:5] or "??:??")
            en = (it.get("endTime","")[:5] or "??:??")
            num = it.get("lessonNumber","-")
            subj = (it.get("subject") or {}).get("name","—")
            rooms = ", ".join(c.get("roomNumber","") for c in it.get("classrooms",[])) or "—"
            teachers = ", ".join(t.get("shortName","") for t in it.get("teachers",[])) or "—"
            groups = ", ".join(g.get("name","") for g in it.get("groups",[])) or "—"
            lines.append(f"{st}-{en} | №{num} | {subj} | Группы: {groups} | Каб.: {rooms} | Преп.: {teachers}")

    return "\n".join(lines)

async def get_schedule(group_name: str) -> str: # Удобная абстракция для получения расписания
    print(f"Fetching schedule for group: {group_name}")
    data = await fetch_schedule_cached(group_name)
    lines = pretty_schedule_str(data)
    return lines



# Пример использования
async def main():
    
    data = await fetch_schedule_cached("АП-11")
    #pprint(data)
    print(pretty_schedule_str(data))


if __name__ == "__main__":
    asyncio.run(main())