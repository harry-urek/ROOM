from email import message
from celery import Celery
from .operations import add_session, add_user, add_user_to_room, get_room, get_session, get_user


celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks"],
)


@celery.task
def process_message(message: message):
    pass
