from .db import get_db_session
from .models import UserModel, SessionModel, User_Session, Member_Model, RoomModel, MessageModel, KeyModel
from .schemas import User, Message, Room,  CreateUser, CreateSession, CreateRoom

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List


DB: Session = Depends(get_db_session)


def add_user(user: CreateUser, db: DB):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_user(user_id: int, db: DB):
    if user := db.query(UserModel).filter(UserModel.uid == user_id).first():
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {user_id} does not exists in DB or CACHE")


def get_room(room_id: int, db: DB):
    if room := db.query(RoomModel).filter(RoomModel.rid == room_id).first():
        return room
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Room with id: {room_id} does not exists in DB or CACHE")


def get_session(session_id: int, db: DB):
    if room := db.query(SessionModel).filter(SessionModel.session_id == session_id).first():
        return room
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Session with id: {session_id} does not exists in DB or CACHE")


def add_session(session: CreateSession, room_id: int, db: DB):
    room = db.query(RoomModel).filter(
        RoomModel.rid == session.room_id).first()

    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No such Room With room id : {CreateSession.room_id} exists")

    if (set(session.users) - {UserModel.uid for _ in RoomModel.members}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Foreign Users Found in Selected Users check users",
        )

    new_session = SessionModel(
        room_id=session.room_id,
        session_name=session.session_name,
        users=[db.query(UserModel).filter(UserModel.uid == user_id).first()
               for user_id in session.users]
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


def add_user_to_room(users: List[User.uid], room_id: int, db: DB):

    room = db.query(RoomModel).filter(RoomModel.rid == room_id).first()
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Room with id: {id} does not exist")
    for user_id in users:
        user = db.query(UserModel).filter(UserModel.uid == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with id {user_id} not found")

        if user not in room.members:
            room.members.append(user)

    db.commit()
    db.refresh(room)

    return room


def make_room(room: CreateRoom, db: DB):
    if (
        existing_room := db.query(RoomModel)
        .filter_by(RoomModel.room_name == room.room_name)
        .first()
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Room with name : {room.room_name} already exists in server")

    members = db.query(UserModel).filter(UserModel.uid.in_(room.members)).all()
    if len(members) != room.room_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Specified Number of users: {room.room_size} users got from database: {len(members)}")

    new_room = RoomModel(room_name=room.room_name, members=room.members)

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room


def get_message(message_id: int, db: DB):
    if message := db.query(Member_Model).filter(MessageModel.mid == message_id).first():
        return message
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Message with id: {message_id} does not exists in DB or CACHE")


def new_message(message: Message, db: DB):
    session_conn = get_session(message.session)
    if not session_conn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid Session ID : {message.session}")

    new_message = MessageModel(
        sender_id=message.sender_id, mssg_encrypt=message.text, session=session_conn)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return new_message
