from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.config.database import (
    get_messages_collection,
    get_private_rooms_collection,
)
from chatApp.utils.object_id import PydanticObjectId

from .public_room import fetch_public_room_by_id


class Message(BaseModel):
    user_id: PydanticObjectId
    room_id: PydanticObjectId
    room_type: str
    content: str | None = Field(default=None)
    media: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class MessageInDB(Message):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")


# async def insert_message(message: str):
#     message_collection = get_messages_collection()
#     result = await message_collection.insert_one(message.dict())
#     return result.inserted_id


async def get_public_messages(room_id: str) -> list[MessageInDB]:
    """
    Fetch public messages from a specific room.
    """
    messages_collection = get_messages_collection()

    # Fetch the public room by ID
    room = await fetch_public_room_by_id(room_id)
    if room is None:
        return []

    room_id_obj = PydanticObjectId(room_id)
    query = {"room_id": room_id_obj, "room_type": "public"}

    # Fetch the documents using the query
    cursor = messages_collection.find(query)

    # Convert the cursor to a list and await the result
    messages = await cursor.to_list(length=None)

    # Convert each document to MessageInDB
    return [MessageInDB(**message) for message in messages]


async def get_private_messages(
    room_id: str,
) -> list[MessageInDB]:
    """
    Fetch private messages from a specific room between two users.
    """
    # Fetch the private room by ID
    room_collection = get_private_rooms_collection()
    room_id_obj = PydanticObjectId(room_id)
    room = await room_collection.find_one({"_id": room_id_obj})
    if room is None:
        return []

    messages_collection = get_messages_collection()
    query = {"room_id": room_id_obj, "room_type": "private"}

    # Fetch the documents using the query
    cursor = messages_collection.find(query)

    # Convert the cursor to a list and await the result
    messages = await cursor.to_list(length=None)

    # Convert each document to MessageInDB
    return [MessageInDB(**message) for message in messages]
