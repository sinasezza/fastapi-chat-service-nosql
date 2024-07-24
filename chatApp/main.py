import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatApp.config.config import get_settings
from chatApp.config.database import close_mongodb_connection, connect_to_mongodb
from chatApp.routes import auth, chat, user

# Fetch settings
settings = get_settings()

app = FastAPI()

# Configure CORS using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Create a Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Wrap with ASGI application
socket_app = socketio.ASGIApp(sio, app)


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Chat App"}


# Define lifespan event handlers
async def lifespan(app: FastAPI):
    # On startup
    await connect_to_mongodb()

    yield

    # On shutdown
    await close_mongodb_connection()


app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(user.router)


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


if __name__ == "__main__":
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=True)
