from motor.motor_asyncio import AsyncIOMotorClient

from .config import get_settings

settings = get_settings()

# Global variable to hold the database client
db_client = None
db = None


async def connect_to_mongodb():
    global db_client, db
    db_client = AsyncIOMotorClient(settings.database_url, maxPoolSize=10, minPoolSize=1)
    db = db_client[settings.database_name]
    print("Connected to MongoDB")


async def close_mongodb_connection():
    global db_client
    if db_client:
        db_client.close()
        print("Closed MongoDB connection")
