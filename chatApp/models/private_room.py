from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.utils.object_id import PydanticObjectId


class PrivateRoom(BaseModel):
    member1: PydanticObjectId
    member2: PydanticObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class PrivateRoomInDB(PrivateRoom):
    id: PydanticObjectId = Field(alias="_id")
