import socketio

from chatApp.config.config import get_settings

settings = get_settings()

# Define the Socket.IO server
sio_server = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_allow_origins,
)

# Create the ASGI app using the defined server
sio_app = socketio.ASGIApp(
    socketio_server=sio_server, socketio_path="/", other_asgi_app="main:app"
)


# Event handlers
@sio_server.event
async def connect(sid: str, environ: dict, auth: dict) -> None:
    print(f"Client connected: {sid}")


@sio_server.event
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")
