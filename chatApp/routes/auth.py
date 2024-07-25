# auth.py
from collections.abc import Mapping
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from chatApp.config import auth
from chatApp.models.user import User
from chatApp.schemas.user import UserCreateSchema
from chatApp.utils.exceptions import credentials_exception

router = APIRouter()


@router.post("/register", response_model=User)
async def register_user(user: UserCreateSchema) -> User:
    # Fetch the users_collection within the request scope
    users_collection = auth.get_users_collection()

    # Check if the user already exists
    existing_user: Optional[Mapping[str, Any]] = await users_collection.find_one(
        {"username": user.username}
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash the password before saving
    hashed_password = auth.get_password_hash(user.password)
    user_dict = user.model_dump(exclude={"password"})
    user_dict["hashed_password"] = hashed_password

    # Insert user into the database
    await users_collection.insert_one(user_dict)

    # Construct and return a User instance from the inserted document
    return User(**user_dict)


@router.post("/token", response_model=dict)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    # Attempt to authenticate the user using provided credentials
    user = await auth.authenticate_user(form_data.username, form_data.password)

    # Raise an exception if authentication fails
    if not user:
        raise credentials_exception

    # Create an access token with a specific expiration time
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Return the generated token and its type
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(auth.get_current_user)) -> User:
    return current_user
