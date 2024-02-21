from uuid import uuid4
from datetime import datetime
from pytz import timezone
from sqlalchemy import (
    mapped_column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    BigInteger,
    DateTime,
)

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.services.db import Base
from typing import List, Optional, Set


class TimeModel(Base):
    __abstract__ = True

    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=func.now())
    update_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserModel(TimeModel):
    __tablename__ = "users"

    uid: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True)
    nick_name: Mapped[str]
    name: Mapped[str] = mapped_column(nullable=False)
    public_key: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    number: Mapped[str] = mapped_column(unique=True, nullable=False)
    status: Mapped[str]

    # One to One relationShip with the private Key
    # public_key = relationship("KeyModel", uselist=False, back_populates="user")

    rooms: Mapped[Set["RoomModel"]] = relationship(secondary="membership", back_populates="members"
                                                   )

    sessions: Mapped[Set["SessionModel"]] = relationship(secondary="session_data", back_populates="users"
                                                         )


class SessionModel(TimeModel):
    __tablename__ = "sessions"

    session_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    session_name: Mapped[int] = mapped_column(nullable=False)

    rooms: Mapped[Set["RoomModel"]] = relationship(back_populates="sessions")
    users: Mapped[Set["UserModel"]] = relationship(secondary="session_data", back_populates="sessions"
                                                   )
    # Establish a one - to - many relation with message sent in the room
    messages: Mapped[List["MessageModel"]] = relationship(
        back_populates="session"
    )


class User_Session(Base):
    __tablename__ = "session_data"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.session_id"), primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.uid"), primary_key=True)


class Member_Model(Base):
    __tablename__ = "membership"

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.rid"), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.uid"), primary_key=True)


class RoomModel(TimeModel):
    __tablename__ = "rooms"

    room_name: Mapped[str] = mapped_column(nullable=False)
    rid: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True)
    members: Mapped[Set["UserModel"]] = relationship(
        secondary="membership", back_populates="rooms")
    session: Mapped["SessionModel"] = relationship(
        back_populates="rooms")


class MessageModel(TimeModel):
    __tablename__ = "messages"

    mid: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True)

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.uid"), nullable=False)
    mssg_encrypt: Mapped[str]
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.rid"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"))
    room: Mapped["RoomModel"] = relationship(back_populates="messages")
