from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path

from chatApp.config import auth
from chatApp.models import message, private_room, public_room, user
from chatApp.schemas.public_room import CreatePublicRoom, GetPublicRoomSchema
from chatApp.utils.object_id import is_valid_object_id

router = APIRouter()


@router.post("/create-public-room", response_model=public_room.PublicRoomInDB)
async def create_public_room(
    room_info: CreatePublicRoom,
    user: user.UserInDB = Depends(auth.get_current_user),
):
    return await public_room.create_public_room(
        owner=str(user.id), room_info=room_info.model_dump(by_alias=True)
    )


@router.get(
    "/join-public-room/{room_id}", response_model=public_room.PublicRoomInDB
)
async def join_public_room(
    room_id: str = Path(..., description="ID of the public room to join"),
    user: user.UserInDB = Depends(auth.get_current_user),
):
    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room ID format")

    # Check if the room exists
    room = await public_room.fetch_public_room_by_id(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    result, report, code = await public_room.join_public_room(
        room_id, str(user.id)
    )
    if result:
        return room
    else:
        raise HTTPException(detail=report, status_code=code)


@router.get("/get-public-rooms", response_model=Mapping[str, Any])
async def get_public_rooms(
    page: int = 1,
    per_page: int = 10,
):
    all_rooms: list[
        GetPublicRoomSchema
    ] = await public_room.fetch_all_public_rooms()
    total_count = len(all_rooms)

    # Calculate pagination indexes
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    if start_index >= total_count:
        raise HTTPException(status_code=404, detail="Page out of range")

    paginated_rooms = all_rooms[start_index:end_index]

    data_to_return = {
        "data": paginated_rooms,
        "meta": {
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
        },
    }
    return data_to_return


@router.post(
    "/create-private-room/{person_id}",
    response_model=private_room.PrivateRoomInDB,
)
async def create_private_room(
    person_id: str = Path(..., description="other person's id"),
    user: user.UserInDB = Depends(auth.get_current_user),
):
    if not is_valid_object_id(person_id):
        raise HTTPException(status_code=400, detail="Invalid person ID format")

    # Create the PrivateRoom instance
    return await private_room.create_private_room(str(user.id), person_id)


@router.get(
    "/get-private-rooms", response_model=list[private_room.PrivateRoomInDB]
)
async def get_private_rooms(
    user: user.UserInDB = Depends(auth.get_current_user),
):
    return await private_room.get_user_private_rooms(str(user.id))


@router.get(
    "/get-private-room/{room_id}", response_model=private_room.PrivateRoomInDB
)
async def get_private_room(
    room_id: str = Path(..., description="ID of the private room to retrieve"),
    user: user.UserInDB = Depends(auth.get_current_user),
):
    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room ID format")

    room = await private_room.fetch_private_room_by_id(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Private room not found")

    if not await private_room.check_user_in_private_room(
        str(room.id), str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="You are not a member of this room"
        )

    return room


@router.get(
    "/get-messages/public/{room_id}", response_model=list[message.MessageInDB]
)
async def get_messages_of_public_room(
    room_id: str = Path(..., description="id of the public room"),
    user: user.UserInDB = Depends(auth.get_current_user),
):
    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room id")

    room = await public_room.fetch_public_room_by_id(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Public room not found")

    if not await public_room.check_user_in_public_room(room_id, str(user.id)):
        raise HTTPException(
            status_code=403, detail="User not a member of the room"
        )

    return await message.get_public_messages(room_id)


@router.get(
    "/get-messages/private/{room_id}", response_model=list[message.MessageInDB]
)
async def get_messages_of_private_room(
    room_id: str = Path(..., description="id of the private room"),
    user: user.UserInDB = Depends(auth.get_current_user),
):
    if not is_valid_object_id(room_id):
        raise HTTPException(status_code=400, detail="Invalid room id")

    room = await private_room.fetch_private_room_by_id(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Private room not found")

    if not await public_room.check_user_in_public_room(
        str(room.id), str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="User not a member of the room"
        )

    return await message.get_private_messages(room_id)
