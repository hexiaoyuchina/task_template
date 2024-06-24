import logging
import celery
from tasks.base import BaseTask


@celery.task(bind=True, base=BaseTask, Q="task")
def instance_create_task(self, *args, **kwargs):
    pass
