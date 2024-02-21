from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect

# An instance  ConnectionManager() gets initiated for every webSock endpoints
# Each user connected to that webSock endpoint will be managed by the connection manager for that
# endpoint with each user having a websock connection stored in @connections{uid : connection} & @connected [connections]


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int:WebSocket] = {}

    async def connect(self, user_id: int, session_id: int, websock: WebSocket):
        await websock.accept()
        self.connections[user_id] = websock

    async def broadcast_message(self, data: str):
        for _, connects in self.connections:
            await connects.send_text(data)

    def total_connections(self, websock: WebSocket):
        return len(self.connections)

    async def disconnect(self, uid: int, websock: WebSocket):
        await websock.close()
        del self.connections[uid]
