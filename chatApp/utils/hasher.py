from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from chatApp.config.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


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
