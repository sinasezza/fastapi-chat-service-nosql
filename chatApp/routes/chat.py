from collections.abc import Mapping
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from chatApp.config import auth
from chatApp.config.database import get_messages_collection
from chatApp.models.message import MessageInDB
from chatApp.models.user import UserInDB
from chatApp.schemas.message import MessageCreateSchema

router = APIRouter()


@router.get("/all-messages", response_model=list[MessageInDB])
async def get_all_messages():
    messages_collection: AsyncIOMotorCollection = get_messages_collection()

    cursor: AsyncIOMotorCursor = messages_collection.find()
    messages_dicts: list[Mapping[str, Any]] = await cursor.to_list(length=None)
    messages: list[MessageInDB] = [
        MessageInDB(**message_dict) for message_dict in messages_dicts
    ]

    return messages


@router.get("/messages", response_model=list[MessageInDB])
async def get_messages(user: UserInDB = Depends(auth.get_current_user)):
    messages_collection: AsyncIOMotorCollection = get_messages_collection()

    cursor: AsyncIOMotorCursor = messages_collection.find(
        {"user_id": ObjectId(user.id)}
    )
    messages_dicts: list[Mapping[str, Any]] = await cursor.to_list(length=None)
    messages: list[MessageInDB] = [
        MessageInDB(**message_dict) for message_dict in messages_dicts
    ]

    return messages


@router.get("/message/{message_id}", response_model=MessageInDB)
async def get_message(message_id: str, user: UserInDB = Depends(auth.get_current_user)):
    messages_collection: AsyncIOMotorCollection = get_messages_collection()

    message = await messages_collection.find_one(
        {"_id": ObjectId(message_id), "user_id": ObjectId(user.id)}
    )

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    return MessageInDB(**message)


@router.post("/message", response_model=MessageInDB)
async def create_message(
    message: MessageCreateSchema, user: UserInDB = Depends(auth.get_current_user)
):
    messages_collection = get_messages_collection()

    message_dict = message.model_dump()
    message_dict["user_id"] = user.id

    result = await messages_collection.insert_one(message_dict)

    return MessageInDB(**message_dict, _id=result.inserted_id)
