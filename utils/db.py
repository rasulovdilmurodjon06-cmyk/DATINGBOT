from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import random

class Database:
    def __init__(self, uri):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client['dating_bot']
        self.users = self.db['users']

    async def add_user(self, user_id, username, lang):
        await self.users.update_one(
            {'user_id': user_id},
            {'$setOnInsert': {
                'user_id': user_id,
                'username': username,
                'lang': lang,
                'is_fake': 0,
                'created_at': datetime.now()
            }},
            upsert=True
        )

    async def update_user(self, user_id, **kwargs):
        await self.users.update_one({'user_id': user_id}, {'$set': kwargs})

    async def get_user(self, user_id):
        return await self.users.find_one({'user_id': user_id})

    async def get_random_users(self, gender, limit=10):
        cursor = self.users.find({'gender': gender})
        users = await cursor.to_list(length=100)
        return random.sample(users, min(len(users), limit))
                                         
