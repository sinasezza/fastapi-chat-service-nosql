import logging

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
        self.db_client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.users_collection: AsyncIOMotorCollection | None = None
        self.messages_collection: AsyncIOMotorCollection | None = None
        self.rooms_collection: AsyncIOMotorCollection | None = None

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
            self.public_rooms_collection = self.db.get_collection(
                "public_rooms"
            )
            self.private_rooms_collection = self.db.get_collection(
                "private_rooms"
            )

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


def get_users_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the users collection from the MongoDB database.

    :return: The users collection instance.
    :raises RuntimeError: If the users collection is not initialized.
    """
    users_collection = mongo_db.users_collection
    if users_collection is None:
        raise RuntimeError("Users collection is not initialized.")
    return users_collection


def get_messages_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the messages collection from the MongoDB database.

    :return: The messages collection instance.
    :raises RuntimeError: If the messages collection is not initialized.
    """
    messages_collection = mongo_db.messages_collection
    if messages_collection is None:
        raise RuntimeError("messages collection is not initialized.")
    return messages_collection


def get_public_rooms_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the public rooms collection from the MongoDB database.

    :return: The rooms collection instance.
    :raises RuntimeError: If the rooms collection is not initialized.
    """
    rooms_collection = mongo_db.public_rooms_collection
    if rooms_collection is None:
        raise RuntimeError("public rooms collection is not initialized.")
    return rooms_collection


def get_private_rooms_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the private rooms collection from the MongoDB database.

    :return: The rooms collection instance.
    :raises RuntimeError: If the rooms collection is not initialized.
    """
    rooms_collection = mongo_db.private_rooms_collection
    if rooms_collection is None:
        raise RuntimeError("private rooms collection is not initialized.")
    return rooms_collection
