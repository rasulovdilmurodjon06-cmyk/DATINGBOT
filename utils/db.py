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
    
