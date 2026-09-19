import logging

from flask import request
from flask_socketio import SocketIO, emit

from app.security.permissions import authenticate_socket
from app.services.message_service import MessageService
from app.dto.message_dto import SendMessageRequest
from app.exceptions.exceptions import AuthenticationError, ValidationError, AttachmentError
from pydantic import ValidationError as PydanticError

logger = logging.getLogger(__name__)

socketio = SocketIO()
message_service = MessageService()

# Track authenticated users: sid -> user
connected_users = {}


@socketio.on("connect")
def handle_connect():
    token = request.args.get("token")
    if not token:
        logger.warning("Socket connection rejected: no token")
        return False

    try:
        user = authenticate_socket(token)
        connected_users[request.sid] = user
        logger.info("User connected: %s (sid=%s)", user.username, request.sid)
    except AuthenticationError as e:
        logger.warning("Socket authentication failed: %s", e.message)
        return False


@socketio.on("disconnect")
def handle_disconnect():
    user = connected_users.pop(request.sid, None)
    if user:
        logger.info("User disconnected: %s (sid=%s)", user.username, request.sid)


@socketio.on("send_message")
def handle_send_message(data):
    user = connected_users.get(request.sid)
    if not user:
        emit("error", {"code": "AUTHENTICATION_ERROR", "message": "Not authenticated"})
        return

    try:
        dto = SendMessageRequest(**data)
    except (PydanticError, ValueError) as e:
        emit("error", {"code": "VALIDATION_ERROR", "message": str(e)})
        return

    try:
        result = message_service.send_message(
            sender_id=user.id,
            content=dto.content,
            attachment_id=dto.attachment_id,
        )
        emit("receive_message", result, broadcast=True)
    except (ValidationError, AttachmentError) as e:
        emit("error", {"code": e.code, "message": e.message})
