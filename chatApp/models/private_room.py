from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from chatApp.config.database import get_private_rooms_collection
from chatApp.utils.object_id import PydanticObjectId


class PrivateRoom(BaseModel):
    member1: PydanticObjectId
    member2: PydanticObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class PrivateRoomInDB(PrivateRoom):
    id: PydanticObjectId = Field(alias="_id")


async def fetch_private_room_by_id(id: str) -> PrivateRoomInDB | None:
    room_collection = get_private_rooms_collection()
    room = await room_collection.find_one({"_id": PydanticObjectId(id)})
    return PrivateRoomInDB(**room) if room else None


async def fetch_private_room_by_members(
    user1_id: str, user2_id: str
) -> PrivateRoomInDB | None:
    rooms_collection = get_private_rooms_collection()
    room: Mapping[str, Any] | None = await rooms_collection.find_one(
        {
            "$or": [
                {
                    "member1": PydanticObjectId(user1_id),
                    "member2": PydanticObjectId(user2_id),
                },
                {
                    "member1": PydanticObjectId(user2_id),
                    "member2": PydanticObjectId(user1_id),
                },
            ],
        }
    )
    return PrivateRoomInDB(**room) if room else None


async def check_user_in_private_room(room_id: str, user_id: str) -> bool:
    room: PrivateRoomInDB | None = await fetch_private_room_by_id(room_id)
    user_id_obj = PydanticObjectId(user_id)
    return user_id_obj in [room.member1, room.member2] if room else False


async def get_user_private_rooms(user_id: str) -> list[PrivateRoomInDB]:
    rooms_collection = get_private_rooms_collection()

    # Create a query to find private rooms for the specified user
    query = {
        "$or": [
            {"member1": PydanticObjectId(user_id)},
            {"member2": PydanticObjectId(user_id)},
        ]
    }

    # Fetch the documents using the query
    cursor = rooms_collection.find(query)

    # Convert the cursor to a list and await the result
    rooms = await cursor.to_list(length=None)

    # Convert each document to PrivateRoomInDB
    return [PrivateRoomInDB(**room) for room in rooms]


async def create_private_room(user1_id: str, user2_id: str) -> PrivateRoomInDB:
    if user1_id == user2_id:
        raise ValueError("Users cannot be the same")

    rooms_collection = get_private_rooms_collection()

    room = await fetch_private_room_by_members(user1_id, user2_id)

    if room is not None:
        return room
    else:
        user1_id_obj = PydanticObjectId(user1_id)
        user2_id_obj = PydanticObjectId(user2_id)
        new_room = PrivateRoom(
            member1=user1_id_obj,
            member2=user2_id_obj,
            created_at=datetime.now(),
        )
        new_room_obj = await rooms_collection.insert_one(
            new_room.model_dump(by_alias=True)
        )
        return PrivateRoomInDB(
            **new_room.model_dump(by_alias=True), _id=new_room_obj.inserted_id
        )
