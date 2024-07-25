def message_serializer(message) -> dict:
    return {
        "id": str(message["_id"]),
        "userId": str(message["user_id"]),
        "roomId": message["room_id"],
        "content": message["content"],
    }


def messages_serializer(messages) -> list:
    return [message_serializer(message) for message in messages]
