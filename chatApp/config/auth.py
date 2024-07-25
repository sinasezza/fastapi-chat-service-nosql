# auth.py
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.context import CryptContext

from chatApp.config.config import get_settings
from chatApp.config.database import mongo_db
from chatApp.config.logs import logger
from chatApp.models.user import User
from chatApp.utils.exceptions import credentials_exception

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# JWT settings
SECRET_KEY = settings.jwt_secret_key.get_secret_value()
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the stored hashed password.

    :param plain_password: The plain text password.
    :param hashed_password: The hashed password stored in the database.
    :return: True if passwords match, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash the given password using the password hashing context.

    :param password: The plain text password to hash.
    :return: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with a specified expiration.

    :param data: The data to encode into the token.
    :param expires_delta: Optional expiration time delta for the token.
    :return: The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def parse_access_token(token: str) -> dict[str, Any]:
    """
    Parse and validate the given JWT token, returning its payload.

    :param token: The JWT token to parse.
    :return: The payload data from the token.
    :raises credentials_exception: If the token is invalid or cannot be decoded.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT error: {e}")  # Log the error for debugging purposes
        raise credentials_exception


def get_users_collection() -> AsyncIOMotorCollection:
    """
    Retrieve the users collection from the MongoDB database.

    :return: The users collection instance.
    :raises RuntimeError: If the users collection is not initialized.
    """
    users_collection = mongo_db.users_collection
    if users_collection is None:
        raise RuntimeError("Users collection is not initialized.")
    return users_collection


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Retrieve the current user from the database using the provided JWT token.

    :param token: The JWT token used for authentication.
    :return: The User object representing the authenticated user.
    :raises credentials_exception: If the user cannot be found or the token is invalid.
    """
    # Parse the token to get the payload
    payload = parse_access_token(token)
    username: Optional[str] = payload.get("sub")

    if username is None:
        logger.error("Username is missing in the token payload.")
        raise credentials_exception

    # Fetch the users_collection within the request scope
    users_collection = get_users_collection()

    # Properly type the result of the find_one query
    user: Optional[Mapping[str, Any]] = await users_collection.find_one(
        {"username": username}
    )

    # Raise an exception if no user was found
    if user is None:
        logger.error(f"User with username {username} not found in database.")
        raise credentials_exception

    # Construct and return a User instance from the found document
    return User(**user)


async def authenticate_user(username: str, password: str) -> Optional[User]:
    # Fetch the users_collection within the request scope
    users_collection = get_users_collection()

    # Properly type the result of the find_one query
    user: Optional[Mapping[str, Any]] = await users_collection.find_one(
        {"username": username}
    )

    # Return None if no user was found or if password verification fails
    if user is None or not verify_password(password, user["hashed_password"]):
        return None

    # Construct and return a User instance from the found document
    return User(**user)
