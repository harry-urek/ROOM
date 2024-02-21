from uuid import uuid4
from datetime import datetime
from sqlalchemy import (
    mapped_column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    BigInteger,
    DateTime,
)

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped, mapped_mapped_column

from app.services.db import Base


class TimeModel(Base):
    __abstract__ = True

    created_t: Mapped[DateTime] = mapped_mapped_column(
        default=datetime.now(), nullable=False)
    update_t: Mapped[DateTime] = mapped_mapped_column(onupdate=datetime.now())


class UserModel(TimeModel):
    __tablename__ = "users"

    uid: Mapped[int] = mapped_column(primary_key=True,
                                     autoincrement=True, index=True)
    nick_name: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, nullable=False)
    public_key: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String)

    # One to One relationShip with the private Key
    # public_key = relationship("KeyModel", uselist=False, back_populates="user")

    rooms = relationship("RoomModel", secondary="membership",
                         back_populates="members")

    sessions = relationship(
        "SessionModel", secondary="session_data", back_populates="users"
    )


class SessionModel(TimeModel):
    __tablename__ = "sessions"

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                            autoincrement=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.rid"))
    session_name: Mapped[int] = mapped_column(String, nullable=False)

    room = relationship("RoomModel", back_populates="sessions")
    users = relationship(
        "UserModel", secondary="session_data", back_populates="sessions"
    )
    # Establish a one - to - many relation with message sent in the room
    messages = relationship(
        "MessageModel",
        back_populates="session",
    )


class User_Session(Base):
    __tablename__ = "session_data"

    session_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "sessions.session_id"), primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.uid"), primary_key=True)


class Member_Model(Base):
    __tablename__ = "membership"

    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.rid"), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.uid"), primary_key=True)


class RoomModel(TimeModel):
    __tablename__ = "rooms"

    room_name: Mapped[int] = mapped_column(String, nullable=False)
    rid: Mapped[int] = mapped_column(Integer, primary_key=True,
                                     autoincrement=True, index=True)
    members = relationship(
        "UserModel", secondary="membership", back_populates="rooms")
    sessions = relationship("SessionModel", back_populates="room")


class MessageModel(TimeModel):
    __tablename__ = "messages"

    mid: Mapped[int] = mapped_column(Integer, primary_key=True,
                                     index=True, autoincrement=True)

    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.uid"))
    mssg_encrypt: Mapped[int] = mapped_column(String)

    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.session_id"))
    session = relationship("SessionModel", back_populates="messages")
