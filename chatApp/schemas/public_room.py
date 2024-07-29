from pydantic import BaseModel, Field


class CreatePublicRoom(BaseModel):
    name: str = Field(..., description="Name of the public room")
    description: str = Field(..., description="Description of the public room")
    max_members: int = Field(
        10, description="Maximum number of members allowed"
    )
    welcome_message: str | None = Field(
        None, description="Welcome message for the room"
    )
    rules: str | None = Field(None, description="Rules for the room")
    allow_file_sharing: bool = Field(
        True, description="Allow file sharing in the room"
    )
    allow_users_access_message_history: bool = Field(
        True, description="Allow users to access message history"
    )
    max_latest_messages_access: int | None = Field(
        None, description="Maximum number of latest messages to access"
    )