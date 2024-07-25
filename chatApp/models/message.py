from bson import ObjectId
from pydantic import BaseModel


class Message(BaseModel):
    _id: ObjectId
    user_id: ObjectId
    room_id: str
    content: str
    # created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
