from datetime import datetime

from pydantic import BaseModel, Field

from chatApp.utils.object_id import PydanticObjectId


class User(BaseModel):
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    last_login: datetime | None = None


class UserInDB(User):
    id: PydanticObjectId = Field(alias="_id", serialization_alias="id")
