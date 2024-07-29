from datetime import datetime

from pydantic import BaseModel, Field

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
