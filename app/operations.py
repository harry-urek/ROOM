from .services.db import get_db_session
from .models import UserModel, SessionModel, User_Session, Member_Model, RoomModel, MessageModel, KeyModel, AddUser  # noqa: F401
from .models.schemas import User, Message, Room,  CreateUser, CreateSession, CreateRoom

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List


DB: Session = Depends(get_db_session)

#  Direct OP


def add_user(user: CreateUser, db: DB):
    """
    The function `add_user` adds a new user to the database.

    :param user: The parameter `user` is of type `CreateUser`, which is likely a data class or a class
    that holds the information needed to create a new user in the database. It may have attributes such
    as `name`, `email`, and `number`, which are used to populate the corresponding fields in
    :type user: CreateUser
    :param db: The "db" parameter is an instance of the DB class, which is used to interact with the
    database. It is likely an object that provides methods for adding, committing, and refreshing data
    in the database
    :type db: DB
    :return: the `db_user` object, which is an instance of the `UserModel` class.
    """
    db_user = UserModel(
        name=user.name,
        email=user.email,
        number=user.number,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

# Celery OPeration when a user demands another user
# Non Celery OP if user itself requests


def get_user(user_id: int, db: DB):
    """
    The function `get_user` retrieves a user from a database based on their user ID and returns the user
    if found, otherwise it raises an HTTPException with a 404 status code.

    :param user_id: The user_id parameter is an integer that represents the unique identifier of a user
    :type user_id: int
    :param db: The "db" parameter is an instance of the DB class, which is used to query the database.
    It is assumed to have a method called "query" that can be used to execute queries on the database
    :type db: DB
    :return: The function `get_user` returns the user object if it exists in the database. If the user
    does not exist, it raises an HTTPException with a 404 status code and a detail message indicating
    that the user with the given id does not exist in the database or cache.
    """
    if user := db.query(UserModel).filter(UserModel.uid == user_id).first():
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {user_id} does not exists in DB or CACHE",
        )

# Celery OP


def get_room(room_id: int, db: DB):
    """
    The function `get_room` retrieves a room from a database based on its ID and raises an exception if
    the room does not exist.

    :param room_id: The room_id parameter is an integer that represents the unique identifier of a room.
    It is used to query the database and retrieve the corresponding room object
    :type room_id: int
    :param db: The `db` parameter is an instance of a database connection or session. It is used to
    query the database for the room with the given `room_id`
    :type db: DB
    :return: The function `get_room` returns the room object with the specified `room_id` if it exists
    in the database (`db`). If the room does not exist, it raises an HTTPException with a 404 status
    code and a detail message indicating that the room does not exist in the database or cache.
    """
    if room := db.query(RoomModel).filter(RoomModel.rid == room_id).first():
        return room
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id: {room_id} does not exists in DB or CACHE",
        )

# celery OP


def get_session(session_id: int, db: DB):
    """
    The function `get_session` retrieves a session from the database based on the provided session ID,
    and raises an exception if the session does not exist.

    :param session_id: The session_id parameter is an integer that represents the unique identifier of a
    session
    :type session_id: int
    :param db: The `db` parameter is an instance of the `DB` class, which is likely a database
    connection or session object used to interact with the database. It is used to query the database
    for a session with the given `session_id`
    :type db: DB
    :return: the session with the specified session_id if it exists in the database. If the session does
    not exist, it raises an HTTPException with a 404 status code and a detail message indicating that
    the session does not exist in the database or cache.
    """
    if (
        room := db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .first()
    ):
        return room
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id: {session_id} does not exists in DB or CACHE",
        )

#  Direct OP


def add_session(session: CreateSession, db: DB):
    """
    The function `add_session` adds a new session to a database, checking if the room and users exist
    before creating the session.

    :param session: The `session` parameter is of type `CreateSession`, which is a custom class or data
    structure that contains the information needed to create a new session. It likely has the following
    attributes:
    :type session: CreateSession
    :param db: The parameter `db` is an instance of the `DB` class, which is used to interact with the
    database. It is assumed to have methods like `query`, `add`, `commit`, and `refresh` for querying,
    adding, committing, and refreshing data in the database, respectively
    :type db: DB
    :return: a new session object of type SessionModel.
    """
    room = db.query(RoomModel).filter(RoomModel.rid == session.room_id).first()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No such Room With room id : {session.room_id} exists",
        )

    check_user = (
        db.query(Member_Model)
        .filter(
            Member_Model.room_id == session.room_id,
            Member_Model.user_id.in_(session.users),
        )
        .count()
    )

    if check_user != len(session.users):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Foreign Users Found in Selected Users check users",
        )

    new_session = SessionModel(
        room_id=session.room_id,
        session_name=session.session_name,
        users=[
            db.query(UserModel).filter(UserModel.uid == user_id).first()
            for user_id in session.users
        ],
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session

# Celery Task


def add_uses_to_room(users: AddUser, db: DB):
    """
    The function adds users to a room in a database.

    :param users: The parameter `users` is of type `AddUser`, which is a custom class or data structure
    that contains a list of user IDs (`user_list`) that need to be added to a room
    :type users: AddUser
    :param db: The "db" parameter is an instance of a database connection or session. It is used to
    query and manipulate data in the database
    :type db: DB
    :return: the updated room object after adding the specified users to the room's members list.
    """

    room = db.query(RoomModel).filter(RoomModel.rid == users.room_id).first()
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id: {id} does not exist",
        )
    for user_id in users.user_list:
        user = db.query(UserModel).filter(UserModel.uid == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with id {user_id} not found"
            )

        if user not in room.members:
            room.members.append(user)

    db.commit()
    db.refresh(room)

    return room

#  Direct OP


def make_room(room: CreateRoom, db: DB):
    """
    The function `make_room` creates a new room in a database if a room with the same name does not
    already exist, and adds the specified members to the room.

    :param room: The `room` parameter is an instance of the `CreateRoom` class, which contains
    information about the room to be created. It likely has attributes such as `room_name` (the name of
    the room) and `user_ids` (a list of user IDs associated with the room)
    :type room: CreateRoom
    :param db: The `db` parameter is an instance of a database connection or session. It is used to
    interact with the database and perform operations such as querying, adding, and committing data
    :type db: DB
    :return: a new room object of type `RoomModel`.
    """
    if (
        existing_room := db.query(RoomModel)
        .filter(RoomModel.room_name == room.room_name)
        .first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room with name : {room.room_name} already exists in server",
        )

    member_list = db.query(UserModel).filter(
        UserModel.uid.in_(room.user_ids)).all()
    # if len(member_list) != room.room_size:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Specified Number of users: {room.room_size} users got from database: {len(member_list)}",
    #     )

    new_room = RoomModel(room_name=room.room_name, members=member_list)

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room
