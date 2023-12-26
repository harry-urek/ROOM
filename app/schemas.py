from pydantic import BaseModel
from typing import List


class User(BaseModel):
    uid: int
    nick_name: str
    name: str
    number: str
    status: str
    email: str

    class Config:
        orm_mode: True


class AddUser(BaseModel):
    room_id: int
    user_list: List[int]


class Session(BaseModel):
    session_id: int
    room_id: int
    session_name: str
    users: List[User]


# Message


class Message(BaseModel):
    mid: int
    sender_id: int
    session: int
    text: str

    class Config:
        orm_mode: True


# Session


class Session(Session):
    messages: List[Message]

    class Config:
        orm_mode: True


# Room


class Room(BaseModel):
    rid: int
    room_name: str
    members: List[User]
    sessions: List[Session]

    class Config:
        orm_mode: True


# CreateUser


class CreateUser(BaseModel):
    name: str
    email: str
    number: str


# CreateSession


class CreateSession(BaseModel):
    session_name: str
    users: List[int]
    room_id: int


# CreateRoom


class CreateRoom(BaseModel):
    room_name: str
    user_ids: List[int]
    room_size: int
