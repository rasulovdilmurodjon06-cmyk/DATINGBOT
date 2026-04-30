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

    async def get_random_users(self, gender, limit=20):
        cursor = self.users.aggregate([
            {'$match': {'gender': gender}},
            {'$sample': {'size': limit}}
        ])
        return await cursor.to_list(length=limit)

    async def add_fake_user(self, full_name, age, gender, region, city, photo):
        await self.users.insert_one({
            'user_id': random.randint(1000, 9999),
            'full_name': full_name,
            'age': age,
            'gender': gender,
            'region': region,
            'city': city,
            'photo': photo,
            'is_fake': 1,
            'created_at': datetime.now()
        })
        
