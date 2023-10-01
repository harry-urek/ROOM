from pydantic import BaseModel
from typing import List

# User
class User(BaseModel):
    uid: int
    nick_name:str
    name:str
    number:str
    status:str
    email:str

# Message
class Message(BaseModel):
    mid:int
    sender_id :int
    session: Session
# Session
class Session(BaseModel):
    session_id: int
    room_id:int
    session_name:str
    users:List[User.uid]
    messages:List[Message.mid]

# Room
class Room(BaseModel):
    rid:int
    room_name:str
    members:List[User.name]
    sessions:List[Session.session_name]

# CreateUser
class CreateUser(BaseModel):
    name:str
    email:str
    number:str
    
# CreateSession
class CreateSession(BaseModel):
    session_name:str
    users:List[User.uid]
    room_id:int
# CreateRoom
class CreateRoom(BaseModel):
    room_name:str
    members:List[User.uid]
    room_size:int
# UpdateUser
# UpdateSession
# UpdateRoom