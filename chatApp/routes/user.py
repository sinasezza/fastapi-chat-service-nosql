from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorCursor

from chatApp.config.auth import get_users_collection
from chatApp.schemas.user import users_serializer

router = APIRouter()


@router.get("/")
async def get_users() -> list[Mapping[str, Any]]:
    users_collection = get_users_collection()
    # Perform the query to get an async cursor
    cursor: AsyncIOMotorCursor = users_collection.find()
    # Collect all users into a list
    users: list[Mapping[str, Any]] = await cursor.to_list(
        length=None
    )  # length=None will retrieve all documents
    # Serialize the list of users
    return users_serializer(users)
