from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.config.database import get_public_rooms_collection
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


async def fetch_public_room_by_id(id: str):
    room_collection = get_public_rooms_collection()
    return await room_collection.find_one({"_id": PydanticObjectId(id)})


async def join_public_room(room_id: str, user_id: str) -> bool:
    rooms_collection = get_public_rooms_collection()
    room = await rooms_collection.find_one({"_id": PydanticObjectId(room_id)})

    # Ensure room is not None
    if room is None:
        return False

    # Define the expected structure of the room dictionary
    # Adjust this according to the actual structure
    ban_list: list[PydanticObjectId] = room.get("ban_list", [])
    members: list[PydanticObjectId] = room.get("members", [])

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
                return True
            else:
                return False  # Failed to update the room in the database
        return True  # User is already a member
    return False  # User is banned
