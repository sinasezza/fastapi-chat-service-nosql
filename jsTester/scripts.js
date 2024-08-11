const ROOM_ID = "66a7731a11fe8199049c8dbd"; // put your room ID here
const USER1_ID = "66a765df185ba34c8e4a4b1a"; // put your user ID here
const PRV_ROOM_ID = "66a785f6473ff39a7496f918"; // put your private room id to send message

// Establish the Socket.IO connection
const sio = io("http://127.0.0.1:8000/", {
  path: "/socket.io",
  transports: ['websocket', 'polling']
});

// Handle connection event
sio.on("connect", () => {
  console.log("Connected to the server with SID:", sio.id);

  // Emit the 'join_room' event for a public room
  // sio.emit('joining_public_room', { room_id: ROOM_ID, user_id: USER1_ID });

  // Send a public message
  // sio.emit('send_public_message', { room_id: ROOM_ID, message: "Hello, world JS!", user_id: USER1_ID });

  // emit the join_room event for a private room
  // sio.emit('joining_private_room', {room_id: PRV_ROOM_ID, user_id: USER1_ID});

  // Send a private message
  // sio.emit('send_private_message', {room_id: PRV_ROOM_ID, user_id: USER1_ID, message: "hello private!"});
});

// Handle disconnection event
sio.on("disconnect", () => {
  console.log("Disconnected from the server");
});

// Handle connection errors
sio.on("connect_error", (err) => {
  console.log("Connection error:", err.message);
});

// Listen for the 'client_count' event
sio.on("client_count", (count) => {
  console.log(`Number of connected clients: ${count}`);
});

// Listen for the 'room_count' event
sio.on("room_count", (count) => {
  console.log(`Number of connected clients in the room: ${count}`);
});

// Listen for the 'user_joined' event
sio.on("user_joined", (user) => {
  console.log(`${user} joined the chat room`);
});

// Listen for the 'user_left' event
sio.on("user_left", (user) => {
  console.log(`${user} left the chat room`);
});

// Listen for the 'message' event
sio.on("message", ({ sid, message, message_id, user_id }) => {
  console.log(`Message: ${message_id} with content ${message} from ${user_id}`);
});

// Listen for the 'private_message' event
sio.on("private_message", ({ sid, message, recipient_id, sender_id }) => {
  console.log(`Private message: ${message} from ${sender_id} to ${recipient_id}`);
});

// Handle general errors
sio.on("error", (err) => {
  console.error("An error occurred:", err);
});
