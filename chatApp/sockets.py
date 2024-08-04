from typing import Any

import socketio

from chatApp.config.config import get_settings
from chatApp.config.database import get_messages_collection
from chatApp.config.logs import get_logger
from chatApp.models import message, private_room, public_room
from chatApp.models.user import fetch_user_by_id
from chatApp.utils.object_id import PydanticObjectId

settings = get_settings()

# Define the Socket.IO server
sio_server = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],
    logger=get_logger("socket.io"),
)

# Create the ASGI app using the defined server
sio_app = socketio.ASGIApp(
    socketio_server=sio_server,
    socketio_path="/socket.io/",
)


# Global state management
class GlobalState:
    all_clients: int = 0
    rooms_client_count: dict[str, int] = {}


global_state = GlobalState()


@sio_server.event
async def connect(sid: str, environ: dict, auth: dict) -> None:
    """Handle a new client connection."""
    global_state.all_clients += 1
    print(f"Client connected: {sid}")
    print(f"Number of clients connected: {global_state.all_clients}")
    await sio_server.emit("client_count", data=global_state.all_clients)


@sio_server.event
async def disconnect(sid: str) -> None:
    """Handle client disconnection."""
    global_state.all_clients -= 1
    print(f"Client disconnected: {sid}")
    print(f"Number of clients connected: {global_state.all_clients}")
    await sio_server.emit("client_count", data=global_state.all_clients)


@sio_server.event
async def joining_public_room(sid: str, data: dict[str, Any]) -> None:
    """Handle user joining a public room."""
    room_id = data.get("room_id")
    user_id = data.get("user_id")

    if not isinstance(room_id, str) or not isinstance(user_id, str):
        await sio_server.emit(
            "error", data="Invalid room_id or user_id", room=sid
        )
        return

    room_joined, report, _ = await public_room.join_public_room(
        room_id, user_id
    )

    if room_joined:
        await sio_server.enter_room(sid, room_id)
        global_state.rooms_client_count[room_id] = (
            global_state.rooms_client_count.get(room_id, 0) + 1
        )
        room_members = global_state.rooms_client_count[room_id]
        print(f"User {user_id} joined room {room_id}")
        print(f"Number of users in the room {room_id}: {room_members}")
        await sio_server.emit("room_count", data=room_members, room=room_id)
        await sio_server.emit("user_joined", data=user_id, room=room_id)
    else:
        await sio_server.emit("error", data="Error joining room", room=sid)


@sio_server.event
async def joining_private_room(sid: str, data: dict[str, Any]) -> None:
    """Handle user joining a private room."""
    # user1 = data.get("user1")
    # user2 = data.get("user2")

    ...

    # if not isinstance(user1, str) or not isinstance(user2, str):
    #     await sio_server.emit("error", data="Invalid user1 or user2", room=sid)
    #     return

    # room_id = await private_room.join_private_room(user1, user2)
    # await sio_server.enter_room(sid, room_id)
    # print(f"User {user1} joined private room {room_id} with {user2}")
    # await sio_server.emit("user_joined", data=user1, room=room_id)


@sio_server.event
async def leave_room(sid: str, data: dict[str, Any]) -> None:
    """Handle user leaving a room."""
    room_id = data.get("room_id")
    user_id = data.get("user_id")

    if not isinstance(room_id, str) or not isinstance(user_id, str):
        await sio_server.emit(
            "error", data="Invalid room_id or user_id", room=sid
        )
        return

    await sio_server.leave_room(sid, room_id)
    global_state.rooms_client_count[room_id] = max(
        global_state.rooms_client_count.get(room_id, 0) - 1, 0
    )
    room_members = global_state.rooms_client_count[room_id]
    print(f"User {user_id} left room {room_id}")
    print(f"Number of users in the room {room_id}: {room_members}")
    await sio_server.emit("room_count", data=room_members, room=room_id)
    await sio_server.emit("user_left", data=user_id, room=room_id)


@sio_server.event
async def send_public_message(sid: str, data: dict[str, Any]) -> None:
    """Handle sending a message to a public group."""
    room_id = data.get("room_id")
    message_sent = data.get("message")
    user_id = data.get("user_id")

    if (
        not isinstance(room_id, str)
        or not isinstance(message_sent, str)
        or not isinstance(user_id, str)
    ):
        await sio_server.emit(
            "error", data="Invalid room_id, message, or user_id", room=sid
        )
        return

    print(
        f"Sending message to room {room_id}: {message_sent} from user {user_id}"
    )

    room = await public_room.fetch_public_room_by_id(room_id)

    if not room:
        await sio_server.emit(
            "error", data={"error": "Room not found"}, room=sid
        )
        return

    messages_collection = get_messages_collection()
    user = await fetch_user_by_id(user_id)

    if user and user["_id"] in room.members:
        new_message = message.Message(
            user_id=PydanticObjectId(user_id),
            room_id=PydanticObjectId(room_id),
            content=message_sent,
            room_type="public",
        )
        await messages_collection.insert_one(new_message.model_dump())
        await sio_server.emit(
            "message",
            {"sid": sid, "message": message, "user_id": user_id},
            room=room_id,
        )
        print(f"Message sent to room {room_id}: {message}")
    else:
        print("User is not a member of the room or user not found")


@sio_server.event
async def send_private_message(sid: str, data: dict[str, Any]) -> None:
    """Handle sending a private message."""
    room_id = data.get("room_id")
    user1_id = data.get("user1")
    user2_id = data.get("user2")
    message_sent = data.get("message")

    if (
        not isinstance(room_id, str)
        or not isinstance(user1_id, str)
        or not isinstance(user2_id, str)
        or not isinstance(message_sent, str)
    ):
        await sio_server.emit(
            "error",
            data={"error": "Invalid room_id, user1, user2, or message"},
            room=sid,
        )
        return

    user1 = await fetch_user_by_id(user1_id)
    user2 = await fetch_user_by_id(user2_id)
    if not user1 or not user2:
        await sio_server.emit(
            "error", data={"error": "Users not found"}, room=sid
        )
        return

    room: (
        private_room.PrivateRoomInDB | None
    ) = await private_room.fetch_private_room_by_members(user1_id, user2_id)
    if not room:
        await sio_server.emit(
            "error", data={"error": "Room not found"}, room=sid
        )
        return

    messages_collection = get_messages_collection()

    new_message = message.Message(
        user_id=PydanticObjectId(user1_id),
        room_id=PydanticObjectId(room_id),
        content=message_sent,
        room_type="private",
    )
    await messages_collection.insert_one(new_message.model_dump())
    await sio_server.emit(
        "message",
        {"sid": sid, "message": message, "user_id": user1_id},
        room=room_id,
    )
    print(f"Private message sent from {user1_id} to room {room_id}: {message}")
