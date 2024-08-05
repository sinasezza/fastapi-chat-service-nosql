from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from chatApp.config.config import get_settings
from chatApp.config.logs import logger
from chatApp.models import user as user_model
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
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


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


def create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT token with a specified expiration.

    :param data: The data to encode into the token.
    :param token_type: The type of token to create
    :param expires_delta: Optional expiration time delta for the token.
    :return: The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        match token_type:
            case "access":
                expire = datetime.now() + timedelta(
                    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
                )
            case "refresh":
                expire = datetime.now() + timedelta(
                    days=REFRESH_TOKEN_EXPIRE_DAYS
                )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def parse_token(token: str) -> dict[str, Any]:
    """
    Parse and validate the given JWT token, returning its payload.

    :param token: The JWT token to parse.
    :return: The payload data from the token.
    :raises credentials_exception: If the token is invalid or cannot be decoded.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False},
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT error: {e}")  # Log the error for debugging purposes
        raise credentials_exception


def validate_token(token: str) -> bool:
    """
    Validate the given JWT token by checking its expiration.

    :param token: The JWT token to validate.
    :return: True if the token is valid and not expired, otherwise False.
    """
    try:
        # Decode the token without validating the signature to check expiration
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False},
        )
        # Check if the token is expired
        if (
            payload.get("exp")
            and datetime.fromtimestamp(payload["exp"]) < datetime.now()
        ):
            return False
        return True
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        return False


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> user_model.UserInDB:
    """
    Retrieve the current user from the database using the provided JWT token.

    :param token: The JWT token used for authentication.
    :return: The User object representing the authenticated user.
    :raises credentials_exception: If the user cannot be found or the token is invalid.
    """
    # Parse the token to get the payload
    payload = parse_token(token)
    username: str | None = payload.get("username")

    if username is None:
        logger.error("Username is missing in the token payload.")
        raise credentials_exception

    user: user_model.UserInDB | None = await user_model.fetch_user_by_username(
        username
    )

    # Raise an exception if no user was found
    if user is None:
        logger.error(f"User with username {username} not found in database.")
        raise credentials_exception

    return user


async def authenticate_user(
    username: str, password: str
) -> user_model.UserInDB | None:
    user: user_model.UserInDB | None = await user_model.fetch_user_by_username(
        username
    )

    # Return None if no user was found or if password verification fails
    if user is None or not verify_password(password, user.hashed_password):
        return None

    return user
