from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from chatApp.config import auth
from chatApp.models import user as user_model
from chatApp.schemas.user import UserCreateSchema
from chatApp.utils.exceptions import credentials_exception

router = APIRouter()


@router.post("/register", response_model=user_model.UserInDB)
async def register_user(user_info: UserCreateSchema) -> user_model.UserInDB:
    existing_user = await user_model.fetch_user_by_username(user_info.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    existing_user = await user_model.fetch_user_by_email(user_info.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user_dict = user_info.model_dump()
    user = await user_model.create_user(user_dict)

    return user


@router.post("/token", response_model=dict)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    user = await auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise credentials_exception

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    data_to_encode = {
        "username": user.username,
        "email": user.email,
        "id": str(user.id),
    }

    access_token = auth.create_token(
        data=data_to_encode,
        token_type="access",
        expires_delta=access_token_expires,
    )

    refresh_token = auth.create_token(
        data=data_to_encode,
        token_type="refresh",
        expires_delta=refresh_token_expires,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/token/refresh", response_model=dict)
async def refresh_token(token: str) -> dict[str, str]:
    try:
        payload: dict[str, Any] = auth.parse_token(token)
        if not auth.validate_token(token):
            raise credentials_exception

        user_id: str = payload["id"]
        user: user_model.UserInDB | None = await user_model.fetch_user_by_id(
            user_id
        )
        if user is None:
            raise credentials_exception

        access_token_expires = timedelta(
            minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        refresh_token_expires = timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
        data_to_encode = {
            "username": user.username,
            "email": user.email,
            "id": str(user.id),
        }

        new_access_token = auth.create_token(
            data=data_to_encode,
            token_type="access",
            expires_delta=access_token_expires,
        )

        new_refresh_token = auth.create_token(
            data=data_to_encode,
            token_type="refresh",
            expires_delta=refresh_token_expires,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise credentials_exception


@router.get("/users/me/", response_model=user_model.UserInDB)
async def read_users_me(
    current_user: user_model.UserInDB = Depends(auth.get_current_user),
) -> user_model.UserInDB:
    return current_user
