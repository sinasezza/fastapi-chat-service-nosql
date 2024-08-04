from datetime import datetime
from typing import Any

from fastapi import status
from pydantic import BaseModel, Field

from chatApp.config.database import get_public_rooms_collection
from chatApp.schemas.public_room import GetPublicRoomSchema
from chatApp.utils.object_id import PydanticObjectId


class PublicRoom(BaseModel):
    owner: PydanticObjectId
    name: str
    description: str | None = Field(
        default=None, description="Description of the room"
    )
    max_members: int | None = Field(
        default=None, description="Maximum number of members allowed"
    )
    welcome_message: str | None = Field(
        default=None, description="Welcome message for the room"
    )
    rules: str | None = Field(default=None, description="Rules for the room")
    allow_file_sharing: bool = Field(
        default=True, description="Allow file sharing in the room"
    )
    members: list[PydanticObjectId] = Field(
        default_factory=list, description="List of user IDs"
    )
    ban_list: list[PydanticObjectId] = Field(
        default_factory=list, description="List of IDs to be banned"
    )
    moderators: list[PydanticObjectId] = Field(
        default_factory=list, description="List of moderator IDs"
    )
    allow_users_access_message_history: bool = Field(
        True, description="Allow user to access message history"
    )
    max_latest_messages_access: int | None = Field(
        default=None, description="Maximum number of latest messages to access"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class PublicRoomInDB(PublicRoom):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")


async def fetch_all_public_rooms() -> list[GetPublicRoomSchema]:
    """Fetch all public rooms and return them as a list of GetPublicRoomSchema."""
    rooms_collection = get_public_rooms_collection()
    rooms = await rooms_collection.find().to_list(length=None)
    return [
        GetPublicRoomSchema(**room, members_count=len(room["members"]))
        for room in rooms
    ]


async def fetch_public_room_by_id(id: str) -> PublicRoomInDB | None:
    room_collection = get_public_rooms_collection()
    room = await room_collection.find_one({"_id": PydanticObjectId(id)})
    return PublicRoomInDB(**room) if room else None


async def join_public_room(
    room_id: str, user_id: str
) -> tuple[bool, str | None, int]:
    rooms_collection = get_public_rooms_collection()
    room: PublicRoomInDB | None = await fetch_public_room_by_id(room_id)

    # Ensure room is not None
    if room is None:
        return False, "room not found", status.HTTP_404_NOT_FOUND

    ban_list: list[PydanticObjectId] = room.ban_list
    members: list[PydanticObjectId] = room.members
    userObjId = PydanticObjectId(user_id)

    if userObjId not in ban_list:
        if userObjId not in members:
            members.append(userObjId)

            # Update the room in the database
            result = await rooms_collection.update_one(
                {"_id": PydanticObjectId(room_id)},
                {"$set": {"members": members}},  # Update only members
            )

            if result.modified_count == 1:
                return True, None, status.HTTP_204_NO_CONTENT
            else:
                return (
                    False,
                    "something went wrong, please try again",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )  # Failed to update the room in the database
        return (
            True,
            None,
            status.HTTP_204_NO_CONTENT,
        )  # User is already a member
    return (
        False,
        "you are banned from this room",
        status.HTTP_403_FORBIDDEN,
    )  # User is banned


async def check_user_in_public_room(room_id: str, user_id: str) -> bool:
    room: PublicRoomInDB | None = await fetch_public_room_by_id(room_id)
    user_id_obj = PydanticObjectId(user_id)
    if room is None:
        return False
    if user_id_obj not in room.ban_list or user_id_obj not in room.members:
        return False
    return True


async def create_public_room(
    owner: str, room_info: dict[str, Any]
) -> PublicRoomInDB | None:
    rooms_collection = get_public_rooms_collection()

    user_id_obj = PydanticObjectId(owner)
    room = PublicRoom(
        **room_info,
        owner=user_id_obj,
        created_at=datetime.now(),
        members=[user_id_obj],
    )

    room_obj = await rooms_collection.insert_one(
        room.model_dump(by_alias=True)
    )
    return PublicRoomInDB(
        **room.model_dump(by_alias=True), _id=room_obj.inserted_id
    )
