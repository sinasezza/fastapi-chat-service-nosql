from collections.abc import Mapping
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCursor
from pydantic import BaseModel, Field

from chatApp.config import auth
from chatApp.config.database import get_users_collection
from chatApp.utils.object_id import PydanticObjectId


class User(BaseModel):
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    last_login: datetime = Field(default_factory=lambda: datetime.now())


class UserInDB(User):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")


async def get_all_users() -> list[Mapping[str, Any]]:
    users_collection = get_users_collection()

    # Query to get users with necessary fields projected
    cursor: AsyncIOMotorCursor = users_collection.find(
        {}, {"_id": 1, "username": 1, "created_at": 1}
    )

    # Collect all users into a list of UserInDB objects
    return await cursor.to_list(length=None)


async def fetch_user_by_username(username: str) -> UserInDB | None:
    """Fetch a user from the database by username."""
    users_collection = get_users_collection()
    user = await users_collection.find_one({"username": username})
    return UserInDB(**user) if user else None


async def fetch_user_by_id(user_id: str) -> UserInDB | None:
    """Fetch a user from the database by user ID."""
    users_collection = get_users_collection()
    user = await users_collection.find_one({"_id": PydanticObjectId(user_id)})
    return UserInDB(**user) if user else None


async def fetch_user_by_email(email: str) -> UserInDB | None:
    """Fetch a user from the database by email."""
    users_collection = get_users_collection()
    user = await users_collection.find_one({"email": email})
    return UserInDB(**user) if user else None


async def create_user(user_dict: dict[str, Any]) -> UserInDB:
    """Create a new user in the database."""
    users_collection = get_users_collection()

    user_dict["created_at"] = datetime.now()
    user_dict["updated_at"] = datetime.now()
    user_dict["last_login"] = datetime.now()
    user_dict["hashed_password"] = auth.get_password_hash(
        user_dict["password"]
    )

    result = await users_collection.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)

    return UserInDB(**user_dict)
