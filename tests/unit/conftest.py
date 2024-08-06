import pytest

from chatApp.config import database
from chatApp.config.database import mongo_db


@pytest.fixture(scope="session")
async def db():
    # Initialize the test database
    global mongo_db
    print(f"mongodb is {mongo_db}")
    mongo_db = await database.init_mongo_db(test_db=True)
    yield mongo_db
    # Clean up the test database
    await database.shutdown_mongo_db()


@pytest.fixture
async def users_collection(db):
    return db.users_collection


@pytest.fixture
async def messages_collection(db):
    return db.messages_collection


@pytest.fixture
async def public_rooms_collection(db):
    return db.public_rooms_collection


@pytest.fixture
async def private_rooms_collection(db):
    return db.private_rooms_collection


@pytest.fixture
async def test_user():
    return {
        "username": "test_user",
        "email": "test@test.com",
        "password": "test_password",
    }


@pytest.fixture
async def test_room():
    return {"name": "test_room"}


@pytest.fixture
async def test_message():
    return {"sender": "test_user", "text": "test_message"}


@pytest.fixture
async def test_private_room():
    return {"name": "test_private_room", "users": ["test_user"]}


@pytest.fixture
async def test_public_room():
    return {"name": "test_public_room"}
