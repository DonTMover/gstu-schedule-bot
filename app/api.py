import aiohttp
import asyncio
from pprint import pprint
# from app.enum import groups

BASE_URL = "https://sc.gstu.by/api/schedules/group"

groups = {
    "АП-11": "ap-11",
    "АП-21": "ap-21",
    "АП-31": "ap-31",
    "АП-12": "ap-41",
    "АТ-11": "at-11",
    "АТ-21": "at-21",
    "АЭ-11": "ae-11",
    "АЭ-21": "ae-21",
    "АЭП-11": "aep-11",
}

async def fetch_schedule(group_name: str) -> dict:
    url = f"{BASE_URL}/{groups[group_name]}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()



# Example usage
async def main():
    data = await fetch_schedule("АП-11")
    pprint(data)

if __name__ == "__main__":
    asyncio.run(main())
