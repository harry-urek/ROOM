
from app.services.db import Base
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    BigInteger,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP


class TimeModel(Base):
    __abstract__ = True

    created_time = Column(DateTime, default=datetime.now(), nullable=False)
    update_time = Column(DateTime, onupdate=datetime.now())


# The `UserModel` class defines a database table for storing user information with relationships to
# other models.
class UserModel(TimeModel):
    __tablename__ = "users"

    uid = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nick_name = Column(String)
    name = Column(String, nullable=False)
    public_key = Column(String)
    email = Column(String, unique=True, nullable=False)
    number = Column(String, unique=True, nullable=False)
    status = Column(String)

    # One to One relationShip with the private Key
    # public_key = relationship("KeyModel", uselist=False, back_populates="user")

    rooms = relationship("RoomModel", secondary="membership",
                         back_populates="members")

    sessions = relationship(
        "SessionModel", secondary="session_data", back_populates="users"
    )


# The `SessionModel` class defines a database table for sessions with relationships to rooms, users,
# and messages.
class SessionModel(TimeModel):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True,
                        autoincrement=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.rid"))
    session_name = Column(String, nullable=False)

    room = relationship("RoomModel", back_populates="sessions")
    users = relationship(
        "UserModel", secondary="session_data", back_populates="sessions"
    )
    # Establish a one - to - many relation with message sent in the room
    messages = relationship(
        "MessageModel",
        back_populates="session",
    )


# The class `User_Session` defines a table `session_data` with columns `session_id` and `user_id` as
# primary keys, referencing other tables `sessions` and `users` respectively.
class User_Session(Base):
    __tablename__ = "session_data"

    session_id = Column(Integer, ForeignKey(
        "sessions.session_id"), primary_key=True)

    user_id = Column(Integer, ForeignKey("users.uid"), primary_key=True)


# The `Member_Model` class represents a membership table with room_id and user_id as primary keys.
class Member_Model(Base):
    __tablename__ = "membership"

    room_id = Column(Integer, ForeignKey("rooms.rid"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.uid"), primary_key=True)


# The `RoomModel` class defines a SQLAlchemy model for rooms with attributes such as room_name, rid,
# members, and sessions.
class RoomModel(TimeModel):
    __tablename__ = "rooms"

    room_name = Column(String, nullable=False)
    rid = Column(Integer, primary_key=True, autoincrement=True, index=True)
    members = relationship(
        "UserModel", secondary="membership", back_populates="rooms")
    sessions = relationship("SessionModel", back_populates="room")


# The `MessageModel` class represents a message entity with attributes for message ID, sender ID,
# encrypted message content, session ID, and a relationship with the `SessionModel` class.
class MessageModel(TimeModel):
    __tablename__ = "messages"

    mid = Column(Integer, primary_key=True, index=True, autoincrement=True)

    sender_id = Column(Integer, ForeignKey("users.uid"))
    mssg_encrypt = Column(String)

    session_id = Column(Integer, ForeignKey("sessions.session_id"))
    session = relationship("SessionModel", back_populates="messages")
