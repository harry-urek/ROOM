from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.util.compact import contextmanager

DATABASE_URL = "postgresql://user:password@database:5432/alpha"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def add_to_db(value, db: Session = Depends(get_db_session)):
    await db.add(value)
    await db.commit()
    await db.refresh()
