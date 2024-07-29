from pydantic import BaseModel

from chatApp.utils.object_id import PydanticObjectId


class CreatePrivateRoom(BaseModel):
    member1: PydanticObjectId | None = None
    member2: PydanticObjectId | None = None
