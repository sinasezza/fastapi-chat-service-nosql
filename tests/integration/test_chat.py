# tests/integration/test_chat.py

import asyncio

import pytest
import socketio

# Create a new Socket.IO client
sio = socketio.AsyncClient()


@pytest.mark.asyncio
async def test_connection():
    # Define a flag to determine if the connection is successful
    connected = asyncio.Event()

    # Define event handlers
    @sio.event
    async def connect():
        print("Connected to the server with SID:", sio.sid)
        assert sio.sid is not None
        connected.set()  # Set the flag when connected

    @sio.event
    async def disconnect():
        print("Disconnected from server")

    @sio.event
    async def connect_error(data):
        print("Connection failed:", data)

    try:
        # Connect to the server
        await sio.connect(
            "ws://127.0.0.1:8000/", wait_timeout=10
        )  # Ensure correct path

        # Wait for the connect event to be triggered
        await asyncio.wait_for(connected.wait(), timeout=10)

        # Perform additional tests if needed
        assert sio.sid is not None  # Example assertion
    except Exception as e:
        pytest.fail(f"Failed to connect: {e}")
    finally:
        # Disconnect from the server
        await sio.disconnect()
