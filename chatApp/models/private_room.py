from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.config.database import get_private_rooms_collection
from chatApp.utils.object_id import PydanticObjectId


class PrivateRoom(BaseModel):
    member1: PydanticObjectId
    member2: PydanticObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class PrivateRoomInDB(PrivateRoom):
    id: PydanticObjectId = Field(alias="_id")


async def fetch_private_room_by_id(id: str):
    room_collection = get_private_rooms_collection()
    return await room_collection.find_one({"_id": PydanticObjectId(id)})


async def check_members_in_room(user1_id: str, user2_id: str):
    rooms_collection = get_private_rooms_collection()
    room = await rooms_collection.find_one(
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
    return str(room["_id"]) if room is not None else None


async def join_private_room(user1_id: str, user2_id: str) -> str:
    rooms_collection = get_private_rooms_collection()

    room_id = await check_members_in_room(user1_id, user2_id)

    if room_id is not None:
        return room_id
    else:
        room = await rooms_collection.insert_one(
            {
                "member1": PydanticObjectId(user1_id),
                "member2": PydanticObjectId(user2_id),
            }
        )
        return str(room.inserted_id)
