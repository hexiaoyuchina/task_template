import logging
import celery
from tasks.base import BaseTask

logger = logging.getLogger(__file__)


# 定义子任务的消息队列为： task
@celery.task(bind=True, base=BaseTask, Q="task")
def instance_create_task(self, *args, **kwargs):
    logger.info("start instance create")
    pass


@celery.task(bind=True, base=BaseTask, Q="task")
def db_instance_create_task(self, *args, **kwargs):
    logger.info("db instance")
    pass


@celery.task(bind=True, base=BaseTask, Q="task")
def test_task(self, *args, **kwargs):
    logger.info("test_task")
    pass
