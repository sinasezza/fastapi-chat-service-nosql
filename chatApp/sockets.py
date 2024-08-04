from typing import Any

import socketio

from chatApp.config.config import get_settings
from chatApp.config.logs import get_logger
from chatApp.models import message as message_model
from chatApp.models import private_room, public_room
from chatApp.models import user as user_model

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
        print(f"User {user_id} joined public room {room_id}")
        print(f"Number of users in the room {room_id}: {room_members}")
        await sio_server.emit("room_count", data=room_members, room=room_id)
        await sio_server.emit("user_joined", data=user_id, room=room_id)
    else:
        await sio_server.emit("error", data="report", to=sid)


@sio_server.event
async def joining_private_room(sid: str, data: dict[str, Any]) -> None:
    """Handle user joining a private room."""
    room_id: str = data["room_id"]
    user_id: str = data["user_id"]

    room: (
        private_room.PrivateRoomInDB | None
    ) = await private_room.fetch_private_room_by_id(room_id)
    if room is None:
        await sio_server.emit("error", data="Room not found", room=sid)
        return

    user: user_model.UserInDB | None = await user_model.fetch_user_by_id(
        user_id
    )
    if user is None:
        await sio_server.emit("error", data="User not found", room=sid)
        return

    access: bool = await private_room.check_user_in_private_room(
        room_id, user_id
    )
    if access:
        await sio_server.enter_room(sid, room_id)
        await sio_server.emit("user_joined", data=user_id, room=room_id)
    else:
        await sio_server.emit("error", data="Access denied", room=sid)
        return


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
    room_id: str = data["room_id"]
    message_sent: str = data["message"]
    user_id: str = data["user_id"]

    print(
        f"Sending message to room {room_id}: {message_sent} from user {user_id}"
    )

    room = await public_room.fetch_public_room_by_id(room_id)

    if not room:
        await sio_server.emit(
            "error", data={"error": "Room not found"}, room=sid
        )
        return

    user: user_model.UserInDB | None = await user_model.fetch_user_by_id(
        user_id
    )
    if user is None:
        await sio_server.emit(
            "error", data={"error": "User not found"}, room=sid
        )
        return

    if public_room.check_user_in_public_room(room_id, user_id):
        new_message = await message_model.create_message(
            room_id, user_id, "public", message_sent
        )

        await sio_server.emit(
            event="message",
            data={
                "sid": sid,
                "message": new_message.content,
                "user_id": user_id,
            },
            room=room_id,
        )

        print(f"Message sent to room {room_id}: {new_message.content}")
    else:
        print("User is not a member of the room or user not found")


@sio_server.event
async def send_private_message(sid: str, data: dict[str, Any]) -> None:
    """Handle sending a private message."""
    room_id: str = data["room_id"]
    user_id: str = data["user_id"]
    message_sent: str = data["message"]

    room: (
        private_room.PrivateRoomInDB | None
    ) = await private_room.fetch_private_room_by_id(room_id)
    if room is None:
        await sio_server.emit(
            "error", data={"error": "Room not found"}, room=sid
        )
        return
    user: user_model.UserInDB | None = await user_model.fetch_user_by_id(
        user_id
    )
    if user is None:
        await sio_server.emit(
            "error", data={"error": "Users not found"}, room=sid
        )
        return

    new_message: message_model.MessageInDB = (
        await message_model.create_message(
            room_id, user_id, "private", message_sent
        )
    )
    await sio_server.emit(
        "message",
        {
            "sid": sid,
            "message": message_sent,
            "message_id": str(new_message.id),
            "user_id": user_id,
        },
        room=room_id,
    )
    print(
        f"Private message sent from {user_id} to room {room_id}: {message_sent}"
    )
