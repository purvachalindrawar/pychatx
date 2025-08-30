from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)

class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=120)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str

    class Config:
        from_attributes = True  # Pydantic v2: read from ORM
