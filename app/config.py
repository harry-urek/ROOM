import os

# Modify it match our system configs


class Config:
    DB_CONFIG = os.getenv(
        "DB_CONFIG",
        "postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}".format(
            DB_USER=os.getenv("DB_USER", "fastapi"),
            DB_PASSWORD=os.getenv("DB_PASSWORD", "fastapi-password"),
            DB_HOST=os.getenv("DB_HOST", "fastapi-postgresql:5432"),
            DB_NAME=os.getenv("DB_NAME", "fastapi"),

        ))

    RD_HOST = os.getenv("RD_HOST", "localhost"),
    RD_PORT = os.getenv("RD_PORT", "6900")
    VERSION = "0.1.5"
    TITLE = "ROOM COM BACKEND"
    DESCRIPTION = "A fastAPI based super fast backend service"


config = Config()
