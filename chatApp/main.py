import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from chatApp.config.config import get_settings
from chatApp.config.database import mongo_db
from chatApp.middlewares.request_limit import RequestLimitMiddleware
from chatApp.routes import auth, chat, user
from chatApp.sockets import sio_app

# Fetch settings
settings = get_settings()


# Define startup and shutdown event handlers
async def startup_event():
    await mongo_db.connect_to_mongodb()


async def shutdown_event():
    await mongo_db.close_mongodb_connection()


# Create a FastAPI app instance
app = FastAPI(
    title="FastAPI Chat App",
    description="A chat application built with FastAPI and socket.io",
    version="1.0.0",
    on_startup=[startup_event],
    on_shutdown=[shutdown_event],
)

### Add middlewares ###

# Configure CORS using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
app.add_middleware(RequestLimitMiddleware, max_requests=10, window_seconds=1)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)

# Include your routers for API endpoints
app.include_router(auth.router, prefix="/auth")
app.include_router(chat.router, prefix="/chat")
app.include_router(user.router, prefix="/user")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the FastAPI Chat App"}


# Mount socket.io app
app.mount("/", app=sio_app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
