# Ensure models are imported so Alembic/metadata can discover them
from .user import User  # noqa: F401
from .room import Room, RoomMember  # noqa: F401
