import aiohttp
import asyncio
from collections import defaultdict
from groupes import groups

#utils
import json
import os

BASE_URL = "https://sc.gstu.by/api/schedules/group"


async def fetch_schedule(group_name: str) -> dict:
    url = f"{BASE_URL}/{groups[group_name]}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

async def main():
    group = "АП-11"
    data = await fetch_schedule(group)
    filename = f"{group}.json"   # например, "АП-11.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Данные сохранены в {filename}")


if __name__ == "__main__":
    main()