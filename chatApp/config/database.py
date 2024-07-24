from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection

from .config import get_settings

settings = get_settings()


# Singleton Pattern for connecting to the database
class MongoDB:
    def __init__(self):
        self.db_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.users_collection: Optional[Collection] = None
        self.messages_collection: Optional[Collection] = None
        self.rooms_collection: Optional[Collection] = None

    async def connect_to_mongodb(self):
        self.db_client = AsyncIOMotorClient(
            settings.database_url, maxPoolSize=10, minPoolSize=1
        )
        self.db = self.db_client[settings.database_name]
        print("Connected to MongoDB")

        # Initialize collections and create indexes
        self.users_collection = self.db.get_collection("users")
        self.messages_collection = self.db.get_collection("messages")
        self.rooms_collection = self.db.get_collection("rooms")

        # # Create indexes
        # self.users_collection.create_index([("_id", 1)], unique=True)
        # self.messages_collection.create_index([("_id", 1)], unique=True)
        # self.rooms_collection.create_index([("_id", 1)], unique=True)

    async def close_mongodb_connection(self):
        if self.db_client:
            self.db_client.close()
            print("Closed MongoDB connection")


# Create a global instance of MongoDB
mongo_db = MongoDB()
