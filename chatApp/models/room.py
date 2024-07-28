from datetime import datetime, timezone

from pydantic import BaseModel, Field

from chatApp.utils.object_id import PydanticObjectId


class Room(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    members: list[PydanticObjectId]


class RoomInDB(Room):
    id: PydanticObjectId = Field(alias="_id")
