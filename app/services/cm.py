# redis manager lives here

import aioredis


class redisPubSub:
    def __init__(self, redis_host, redis_port):
        self.host = redis_host
        self.port = redis_port
        self.pubsub = None

    async def _get_redis_connection(self) -> aioredis.Redis:
        return aioredis.Redis(host=self.host,
                              port=self.port,
                              auto_close_connection_pool=False)

    async def connect(self) -> None:
        self.redis_connection = await self._get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    async def _publish(self, session_id: int, message: str):
        await self.redis_connection.publish(session_id, message=message)

    async def subscribe(self, session_id: int) -> aioredis.Redis:
        await self.pubsub.subscribe(session_id)
        return self.pubsub

    async def unsubscribe(self, session_id: int):
        await self.pubsub.unsubscribe(session_id)
