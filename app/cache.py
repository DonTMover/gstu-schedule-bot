import os
import asyncio
import json
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv("app/.env")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class Cache: 
    def __init__(self):
        self.client: redis.Redis | None = None

    async def init(self):
        self.client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    async def get_json(self, key: str): # Получаем кеш из редиски для минимизации запросов к апи
        if not self.client:
            raise RuntimeError("Redis не инициализирован")
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def set_json(self, key: str, value, expire: int = 604800): # Записываем в кеш
        if not self.client:
            raise RuntimeError("Redis не инициализирован")
        await self.client.set(key, json.dumps(value), ex=expire)


cache = Cache()
