import asyncio
from fastapi import WebSocket

from .cm import RD_MANAGER as redisPubSub


class WebSockM:
    def __init__(self):
        self.sessions: dict = {}
        self.pubsub_client = redisPubSub

    async def add_user_to_session(self, session_id: int, ws: WebSocket) -> None:
        await ws.accept()

        if session_id in self.sessions:
            self.sessions[session_id].append(ws)
        else:
            self.sessions[session_id] = [ws]

            await self.pubsub_client.connect()
            subscriber = await self.pubsub_client.subscribe(session_id)
            asyncio.create_task(self._pubsub_reader(subscriber)
                                )

    async def broadcast(self, session_id: int, message: str):
        await self.pubsub_client._publish(session_id, message)

    async def remove_user_from_session(self, session_id: str, websocket: WebSocket) -> None:

        self.rooms[session_id].remove(websocket)

        if len(self.rooms[session_id]) == 0:
            del self.rooms[session_id]
            await self.pubsub_client.unsubscribe(session_id)

    async def _pubsub_reader(self, subscriber):
        while True:
            message = await subscriber.get_message(ignore_subscribe_messages=True)
            if message is not None:
                session_id = message['channel'].decode('utf-8')
                all_sockets = self.rooms[session_id]
                for socket in all_sockets:
                    data = message['data'].decode('utf-8')
                    await socket.send_text(data)
