from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websock: WebSocket):
        await websock.accept()
        self.connections.append(websock)

    async def broadcast_message(self, data: str):
        for connection in self.connections:
            await connection.send_text(data)

    async def disconnect(self, sock: WebSocket):
        pass
