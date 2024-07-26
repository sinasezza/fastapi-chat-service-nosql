import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatApp.config.config import get_settings
from chatApp.config.database import mongo_db
from chatApp.middlewares.request_limit import RequestLimitMiddleware
from chatApp.routes import auth, chat, user

# Fetch settings
settings = get_settings()


# Define startup and shutdown event handlers
async def startup_event():
    await mongo_db.connect_to_mongodb()  # Use mongo_db instance


async def shutdown_event():
    await mongo_db.close_mongodb_connection()  # Use mongo_db instance


# Create a FastAPI app instance
app = FastAPI(on_startup=[startup_event], on_shutdown=[shutdown_event])

### add middlewares ###
# Configure CORS using settings with explicit type annotations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# add custom middlewares
app.add_middleware(RequestLimitMiddleware, max_requests=10, window_seconds=1)

# Create a Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_allow_origins,
)

# Wrap with ASGI application
socket_app = socketio.ASGIApp(sio, app)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the FastAPI Chat App"}


# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(chat.router, prefix="/chat")
app.include_router(user.router, prefix="/user")


@sio.event
async def connect(sid: str, environ: dict) -> None:
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")


if __name__ == "__main__":
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=True)
