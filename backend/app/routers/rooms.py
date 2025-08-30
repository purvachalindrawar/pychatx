from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.room import Room, RoomMember
from ..models.user import User
from ..schemas.room import RoomCreate, RoomOut, MemberOut

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])

@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    exists = db.query(Room).filter(Room.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Room name already taken")

    room = Room(name=payload.name, is_private=payload.is_private)
    db.add(room)
    db.flush()  # get room.id before commit

    membership = RoomMember(room_id=room.id, user_id=me.id, role="owner")
    db.add(membership)

    db.commit()
    db.refresh(room)
    return room

@router.get("", response_model=List[RoomOut])
def list_my_rooms(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    # rooms where I'm a member
    room_ids = db.query(RoomMember.room_id).filter(RoomMember.user_id == me.id).subquery()
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).order_by(Room.id.asc()).all()
    return rooms

@router.post("/{room_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def join_room(room_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.is_private:
        raise HTTPException(status_code=403, detail="Private room (invites not implemented yet)")

    existing = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.user_id == me.id).first()
    if existing:
        return None

    db.add(RoomMember(room_id=room_id, user_id=me.id, role="member"))
    db.commit()
    return None

@router.post("/{room_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_room(room_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    membership = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.user_id == me.id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member")
    db.delete(membership)
    db.commit()
    return None

@router.get("/{room_id}/members", response_model=List[MemberOut])
def list_members(room_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    # must be a member to view
    am_member = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.user_id == me.id).first()
    if not am_member:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    members = db.query(RoomMember).filter(RoomMember.room_id == room_id).order_by(RoomMember.id.asc()).all()
    # return minimal info (user_id, role)
    return [MemberOut(user_id=m.user_id, role=m.role) for m in members]
