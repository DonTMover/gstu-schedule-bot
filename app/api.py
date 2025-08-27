import aiohttp
import asyncio
from collections import defaultdict
from groupes import groups
import uuid

BASE_URL = "https://sc.gstu.by/api/schedules/group"

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
}


async def fetch_schedule(group_name: str) -> dict:
    # генерируем новый tid для каждого запроса
    tid = uuid.uuid4().hex
    headers = COMMON_HEADERS.copy()
    headers["X-Id"] = tid
    headers["Cookie"] = f"_tid={tid}"
    headers["Referer"] = f"https://sc.gstu.by/group/{groups[group_name]}"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{BASE_URL}/{groups[group_name]}", timeout=15) as resp:
            resp.raise_for_status()
            return await resp.json()

def get_human_readable_schedule(data):
    days_map = {
        "MONDAY": "Понедельник",
        "TUESDAY": "Вторник",
        "WEDNESDAY": "Среда",
        "THURSDAY": "Четверг",
        "FRIDAY": "Пятница",
        "SATURDAY": "Суббота"
    }
    
    schedule_by_day = {name: [] for name in days_map.values()}
    
    for item in data['data']['scheduleItems']:
        day = days_map.get(item['dayOfWeek'])
        if day:
            lesson = {
                "startTime": item['startTime'],
                "endTime": item['endTime'],
                "subject": item['subject']['name'],
                "subjectShort": item['subject'].get('shortName'),
                "teachers": ", ".join(t['fullName'] for t in item.get('teachers', [])) or None,
                "classrooms": ", ".join(c['roomNumber'] for c in item.get('classrooms', [])) or None,
                "groups": ", ".join(g['name'] for g in item.get('groups', [])) or None
            }
            schedule_by_day[day].append(lesson)
    
    # сортировка по времени
    for lessons in schedule_by_day.values():
        lessons.sort(key=lambda x: x['startTime'])
    
    return schedule_by_day

def pretty_schedule_str(data: dict) -> str:
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

async def get_schedule(group_name: str) -> str:
    print(f"Fetching schedule for group: {group_name}")
    data = await fetch_schedule(group_name)
    lines = pretty_schedule_str(data)
    return lines



# Example usage
async def main():
    
    data = await fetch_schedule("АП-11")
    #pprint(data)
    print(pretty_schedule_str(data))


if __name__ == "__main__":
    asyncio.run(main())