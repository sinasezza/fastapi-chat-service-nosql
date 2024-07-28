from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorCursor

from chatApp.config.database import get_users_collection
from chatApp.models.user import User

router = APIRouter()


@router.get("/", response_model=list[User])
async def get_users() -> list[User]:
    users_collection = get_users_collection()

    # Perform the query to get an async cursor
    cursor: AsyncIOMotorCursor = users_collection.find()

    # Collect all users into a list of dictionaries
    users_dicts: list[Mapping[str, Any]] = await cursor.to_list(length=None)

    # Convert each dictionary to a User object
    users: list[User] = [User(**user_dict) for user_dict in users_dicts]

    return users
