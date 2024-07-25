from bson import ObjectId
from pydantic import BaseModel


class User(BaseModel):
    _id: ObjectId
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    # created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # last_login: datetime = None
    # last_logout: datetime = None
