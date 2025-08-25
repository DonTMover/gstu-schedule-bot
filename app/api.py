import aiohttp
import asyncio
from pprint import pprint
from app.enum import groups

BASE_URL = "https://sc.gstu.by/api/schedules/group"

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
