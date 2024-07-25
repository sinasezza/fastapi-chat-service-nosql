import logging
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MongoDB:
    def __init__(self) -> None:
        self.db_client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.users_collection: Optional[AsyncIOMotorCollection] = None
        self.messages_collection: Optional[AsyncIOMotorCollection] = None
        self.rooms_collection: Optional[AsyncIOMotorCollection] = None

    async def connect_to_mongodb(self) -> None:
        try:
            self.db_client = AsyncIOMotorClient(
                settings.database_url,
                maxPoolSize=settings.max_pool_size,
                minPoolSize=settings.min_pool_size,
            )

            assert self.db_client is not None
            self.db = self.db_client[settings.database_name]
            assert self.db is not None

            # Initialize collections
            self.users_collection = self.db.get_collection("users")
            self.messages_collection = self.db.get_collection("messages")
            self.rooms_collection = self.db.get_collection("rooms")

            # Ping the server to validate the connection
            await self.db_client.admin.command("ismaster")
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    async def close_mongodb_connection(self) -> None:
        if self.db_client:
            self.db_client.close()
            logger.info("Closed MongoDB connection")


# Create a global instance of MongoDB
mongo_db = MongoDB()
