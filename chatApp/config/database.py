import logging
from functools import lru_cache

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import CollectionInvalid

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MongoDB:
    def __init__(self) -> None:
        self.db_client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.users_collection: AsyncIOMotorCollection | None = None
        self.messages_collection: AsyncIOMotorCollection | None = None
        self.public_rooms_collection: AsyncIOMotorCollection | None = None
        self.private_rooms_collection: AsyncIOMotorCollection | None = None

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

            # Define collections and schema validations
            await self.create_collections()

            # Ping the server to validate the connection
            await self.db_client.admin.command("ismaster")
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    async def create_collections(self) -> None:
        # Define schema validation for each collection
        user_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["username", "email", "hashed_password"],
                "properties": {
                    "username": {"bsonType": "string"},
                    "email": {"bsonType": "string"},
                    "hashed_password": {"bsonType": "string"},
                    "is_active": {"bsonType": "bool"},
                    "is_admin": {"bsonType": "bool"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "last_login": {"bsonType": "date"},
                },
            }
        }

        message_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "room_id", "room_type"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "room_id": {"bsonType": "objectId"},
                    "room_type": {"bsonType": "string"},
                    "content": {"bsonType": "string"},
                    "media": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                },
            }
        }

        public_room_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["owner", "name"],
                "properties": {
                    "owner": {"bsonType": "objectId"},
                    "name": {"bsonType": "string"},
                    "description": {"bsonType": "string"},
                    "max_members": {"bsonType": "int"},
                    "welcome_message": {"bsonType": "string"},
                    "rules": {"bsonType": "string"},
                    "allow_file_sharing": {"bsonType": "bool"},
                    "members": {
                        "bsonType": "array",
                        "items": {"bsonType": "objectId"},
                    },
                    "ban_list": {
                        "bsonType": "array",
                        "items": {"bsonType": "objectId"},
                    },
                    "moderators": {
                        "bsonType": "array",
                        "items": {"bsonType": "objectId"},
                    },
                    "allow_users_access_message_history": {"bsonType": "bool"},
                    "max_latest_messages_access": {"bsonType": "int"},
                    "created_at": {"bsonType": "date"},
                },
            }
        }

        private_room_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["member1", "member2"],
                "properties": {
                    "member1": {"bsonType": "objectId"},
                    "member2": {"bsonType": "objectId"},
                    "created_at": {"bsonType": "date"},
                },
            }
        }

        if self.db is not None:
            await self.create_or_update_collection("users", user_schema)
            await self.create_or_update_collection("messages", message_schema)
            await self.create_or_update_collection(
                "public_rooms", public_room_schema
            )
            await self.create_or_update_collection(
                "private_rooms", private_room_schema
            )

            await self.create_indexes()

    async def create_or_update_collection(
        self, name: str, validator: dict
    ) -> None:
        if self.db is not None:
            try:
                await self.db.create_collection(name, validator=validator)
            except CollectionInvalid:
                logger.info(f"Collection '{name}' already exists.")
            except Exception as e:
                logger.error(f"Could not create collection '{name}': {e}")
                raise
        else:
            logger.error("MongoDB client is not initialized.")

    async def create_indexes(self) -> None:
        if self.db is not None:
            if self.users_collection is None:
                self.users_collection = self.db["users"]
            if self.messages_collection is None:
                self.messages_collection = self.db["messages"]
            if self.public_rooms_collection is None:
                self.public_rooms_collection = self.db["public_rooms"]
            if self.private_rooms_collection is None:
                self.private_rooms_collection = self.db["private_rooms"]

            await self.users_collection.create_indexes(
                [
                    IndexModel([("username", ASCENDING)], unique=True),
                    IndexModel([("email", ASCENDING)], unique=True),
                ]
            )

            await self.messages_collection.create_indexes(
                [
                    IndexModel(
                        [("room_id", ASCENDING), ("created_at", DESCENDING)]
                    ),
                    IndexModel(
                        [("room_type", ASCENDING), ("created_at", DESCENDING)]
                    ),
                ]
            )

            await self.public_rooms_collection.create_indexes(
                [IndexModel([("name", ASCENDING)], unique=True)]
            )

            await self.private_rooms_collection.create_indexes(
                [
                    IndexModel(
                        [("member1", ASCENDING), ("member2", ASCENDING)],
                        unique=True,
                    )
                ]
            )

    async def close_mongodb_connection(self) -> None:
        if self.db_client:
            self.db_client.close()
            logger.info("Closed MongoDB connection")


mongo_db = None


async def init_mongo_db():
    global mongo_db
    mongo_db = MongoDB()
    await mongo_db.connect_to_mongodb()
    return mongo_db


async def shutdown_mongo_db():
    """
    Close the MongoDB connection.
    """
    global mongo_db
    if mongo_db is not None:
        await mongo_db.close_mongodb_connection()


@lru_cache
def get_users_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the users collection from the MongoDB database.

    :return: The users collection instance.
    :raises RuntimeError: If the users collection is not initialized.
    """
    if mongo_db is None:
        raise RuntimeError("MongoDB instance is not initialized.")
    if mongo_db.users_collection is None:
        raise RuntimeError("Users collection is not initialized.")
    return mongo_db.users_collection


@lru_cache
def get_messages_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the messages collection from the MongoDB database.

    :return: The messages collection instance.
    :raises RuntimeError: If the messages collection is not initialized.
    """
    if mongo_db is None:
        raise RuntimeError("MongoDB instance is not initialized.")
    if mongo_db.messages_collection is None:
        raise RuntimeError("Messages collection is not initialized.")
    return mongo_db.messages_collection


@lru_cache
def get_public_rooms_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the public rooms collection from the MongoDB database.

    :return: The rooms collection instance.
    :raises RuntimeError: If the rooms collection is not initialized.
    """
    if mongo_db is None:
        raise RuntimeError("MongoDB instance is not initialized.")
    if mongo_db.public_rooms_collection is None:
        raise RuntimeError("Public rooms collection is not initialized.")
    return mongo_db.public_rooms_collection


@lru_cache
def get_private_rooms_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the private rooms collection from the MongoDB database.

    :return: The rooms collection instance.
    :raises RuntimeError: If the rooms collection is not initialized.
    """
    if mongo_db is None:
        raise RuntimeError("MongoDB instance is not initialized.")
    if mongo_db.private_rooms_collection is None:
        raise RuntimeError("Private rooms collection is not initialized.")
    return mongo_db.private_rooms_collection
