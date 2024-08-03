from collections.abc import Mapping
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from chatApp.config import auth
from chatApp.config.database import (
    get_messages_collection,
    get_private_rooms_collection,
    get_public_rooms_collection,
)
from chatApp.models.message import MessageInDB
from chatApp.models.private_room import PrivateRoom, PrivateRoomInDB
from chatApp.models.public_room import PublicRoom, PublicRoomInDB
from chatApp.models.user import UserInDB
from chatApp.schemas.private_room import CreatePrivateRoom
from chatApp.schemas.public_room import CreatePublicRoom, GetPulbicRoomsSchema
from chatApp.utils.object_id import PydanticObjectId, is_valid_object_id

router = APIRouter()


@router.post("/create-public-room", response_model=PublicRoomInDB)
async def create_public_room(
    room_info: CreatePublicRoom,
    user: UserInDB = Depends(auth.get_current_user),
):
    rooms_collection: AsyncIOMotorCollection = get_public_rooms_collection()

    # Convert room_info to dictionary and add the owner
    room_dict: dict[str, Any] = room_info.model_dump()
    room_dict["owner"] = user.id
    room_dict["members"] = [user.id]

    room = PublicRoom(**room_dict)

    # Insert the room into the database
    result = await rooms_collection.insert_one(room.model_dump(by_alias=True))

    return PublicRoomInDB(
        **room.model_dump(by_alias=True), _id=result.inserted_id
    )


@router.get("/join-public-room/{room_id}")
async def join_public_room(
    room_id: str = Path(..., description="ID of the public room to join"),
    user: UserInDB = Depends(auth.get_current_user),
):
    rooms_collection: AsyncIOMotorCollection = get_public_rooms_collection()

    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room ID format")

    # Check if the room exists
    room = await rooms_collection.find_one({"_id": PydanticObjectId(room_id)})
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    if user.id not in room["ban_list"]:
        if user.id not in room["members"]:
            room["members"].append(user.id)

            # Update the room in the database
            await rooms_collection.update_one(
                {"_id": room["_id"]}, {"$set": room}
            )
    else:
        raise HTTPException(
            status_code=403, detail="You are banned from this room"
        )

    return PublicRoomInDB(**room)


@router.get("/get-public-rooms/", response_model=Mapping[str, Any])
async def get_public_rooms(
    page: int = 1,
    per_page: int = 10,
):
    rooms_collection: AsyncIOMotorCollection = get_public_rooms_collection()
    total_count = await rooms_collection.count_documents({})
    rooms = (
        await rooms_collection.find(
            {},
            {
                "_id": 1,
                "name": 1,
                "description": 1,
                "owner": 1,
                "created_at": 1,
            },
        )
        .skip((page - 1) * per_page)
        .limit(per_page)
        .to_list(None)
    )

    data_to_return = {
        "data": [GetPulbicRoomsSchema(**room) for room in rooms],
        "meta": {
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
        },
    }
    return data_to_return


@router.post(
    "/create-private-room/{person_id}", response_model=PrivateRoomInDB
)
async def create_private_room(
    person_id: str = Path(..., description="other person's id"),
    user: UserInDB = Depends(auth.get_current_user),
):
    rooms_collection: AsyncIOMotorCollection = get_private_rooms_collection()

    if not is_valid_object_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")

    # Create a PrivateRoomInDB instance with current time
    room_schema = CreatePrivateRoom(
        member1=user.id, member2=PydanticObjectId(person_id)
    )
    room_dict = room_schema.model_dump()
    room_dict["created_at"] = datetime.now()

    # Ensure member1 and member2 are not the same
    if room_dict["member1"] == room_dict["member2"]:
        raise HTTPException(
            status_code=400, detail="Members must be different"
        )

    recently_created = await rooms_collection.find_one(
        {
            "$or": [
                {
                    "member1": room_dict["member1"],
                    "member2": room_dict["member2"],
                },
                {
                    "member1": room_dict["member2"],
                    "member2": room_dict["member1"],
                },
            ]
        }
    )
    if recently_created is not None:
        raise HTTPException(
            status_code=400,
            detail="A private room already exists between you and this user",
        )

    # Create the PrivateRoom instance
    room = PrivateRoom(**room_dict)

    # Insert the room into the database
    result = await rooms_collection.insert_one(room.model_dump(by_alias=True))

    return PrivateRoomInDB(
        **room.model_dump(by_alias=True), _id=result.inserted_id
    )


@router.get("/private-room/{room_id}", response_model=PrivateRoomInDB)
async def get_private_room(
    room_id: str = Path(..., description="ID of the private room to retrieve"),
    user: UserInDB = Depends(auth.get_current_user),
):
    rooms_collection: AsyncIOMotorCollection = get_private_rooms_collection()

    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room ID format")

    # Fetch the room from the database
    room_data = await rooms_collection.find_one(
        {"_id": PydanticObjectId(room_id)}
    )

    if room_data is None:
        raise HTTPException(status_code=404, detail="Private room not found")

    if user.id not in [room_data.get("member1"), room_data.get("member2")]:
        raise HTTPException(
            status_code=403, detail="You are not a member of this room"
        )

    return PrivateRoomInDB(**room_data)


@router.get("/messages/public/{room_id}", response_model=list[MessageInDB])
async def get_messages_of_public_room(
    room_id: str = Path(..., description="id of the public room"),
    user: UserInDB = Depends(auth.get_current_user),
):
    messages_collection: AsyncIOMotorCollection = get_messages_collection()
    public_room_collection: AsyncIOMotorCollection = (
        get_public_rooms_collection()
    )

    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room id")

    room = await public_room_collection.find_one(
        {"_id": PydanticObjectId(room_id)}
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Public room not found")

    if user.id not in room["members"]:
        raise HTTPException(
            status_code=403, detail="User not a member of the room"
        )

    cursor: AsyncIOMotorCursor = messages_collection.find(
        {"room_id": PydanticObjectId(room_id)}
    )
    messages_dicts: list[Mapping[str, Any]] = await cursor.to_list(length=None)
    messages: list[MessageInDB] = [
        MessageInDB(**message_dict) for message_dict in messages_dicts
    ]

    return messages


@router.get("/messages/private/{room_id}", response_model=MessageInDB)
async def get_message_of_private_room(
    room_id: str = Path(..., description="id of the private room"),
    user: UserInDB = Depends(auth.get_current_user),
):
    messages_collection: AsyncIOMotorCollection = get_messages_collection()
    private_rooms_collection: AsyncIOMotorCollection = (
        get_private_rooms_collection()
    )

    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room id")

    room = await private_rooms_collection.find_one(
        {"_id": PydanticObjectId(room_id)}
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Private room not found")

    if user.id not in [room["member1"], room["member2"]]:
        raise HTTPException(
            status_code=403, detail="User not a member of the room"
        )

    # Get the last message from the room
    cursor: AsyncIOMotorCursor = messages_collection.find(
        {"room_id": PydanticObjectId(room_id)}
    )
    messages_dicts: list[Mapping[str, Any]] = await cursor.to_list(length=None)
    messages: list[MessageInDB] = [
        MessageInDB(**message_dict) for message_dict in messages_dicts
    ]

    return messages
