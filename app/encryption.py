import redis  # TODO can we change it to async redis
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from app.db import get_db_session
from app.models import MessageModel


DB: Session = Depends(get_db_session)
# Assuming you have a Redis client instance
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

# Your Fernet key for encryption
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)


def encrypt_message(message: str) -> str:
    return cipher_suite.encrypt(message.encode())


def decrypt_message(encrypted_message: str) -> str:
    return cipher_suite.decrypt(encrypted_message).decode()


async def store_message(user_id: int, message: str, db: DB, sid: int):
    # Encrypt the message
    encrypted_message = encrypt_message(message)

    # Store the encrypted message in the database
    db_message = MessageModel(
        sender_id=user_id, mssg_encrypt=encrypted_message, session_id=sid)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Store the encrypted message in Redis cache
    cache_key = f"message:{db_message.id}"
    redis_client.set(cache_key, encrypted_message)

    # Set an expiration time for the cache key # 1hr
    expiration_time = datetime.now() + timedelta(hours=1)
    redis_client.expireat(cache_key, expiration_time)


def get_message_from_cache(message_id: int) -> str:
    cache_key = f"message:{message_id}"
    if cached_message := redis_client.get(cache_key):
        return decrypt_message(cached_message.decode())
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found in cache",
        )
