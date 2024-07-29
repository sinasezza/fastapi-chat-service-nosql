from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.utils.object_id import PydanticObjectId


class Message(BaseModel):
    user_id: PydanticObjectId
    room_id: str | None = Field(default=None)
    content: str = Field(default=None)
    media: str = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class MessageInDB(Message):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")
