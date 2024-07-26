
from email import message
import json
import uvicorn
import logging
import argparse

from .services.ws import WebSockM
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException
from typing import List
from fastapi import FastAPI, WebSocket, Depends, status
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

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <label>Session ID: <input type="text" id="SessionId" autocomplete="off" value="foo"/></label>
            <label>User ID: <input type="text" id="UserId" autocomplete="off" value="foo"/></label>
            
            <button onclick="connect(event)">Connect</button>
            <hr>
            <label>Message ID: <input type="text" id="messageId" autocomplete="off"/></label>
            <label>Message: <input type="text" id="messageText" autocomplete="off"/></label>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
        var ws = null;
            function connect(event) {
                var session_id = document.getElementById("SessionId").value;
                var user_id = document.getElementById("UserId").value;
                
                ws = new WebSocket("ws://localhost:8000/ws/" + session_id +"/" + user_id );
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    var content = document.createTextNode(event.data);
                    message.appendChild(content);
                    messages.appendChild(message);
                };
                event.preventDefault()
            }
            function sendMessage(event) {
                var messageId = document.getElementById("messageId").value;
                var session_id = document.getElementById("SessionId").value;
                var user_id = document.getElementById("UserId").value;
                var messageText = document.getElementById("messageText").value;
                var message = {
                    mid: messageId,
                    sender_id: user_id,
                    session: session_id,
                    text: messageText
                };
                ws.send(JSON.stringify(message));
                document.getElementbyId("messageText").value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""

# async def send_message(session_id: int, user_id: int, message: Message, db: AsyncSession):
#     await store_message(message=message, user_id=user_id, sid=session_id)
#     # Save encrypted message to the database
#     # Enqueue task for processing
#     process_message.apply_async(args=[message], countdown=1)
#     return {"message": "Message sent for processing"}


@app.get("/")
def root():
    return HTMLResponse(html)


@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_endpoint(webS: WebSocket, session_id: str | None, user_id: str | None,  db: AsyncSession = Depends(get_db)):
    if session_id is None or user_id is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    sess_id = int(session_id)
    await socket_manager.add_user_to_session(sess_id, webS)
    try:
        while True:
            data = await webS.receive_text()
            message_packet = json.loads(data)
            message = Message(**message_packet)
            await store_message(sid=sess_id, user_id=int(user_id), message=message.text, db=db)
            await socket_manager.broadcast(sess_id, message.text)

    except WebSocketDisconnect:
        await socket_manager.remove_user_from_session(sess_id, webS)
        print(f"User {sess_id} got disconnected")
