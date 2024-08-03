from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from chatApp.config.database import get_messages_collection
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


async def get_public_messages(
    room_id: str,
) -> tuple[bool, list[Mapping[str, Any]]]:
    """
    Fetch public messages from a specific room.

    :param room_id: The ID of the public room to fetch messages from.
    :return: A tuple where the first element is a boolean indicating success,
             and the second element is a list of messages (each message represented as a dictionary).
    """
    messages_collection = get_messages_collection()

    # Fetch the public room by ID
    room = await fetch_public_room_by_id(room_id)
    if room is None:
        return False, []

    # Fetch messages from the messages collection
    cursor = messages_collection.find({"room_id": room_id})
    messages = await cursor.to_list(
        length=None
    )  # Await the cursor to list conversion

    return True, messages
