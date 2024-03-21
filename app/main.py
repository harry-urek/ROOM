
from email import message
import uvicorn
import logging
import argparse

from .services.ws import WebSockM
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from fastapi import FastAPI, WebSocket, Depends
from .services.db import get_db
from .services.encryption import store_message
# from .models import (
#     UserModel,
#     SessionModel,
#     User_Session,
#     Member_Model,
#     RoomModel,
#     MessageModel,
#     KeyModel,
#     AddUser,
# )
from .models.schemas import Session, User, Message, Room, CreateUser, CreateSession, CreateRoom


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ROOM SERVE")


app = FastAPI()
socket_manager = WebSockM()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# async def send_message(session_id: int, user_id: int, message: Message, db: AsyncSession):
#     await store_message(message=message, user_id=user_id, sid=session_id)
#     # Save encrypted message to the database
#     # Enqueue task for processing
#     process_message.apply_async(args=[message], countdown=1)
#     return {"message": "Message sent for processing"}
@app.get("/")
def root():
    return {"Connected to FastAPI ROOM SERVER"}


@app.websocket_route("/message/{session_id}")
async def session_box(webS: WebSocket, session_id: str, user_id: int,  db: AsyncSession = Depends(get_db)):
    await socket_manager.add_user_to_session(session_id, webS)
    try:
        while True:
            data = await webS.receive_text()
            message = Message(text=data)
            await store_message(session_id=session_id, user_id=user_id, message=message, db=db)
            await socket_manager.broadcast(session_id, message)

    except WebSocketDisconnect:
        await socket_manager.remove_user_from_session(session_id, webS)
