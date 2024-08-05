from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.utils.object_id import PydanticObjectId


class UserCreateSchema(BaseModel):
    username: str
    email: str
    password: str


class UserListSchema(BaseModel):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")
    username: str
    created_at: datetime = datetime.now()
