from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    def __init__(self, uri: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client["datingbot"]
        self.users = self.db["users"]

    async def get_user(self, user_id: int):
        return await self.users.find_one({"user_id": user_id})

    async def add_user(self, user_id: int, username: str, lang: str):
        await self.users.insert_one({
            "user_id": user_id,
            "username": username,
            "lang": lang
        })

    async def update_user(self, user_id: int, **kwargs):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": kwargs}
        )

    async def get_random_users(self, gender: str, exclude_id: int):
        users = await self.users.find(
            {"gender": gender, "user_id": {"$ne": exclude_id}, "is_banned": {"$ne": True}}
        ).to_list(length=100)
        return users

    async def get_users_count(self):
        return await self.users.count_documents({})

    async def get_active_users_count(self):
        return await self.users.count_documents({"is_banned": {"$ne": True}})

    async def get_banned_users_count(self):
        return await self.users.count_documents({"is_banned": True})

    async def get_all_users(self, limit=None):
        cursor = self.users.find({})
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit or 10000)

    async def ban_user(self, user_id: int):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": True}}
        )

    async def unban_user(self, user_id: int):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": False}}
    )
        
