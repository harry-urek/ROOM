
import redis
from .ws import ConnectionManager
from .tasks import celery
from datetime import datetime
from celery import Celery
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from fastapi import FastAPI, WebSocket, Depends
from .db import get_db_session
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
from .schemas import Session, User, Message, Room, CreateUser, CreateSession, CreateRoom

app = FastAPI()

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.post("/send_message")
async def send_message(message: Message, db: Session = Depends(get_db_session)):
    # Save encrypted message to the database
    # Enqueue task for processing
    process_message.apply_async(args=[message], countdown=1)
    return {"message": "Message sent for processing"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, session_id: int, db: Session = Depends(get_db_session)
):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            # Process the message and send it to other users in the session
            await manager.broadcast_message(message)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
