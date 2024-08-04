from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.config.database import get_messages_collection
from chatApp.utils.object_id import PydanticObjectId

from . import private_room, public_room


class Message(BaseModel):
    user_id: PydanticObjectId
    room_id: PydanticObjectId
    room_type: str
    content: str | None = Field(default=None)
    media: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class MessageInDB(Message):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")


async def get_public_messages(room_id: str) -> list[MessageInDB]:
    """
    Fetch public messages from a specific room.
    """
    messages_collection = get_messages_collection()

    # Fetch the public room by ID
    room = await public_room.fetch_public_room_by_id(room_id)
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
    room_id_obj = PydanticObjectId(room_id)
    room = await private_room.fetch_private_room_by_id(room_id)
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


async def create_message(
    room_id: str, user_id: str, room_type: str, content: str
):
    """
    Create a new message in the specified room.
    """
    room: private_room.PrivateRoomInDB | public_room.PublicRoomInDB | None = (
        None
    )
    if room_type == "private":
        room = await private_room.fetch_private_room_by_id(room_id)
    else:
        room = await public_room.fetch_public_room_by_id(room_id)

    if room is None:
        raise ValueError("Room not found")

    messages_collection = get_messages_collection()
    room_id_obj = PydanticObjectId(room_id)
    user_id_obj = PydanticObjectId(user_id)

    message = Message(
        user_id=user_id_obj,
        room_id=room_id_obj,
        room_type=room_type,
        content=content,
        created_at=datetime.now(),
    )

    message_dict = message.model_dump(by_alias=True)

    # Add the `_id` to the dictionary
    result = await messages_collection.insert_one(message_dict)
    message_dict["_id"] = (
        result.inserted_id
    )  # Add the _id field to the dictionary

    # Return MessageInDB with _id included in the dictionary
    return MessageInDB(**message_dict)
