from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

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
    last_login: datetime | None = None


class UserInDB(User):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")


async def fetch_user_by_username(username: str) -> Mapping[str, Any] | None:
    """Fetch a user from the database by username."""
    users_collection = get_users_collection()
    return await users_collection.find_one({"username": username})


async def fetch_user_by_id(user_id: str) -> Mapping[str, Any] | None:
    """Fetch a user from the database by user ID."""
    users_collection = get_users_collection()
    return await users_collection.find_one({"_id": PydanticObjectId(user_id)})


async def fetch_user_by_email(email: str) -> Mapping[str, Any] | None:
    """Fetch a user from the database by email."""
    users_collection = get_users_collection()
    return await users_collection.find_one({"email": email})
