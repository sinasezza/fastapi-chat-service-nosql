from pydantic import BaseModel


def user_serializer(user) -> dict:
    return {
        "id": str(user["_id"]),
        "userName": user["username"],
        "email": user["email"],
    }


def users_serializer(users) -> list:
    return [user_serializer(user) for user in users]


class UserCreateSchema(BaseModel):
    username: str
    email: str
    password: str
