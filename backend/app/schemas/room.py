from pydantic import BaseModel, Field

class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    is_private: bool = False

class RoomOut(BaseModel):
    id: int
    name: str
    is_private: bool

    class Config:
        from_attributes = True

class MemberOut(BaseModel):
    user_id: int
    role: str

    class Config:
        from_attributes = True
