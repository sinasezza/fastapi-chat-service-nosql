from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter

from chatApp.models import user as user_model
from chatApp.schemas.user import UserListSchema

router = APIRouter()


@router.get("/", response_model=Mapping[str, Any])
async def get_all_users():
    users: list[Mapping[str, Any]] = await user_model.get_all_users()

    return {
        "users": [UserListSchema(**user) for user in users],
        "count": len(users),
    }
