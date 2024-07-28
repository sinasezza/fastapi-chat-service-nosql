from pydantic import BaseModel


class MessageCreateSchema(BaseModel):
    content: str
