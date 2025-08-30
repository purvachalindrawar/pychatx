# Ensure SQLAlchemy models are imported when the package loads
# so Base.metadata.create_all() sees them.

from .user import User  # noqa: F401
