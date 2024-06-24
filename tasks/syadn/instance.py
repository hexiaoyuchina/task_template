import logging
import celery
from tasks.base import BaseTask

# 定义子任务的消息队列为： task
@celery.task(bind=True, base=BaseTask, Q="task")
def instance_create_task(self, *args, **kwargs):
    pass
